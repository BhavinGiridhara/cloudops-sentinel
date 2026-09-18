import json

from services.detection import handler


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, **kwargs):
        self.items.append(kwargs["Item"])
        return {}


class FakeSns:
    def __init__(self):
        self.messages = []

    def publish(self, **kwargs):
        self.messages.append(kwargs)
        return {"MessageId": "alert-123"}


def telemetry_record(
    message_id,
    request_count=1000,
    error_count=173,
    latency_p95_ms=3850,
):
    return {
        "messageId": message_id,
        "body": json.dumps(
            {
                "event_id": f"event-{message_id}",
		"event_type": "TELEMETRY",
                "service": "checkout-api",
                "request_count": request_count,
                "error_count": error_count,
                "latency_p95_ms": latency_p95_ms,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ),
    }


def test_critical_telemetry_is_stored_and_alerted(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()

    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    result = handler.lambda_handler(
        {"Records": [telemetry_record("1")]},
        None,
    )

    assert result["processed_records"] == 1
    assert result["anomalies_detected"] == 1
    assert result["alerts_published"] == 1

    assert len(fake_table.items) == 1

    incident = fake_table.items[0]

    assert incident["severity"] == "CRITICAL"
    assert incident["incident_type"] == "ServiceDegradation"
    assert incident["status"] == "DETECTED"
    assert incident["request_count"] == 1000
    assert incident["error_count"] == 173
    assert incident["detected_at"]

    assert len(fake_sns.messages) == 1
    assert "CRITICAL" in fake_sns.messages[0]["Subject"]


def test_medium_telemetry_is_stored_without_alert(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()

    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    result = handler.lambda_handler(
        {
            "Records": [
                telemetry_record(
                    "1",
                    request_count=1000,
                    error_count=60,
                    latency_p95_ms=500,
                )
            ]
        },
        None,
    )

    assert result["processed_records"] == 1
    assert result["alerts_published"] == 0

    assert len(fake_table.items) == 1
    assert fake_table.items[0]["severity"] == "MEDIUM"
    assert fake_sns.messages == []


def test_healthy_telemetry_creates_no_incident(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()

    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    result = handler.lambda_handler(
        {
            "Records": [
                telemetry_record(
                    "1",
                    request_count=1000,
                    error_count=10,
                    latency_p95_ms=250,
                )
            ]
        },
        None,
    )

    assert result["processed_records"] == 1
    assert result["alerts_published"] == 0
    assert fake_table.items == []
    assert fake_sns.messages == []


def test_multiple_records_are_processed(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()

    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    event = {
        "Records": [
            telemetry_record(
                "healthy",
                request_count=1000,
                error_count=10,
                latency_p95_ms=250,
            ),
            telemetry_record(
                "medium",
                request_count=1000,
                error_count=60,
                latency_p95_ms=500,
            ),
            telemetry_record(
                "critical",
                request_count=1000,
                error_count=173,
                latency_p95_ms=3850,
            ),
        ]
    }

    result = handler.lambda_handler(event, None)

    assert result["processed_records"] == 3
    assert result["alerts_published"] == 1

    # HEALTHY is not persisted.
    assert len(fake_table.items) == 2

    assert len(fake_sns.messages) == 1