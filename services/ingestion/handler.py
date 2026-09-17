import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]

REQUIRED_FIELDS = ("service", "incident_type", "severity", "message")
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _request_data(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body", event)

    if isinstance(body, str):
        body = json.loads(body)

    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object")

    return body


def _validation_errors(request_data: dict[str, Any]) -> list[str]:
    errors = []

    for field in REQUIRED_FIELDS:
        value = request_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    severity = request_data.get("severity")
    if isinstance(severity, str) and severity.strip():
        normalized_severity = severity.strip().upper()
        if normalized_severity not in VALID_SEVERITIES:
            allowed = ", ".join(sorted(VALID_SEVERITIES))
            errors.append(f"severity must be one of: {allowed}")

    return errors


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        request_data = _request_data(event)
    except json.JSONDecodeError:
        return _response(400, {"message": "Request body must contain valid JSON"})
    except ValueError as error:
        return _response(400, {"message": str(error)})

    validation_errors = _validation_errors(request_data)
    if validation_errors:
        return _response(
            400,
            {
                "message": "Invalid incident request",
                "errors": validation_errors,
            },
        )

    incident = {
        "incident_id": str(uuid4()),
        "record_type": "INCIDENT",
        "service": request_data["service"].strip(),
        "incident_type": request_data["incident_type"].strip(),
        "severity": request_data["severity"].strip().upper(),
        "message": request_data["message"].strip(),
        "status": "RECEIVED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(incident),
        )
    except Exception as error:
        print(f"Failed to ingest incident: {error}")
        return _response(500, {"message": "Failed to accept incident"})

    return _response(
        202,
        {
            "message": "Incident accepted",
            "incident_id": incident["incident_id"],
            "sqs_message_id": response["MessageId"],
        },
    )
