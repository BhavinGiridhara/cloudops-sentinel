# Automatic application telemetry

The optional WSGI middleware measures real incoming HTTP requests. It sends the
same four-field JSON contract as the original manual demo, so the Sentinel API
and detector do not need a schema change. No additional Python packages are
required for the middleware or local example (Python 3.12 recommended).

## What is measured

- `service`: the configured application name.
- `request_count`: completed requests in the current process's reporting window.
- `error_count`: HTTP 5xx responses or unhandled application/iteration exceptions.
  HTTP 4xx responses count as requests, but not server failures.
- `latency_p95_ms`: nearest-rank p95 of server-side request durations, measured
  with a monotonic clock through response iteration and cleanup. This is not
  the client's complete network round-trip latency.

The default window is approximately 60 seconds. Empty windows are not submitted.
Requests are assigned to a window when they finish. A lock protects counters
and window rotation; HTTP export happens outside that lock in a background thread.
All request/error counts are retained. Durations use a bounded reservoir of up
to 10,000 samples per window: p95 is exact below that cap and an estimate above it.

## Windows PowerShell demonstration

First check out the branch containing this feature, or merge the PR and update
your local copy. Run commands from the repository root. Use the actual deployed
Sentinel endpoint. In your existing Terraform workspace, this reads the URL:

```powershell
terraform -chdir=./infrastructure/environments/dev output -raw create_incident_endpoint
```

An unrelated fresh clone will not contain your existing local Terraform state.
You can also find the endpoint in your AWS API Gateway console.

Terminal 1:

```powershell
python -m examples.monitored_app --endpoint "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/incidents"
```

Terminal 2, also from the repository root:

```powershell
python -m examples.send_traffic --scenario errors
```

This sends 20 actual HTTP requests to the local application, including five
deliberate HTTP 500 responses. The traffic generator does not calculate or send
telemetry. The middleware does that automatically on the next reporting tick.
If these requests finish in one reporting window, the error rate is 25% and the
existing detector classifies it CRITICAL. If a tick splits the requests, inspect
the actual reported windows rather than expecting exactly one incident.

Wait up to a minute for the app log to show `Telemetry accepted` and the API's
`event_id`. Locate that ID in detection logs and the DynamoDB incident table.
For email delivery, the existing SNS topic needs a confirmed email subscription.
HTTP 202 proves queue acceptance, not downstream completion or email delivery.

Other scenarios:

```powershell
python -m examples.send_traffic --scenario healthy
python -m examples.send_traffic --scenario slow
```

Run these separately, waiting for each reporting window to export. Healthy sends
20 successful requests; it should produce no incident if measured latency also
stays below the threshold. Slow sends three requests whose handler deliberately
waits 3.2 seconds each, allowing latency alone to trigger CRITICAL classification.
For shorter demos, add `--interval 15` when starting the app. Use Ctrl+C to stop;
orderly shutdown attempts to export remaining measurements.

The demonstration server binds only to 127.0.0.1. Its deliberate failure routes
and Python reference server are for local demonstrations, not production hosting.

## Connecting an existing WSGI application

Wrap the application's WSGI callable with `TelemetryMiddleware` and use the
wrapped callable in your server. Start the reporter once per worker after any
process fork and stop it during that worker's orderly shutdown:

```python
from services.instrumentation.wsgi import TelemetryMiddleware, TelemetryReporter

reporter = TelemetryReporter("my-service", sentinel_endpoint, interval=60)
instrumented_application = TelemetryMiddleware(existing_wsgi_application, reporter)
# In the worker startup hook: reporter.start()
# Serve instrumented_application instead of existing_wsgi_application.
# In the worker shutdown hook: reporter.stop()
```

For Flask, wrap `app.wsgi_app`; lifecycle hooks still belong to the worker setup.
This is a WSGI integration. FastAPI is ASGI and needs a separate ASGI adapter;
do not wrap a FastAPI application directly with this middleware.

Each worker reports its own measurements. The current detector evaluates each
report separately, with no cross-worker aggregation or minimum sample size.
The feature does not discover applications automatically: each application must
be instrumented and configured with the service name and endpoint.

## Delivery and deployment limits

Exports use a three-second socket timeout and accept only HTTP 202 as success.
An export failure is logged and the window is dropped. There is no durable buffer
or retry policy yet: retrying an ambiguous submission could create duplicate
incidents because ingestion assigns a new event ID per request. Application
responses are not replaced by exporter errors. Abrupt process termination can
lose unsent telemetry. Authentication, durable delivery, and tracing are future
work; the existing public ingestion API is unchanged.

The accompanying Terraform change packages both `handler.py` and `detector.py`
at the root of the detection Lambda ZIP. Review and apply that change in the
existing deployment workspace before relying on a fresh deployment:

```powershell
terraform -chdir=./infrastructure/environments/dev plan
terraform -chdir=./infrastructure/environments/dev apply
```

Review the plan before applying. This feature does not deploy AWS changes itself.

## Validation and interview explanation

```powershell
python -m pytest -q
```

The integration test sends real loopback HTTP requests, waits for a timed HTTP
export, runs the existing ingestion validator and detector, and checks incident
and alert behavior. AWS calls use test doubles; it does not prove a live AWS
deployment works.

"I added middleware that measures incoming requests, counts server failures, and
calculates p95 latency. A background reporter sends those measurements to Sentinel
periodically. The local demo generates actual successful, failing, and slow HTTP
requests, so the telemetry is measured automatically rather than hand-entered."
