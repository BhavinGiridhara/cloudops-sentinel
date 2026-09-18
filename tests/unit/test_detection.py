import json

import pytest

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


def sqs_record(message_id, severity):
    return {
        "messageId": message_id,
        "body": json.dumps(
            {
                "incident_id": f"incident-{message_id}",
                "record_type": "INCIDENT",
                "service": "checkout-api",
                "incident_type": "Latency",
                "severity": severity,
                "message": "Latency exceeded threshold",
                "status": "RECEIVED",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ),
    }


@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_high_priority_incident_is_stored_and_alerted(monkeypatch, severity):
    fake_table = FakeTable()
    fake_sns = FakeSns()
    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    result = handler.lambda_handler({"Records": [sqs_record("1", severity)]}, None)

    assert result["processed_records"] == 1
    assert result["alerts_published"] == 1
    assert result["batchItemFailures"] == []
    assert fake_table.items[0]["status"] == "DETECTED"
    assert fake_table.items[0]["detected_at"]
    assert len(fake_sns.messages) == 1
    assert severity in fake_sns.messages[0]["Subject"]


def test_medium_incident_is_stored_without_alert(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()
    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    result = handler.lambda_handler({"Records": [sqs_record("1", "MEDIUM")]}, None)

    assert result["processed_records"] == 1
    assert result["alerts_published"] == 0
    assert len(fake_table.items) == 1
    assert fake_sns.messages == []


def test_multiple_records_are_processed(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()
    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    event = {
        "Records": [
            sqs_record("1", "LOW"),
            sqs_record("2", "HIGH"),
            sqs_record("3", "CRITICAL"),
        ]
    }
    result = handler.lambda_handler(event, None)

    assert result["processed_records"] == 3
    assert result["alerts_published"] == 2
    assert len(fake_table.items) == 3
    assert len(fake_sns.messages) == 2


def test_bad_record_is_reported_without_retrying_successes(monkeypatch):
    fake_table = FakeTable()
    fake_sns = FakeSns()
    monkeypatch.setattr(handler, "table", fake_table)
    monkeypatch.setattr(handler, "sns", fake_sns)

    event = {
        "Records": [
            sqs_record("good", "LOW"),
            {"messageId": "bad", "body": "not-json"},
        ]
    }
    result = handler.lambda_handler(event, None)

    assert result["processed_records"] == 1
    assert result["batchItemFailures"] == [{"itemIdentifier": "bad"}]
    assert len(fake_table.items) == 1
