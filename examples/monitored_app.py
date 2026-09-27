"""Run from repository root: python -m examples.monitored_app --endpoint URL."""

import argparse
import json
import logging
import time
from wsgiref.simple_server import make_server

from services.instrumentation.wsgi import TelemetryMiddleware, TelemetryReporter


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path == "/slow":
        time.sleep(3.2)
    status = {
        "/": "200 OK",
        "/ok": "200 OK",
        "/slow": "200 OK",
        "/fail": "500 Internal Server Error",
    }.get(path, "404 Not Found")
    body = json.dumps({"path": path, "status": int(status[:3])}).encode("utf-8")
    start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True, help="Sentinel POST /incidents URL")
    parser.add_argument("--service", default="checkout-demo")
    parser.add_argument("--interval", type=float, default=60)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reporter = TelemetryReporter(args.service, args.endpoint, interval=args.interval)
    app = TelemetryMiddleware(application, reporter)
    # Loopback only: /fail and /slow deliberately create bad responses for the demo.
    with make_server("127.0.0.1", args.port, app) as server:
        reporter.start()
        logging.info("Demo app: http://127.0.0.1:%s; routes /ok /fail /slow", args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            reporter.stop()


if __name__ == "__main__":
    main()
