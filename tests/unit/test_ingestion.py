import json

from services.ingestion import handler


VALID_INCIDENT = {
    "service": "checkout-api",
    "incident_type": "CheckoutOutage",
    "severity": "critical",
    "message": "Customers cannot complete checkout",
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

    response = handler.lambda_handler({"body": json.dumps(VALID_INCIDENT)}, None)

    assert response["statusCode"] == 202
    response_body = json.loads(response["body"])
    assert response_body["incident_id"]
    assert response_body["sqs_message_id"] == "message-123"

    queued_incident = json.loads(fake_sqs.messages[0]["MessageBody"])
    assert queued_incident["severity"] == "CRITICAL"
    assert queued_incident["status"] == "RECEIVED"
    assert queued_incident["record_type"] == "INCIDENT"
    assert queued_incident["created_at"]


def test_direct_invocation_is_supported(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler(VALID_INCIDENT, None)

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


def test_missing_fields_return_actionable_errors(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)

    response = handler.lambda_handler({"body": "{}"}, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["message"] == "Invalid incident request"
    assert len(body["errors"]) == 4
    assert fake_sqs.messages == []


def test_invalid_severity_returns_400(monkeypatch):
    fake_sqs = FakeSqs()
    monkeypatch.setattr(handler, "sqs", fake_sqs)
    incident = {**VALID_INCIDENT, "severity": "urgent"}

    response = handler.lambda_handler({"body": json.dumps(incident)}, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert any("severity must be one of" in error for error in body["errors"])
    assert fake_sqs.messages == []


def test_sqs_failure_returns_500(monkeypatch):
    class FailingSqs:
        def send_message(self, **kwargs):
            raise RuntimeError("SQS unavailable")

    monkeypatch.setattr(handler, "sqs", FailingSqs())

    response = handler.lambda_handler({"body": json.dumps(VALID_INCIDENT)}, None)

    assert response["statusCode"] == 500
