"""Real loopback HTTP requests and timed export; AWS boundaries use test doubles."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import urlopen
from wsgiref.simple_server import make_server

from examples.monitored_app import application
from services.detection import handler as detection
from services.ingestion import handler as ingestion
from services.instrumentation.wsgi import TelemetryMiddleware, TelemetryReporter


def test_real_requests_are_exported_validated_classified_and_alerted(monkeypatch):
    queued, incidents, alerts = [], [], []
    received = threading.Event()

    def send_message(**kwargs):
        queued.append(kwargs["MessageBody"])
        return {"MessageId": "test-message"}

    monkeypatch.setattr(ingestion, "sqs", SimpleNamespace(send_message=send_message))
    monkeypatch.setattr(detection, "table", SimpleNamespace(put_item=lambda **kw: incidents.append(kw["Item"])))
    monkeypatch.setattr(detection, "sns", SimpleNamespace(publish=lambda **kw: alerts.append(kw)))

    class Sink(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            result = ingestion.lambda_handler({"body": body.decode()}, None)
            encoded = result["body"].encode()
            self.send_response(result["statusCode"])
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            received.set()

        def log_message(self, *args):
            pass

    with HTTPServer(("127.0.0.1", 0), Sink) as sink:
        sink_thread = threading.Thread(target=sink.serve_forever, daemon=True)
        sink_thread.start()
        metrics = TelemetryReporter("real-demo", f"http://127.0.0.1:{sink.server_port}/incidents", interval=0.05)
        with make_server("127.0.0.1", 0, TelemetryMiddleware(application, metrics)) as app:
            app_thread = threading.Thread(target=app.serve_forever, daemon=True)
            app_thread.start()
            try:
                for path in ["/ok", "/ok", "/ok", "/fail"]:
                    try:
                        with urlopen(f"http://127.0.0.1:{app.server_port}{path}", timeout=2) as response:
                            response.read()
                    except HTTPError as error:
                        assert error.code == 500
                        error.close()
                # Stop serving so the last response iterator is finalized before export.
                app.shutdown()
                app_thread.join()
                metrics.start()
                assert received.wait(3), "Timed reporter did not POST telemetry"
                metrics.stop()
                assert len(queued) == 1
                payload = json.loads(queued[0])
                assert payload["request_count"] == 4
                assert payload["error_count"] == 1
                assert payload["latency_p95_ms"] >= 0
                assert "severity" not in payload
                result = detection.lambda_handler({"Records": [{"body": queued[0]}]}, None)
                assert result["alerts_published"] == 1
                assert incidents[0]["severity"] == "CRITICAL"
                assert incidents[0]["error_rate_percent"] == 25
                assert len(alerts) == 1
            finally:
                app.shutdown()
                app_thread.join()
                metrics.stop()
                sink.shutdown()
                sink_thread.join()
