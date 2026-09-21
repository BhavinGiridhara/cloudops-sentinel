"""Measure WSGI requests and export aggregate telemetry without blocking on HTTP."""

import json
import logging
import math
import random
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class TelemetryReporter:
    """One reporter per application process; start after any worker fork."""

    def __init__(self, service, endpoint, interval=60, timeout=3, max_samples=10000):
        parsed = urlsplit(endpoint)
        local_http = parsed.scheme == "http" and parsed.hostname in {
            "127.0.0.1", "localhost", "::1"
        }
        if not parsed.hostname or not (parsed.scheme == "https" or local_http):
            raise ValueError("Use an HTTPS endpoint (HTTP is allowed on loopback for tests)")
        if not isinstance(service, str) or not service.strip():
            raise ValueError("service must be non-empty")
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be positive and finite")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        if not isinstance(max_samples, int) or max_samples < 1:
            raise ValueError("max_samples must be a positive integer")
        self.service = service.strip()
        self.endpoint = endpoint
        self.interval = interval
        self.timeout = timeout
        self.max_samples = max_samples
        self._lock = threading.Lock()
        self._flush_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._requests = 0
        self._errors = 0
        self._durations = []

    def record(self, duration_ms, failed):
        with self._lock:
            self._requests += 1
            self._errors += int(failed)
            # Reservoir sampling bounds memory while retaining all request/error counts.
            if len(self._durations) < self.max_samples:
                self._durations.append(duration_ms)
            else:
                index = random.randrange(self._requests)
                if index < self.max_samples:
                    self._durations[index] = duration_ms

    def _snapshot(self):
        with self._lock:
            if not self._requests:
                return None
            requests, errors, durations = self._requests, self._errors, self._durations
            self._requests, self._errors, self._durations = 0, 0, []
        durations.sort()
        p95 = durations[math.ceil(0.95 * len(durations)) - 1]
        return {
            "service": self.service,
            "request_count": requests,
            "error_count": errors,
            "latency_p95_ms": round(p95, 3),
        }

    def flush(self):
        """Export one window. Failed windows are logged and dropped, never retried."""
        with self._flush_lock:
            payload = self._snapshot()
            if payload is None:
                return None  # Sentinel rejects request_count=0.
            try:
                request = Request(
                    self.endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=self.timeout) as response:
                    if response.status != 202:
                        raise RuntimeError(f"Expected HTTP 202, received {response.status}")
                    receipt = json.loads(response.read(65536))
                logger.info("Telemetry accepted: %s; event_id=%s", payload, receipt.get("event_id"))
                return receipt
            except Exception:
                # Monitoring failures must not fail application requests. No automatic
                # retries: ingestion currently assigns a new ID to every submission.
                logger.exception("Telemetry window dropped after export failure: %s", payload)
                return None

    def start(self):
        if self._thread is not None:
            raise RuntimeError("Create a new reporter rather than starting it twice")
        self._thread = threading.Thread(target=self._run, daemon=True, name="sentinel-export")
        self._thread.start()

    def _run(self):
        while not self._stop.wait(self.interval):
            self.flush()
        self.flush()  # Best-effort final window on orderly shutdown.

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join()


class TelemetryMiddleware:
    """Count HTTP 5xx and unhandled exceptions as errors; preserve app responses."""

    def __init__(self, app, reporter):
        self.app = app
        self.reporter = reporter

    def __call__(self, environ, start_response):
        started = time.perf_counter()
        status_code = 500
        failed = False
        iterable = None

        def capture_status(status, headers, exc_info=None):
            nonlocal status_code
            result = start_response(status, headers, exc_info)
            status_code = int(status.split(" ", 1)[0])
            return result

        try:
            iterable = self.app(environ, capture_status)
            yield from iterable
        except Exception:
            failed = True
            raise
        finally:
            try:
                if iterable is not None and hasattr(iterable, "close"):
                    iterable.close()
            except Exception:
                failed = True
                raise
            finally:
                self.reporter.record(
                    (time.perf_counter() - started) * 1000,
                    failed or status_code >= 500,
                )
