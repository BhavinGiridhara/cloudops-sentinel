import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, Mock

import pytest

from services.instrumentation import wsgi


def reporter(**kwargs):
    return wsgi.TelemetryReporter("checkout", "https://sentinel.example/incidents", **kwargs)


def test_counts_p95_and_window_reset():
    metrics = reporter()
    for duration in range(1, 101):
        metrics.record(duration, duration <= 17)
    assert metrics._snapshot() == {
        "service": "checkout", "request_count": 100,
        "error_count": 17, "latency_p95_ms": 95,
    }
    assert metrics._snapshot() is None


def test_reservoir_bounds_memory_without_losing_counts():
    metrics = reporter(max_samples=10)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: metrics.record(123, True), range(1000)))
    assert len(metrics._durations) == 10
    payload = metrics._snapshot()
    assert payload["request_count"] == payload["error_count"] == 1000
    assert payload["latency_p95_ms"] == 123


@pytest.mark.parametrize("status,expected", [("200 OK", 0), ("404 Not Found", 0), ("500 Error", 1)])
def test_middleware_preserves_response_and_measures(monkeypatch, status, expected):
    times = iter([10, 10.25])
    monkeypatch.setattr(wsgi.time, "perf_counter", lambda: next(times))
    metrics = reporter()
    start = Mock()

    def app(environ, start_response):
        start_response(status, [("Content-Type", "text/plain")])
        return [b"hello"]

    assert list(wsgi.TelemetryMiddleware(app, metrics)({}, start)) == [b"hello"]
    assert start.call_args.args[0] == status
    payload = metrics._snapshot()
    assert payload["request_count"] == 1
    assert payload["error_count"] == expected
    assert payload["latency_p95_ms"] == 250


@pytest.mark.parametrize("streaming", [False, True])
def test_unhandled_errors_are_recorded_and_propagated(streaming):
    metrics = reporter()
    closed = []

    def stream():
        try:
            yield b"partial"
            raise RuntimeError("broken stream")
        finally:
            closed.append(True)

    def app(environ, start_response):
        if not streaming:
            raise RuntimeError("broken app")
        start_response("200 OK", [])
        return stream()

    with pytest.raises(RuntimeError):
        list(wsgi.TelemetryMiddleware(app, metrics)({}, Mock()))
    assert metrics._snapshot()["error_count"] == 1
    if streaming:
        assert closed == [True]


def test_export_failure_is_logged_and_does_not_escape(monkeypatch, caplog):
    metrics = reporter()
    metrics.record(20, False)
    send = Mock(side_effect=TimeoutError("unreachable"))
    monkeypatch.setattr(wsgi, "urlopen", send)
    assert metrics.flush() is None
    assert "window dropped" in caplog.text
    assert metrics.flush() is None
    assert send.call_count == 1


def test_empty_window_never_sends(monkeypatch):
    send = Mock()
    monkeypatch.setattr(wsgi, "urlopen", send)
    assert reporter().flush() is None
    send.assert_not_called()


def test_shutdown_flushes_final_window(monkeypatch):
    send = MagicMock()
    response = send.return_value.__enter__.return_value
    response.status = 202
    response.read.return_value = b'{"event_id":"accepted"}'
    monkeypatch.setattr(wsgi, "urlopen", send)
    metrics = reporter(interval=60)
    metrics.start()
    metrics.record(30, False)
    metrics.stop()
    assert not metrics._thread.is_alive()
    assert json.loads(send.call_args.args[0].data)["request_count"] == 1


def test_non_202_is_not_logged_as_accepted(monkeypatch, caplog):
    send = MagicMock()
    send.return_value.__enter__.return_value.status = 200
    monkeypatch.setattr(wsgi, "urlopen", send)
    metrics = reporter()
    metrics.record(1, False)
    assert metrics.flush() is None
    assert "Expected HTTP 202" in caplog.text
