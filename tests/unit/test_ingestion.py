import json

from services.ingestion import handler


VALID_TELEMETRY = {
    "service": "checkout-api",
    "request_count": 1000,
    "error_count": 173,
    "latency_p95_ms": 3850,
}


class FakeSqs:
    def __init__(self):
        self.messages = []

    def send_message(self, **kwargs):
        self.messages.append(kwargs)
        return {"MessageId": "message-123"}


def test_valid_api_gateway_request_is_queued(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler(
        {"body": json.dumps(VALID_TELEMETRY)}, None
    )

    assert response["statusCode"] == 202

    response_body = json.loads(response["body"])
    assert response_body["event_id"]
    assert response_body["sqs_message_id"] == "message-123"

    queued_event = json.loads(fake_sqs.messages[0]["MessageBody"])

    assert queued_event["service"] == "checkout-api"
    assert queued_event["request_count"] == 1000
    assert queued_event["error_count"] == 173
    assert queued_event["latency_p95_ms"] == 3850
    assert queued_event["event_id"]
    assert queued_event["created_at"]

    # Classification belongs to the detection service, not ingestion.
    assert "severity" not in queued_event
    assert "incident_type" not in queued_event


def test_direct_invocation_is_supported(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler(VALID_TELEMETRY, None)

    assert response["statusCode"] == 202
    assert len(fake_sqs.messages) == 1


def test_malformed_json_returns_400(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler({"body": "{not-json"}, None)

    assert response["statusCode"] == 400
    assert fake_sqs.messages == []


def test_non_object_json_returns_400(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler({"body": "[]"}, None)

    assert response["statusCode"] == 400
    assert fake_sqs.messages == []


def test_missing_fields_return_actionable_error(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler({"body": "{}"}, None)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])

    assert "Missing required fields" in body["message"]
    assert "service" in body["message"]
    assert "request_count" in body["message"]
    assert "error_count" in body["message"]
    assert "latency_p95_ms" in body["message"]

    assert fake_sqs.messages == []


def test_caller_does_not_supply_severity(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    telemetry = {
        **VALID_TELEMETRY,
        "severity": "CRITICAL",
    }

    response = handler.lambda_handler(
        {"body": json.dumps(telemetry)}, None
    )

    assert response["statusCode"] == 202

    queued_event = json.loads(fake_sqs.messages[0]["MessageBody"])

    # The ingestion service must not trust caller-provided classification.
    assert "severity" not in queued_event


def test_sqs_failure_returns_500(monkeypatch):
    class FailingSqs:
        def send_message(self, **kwargs):
            raise RuntimeError("SQS unavailable")

    monkeypatch.setattr(handler, "sqs", FailingSqs())

    response = handler.lambda_handler(
        {"body": json.dumps(VALID_TELEMETRY)}, None
    )

    assert response["statusCode"] == 500