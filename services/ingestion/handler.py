import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]

REQUIRED_FIELDS = (
    "service",
    "request_count",
    "error_count",
    "latency_p95_ms",
)


def response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def parse_request(event: dict[str, Any]) -> dict[str, Any]:
    if "body" not in event:
        return event

    body = event.get("body")
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    return {}


def validate_telemetry(data: dict[str, Any]) -> str | None:
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"

    if not isinstance(data["service"], str) or not data["service"].strip():
        return "service must be a non-empty string"

    for field in ("request_count", "error_count", "latency_p95_ms"):
        value = data[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{field} must be a number"
        if value < 0:
            return f"{field} cannot be negative"

    if int(data["request_count"]) != data["request_count"]:
        return "request_count must be a whole number"
    if int(data["error_count"]) != data["error_count"]:
        return "error_count must be a whole number"
    if data["request_count"] <= 0:
        return "request_count must be greater than zero"
    if data["error_count"] > data["request_count"]:
        return "error_count cannot exceed request_count"

    return None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        request_data = parse_request(event)
        validation_error = validate_telemetry(request_data)
        if validation_error:
            return response(400, {"message": validation_error})

        telemetry = {
            "event_id": str(uuid4()),
            "event_type": "TELEMETRY",
            "service": request_data["service"].strip(),
            "request_count": int(request_data["request_count"]),
            "error_count": int(request_data["error_count"]),
            "latency_p95_ms": float(request_data["latency_p95_ms"]),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        queue_response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(telemetry),
        )

        return response(
            202,
            {
                "message": "Telemetry accepted",
                "event_id": telemetry["event_id"],
                "sqs_message_id": queue_response["MessageId"],
            },
        )

    except json.JSONDecodeError:
        return response(400, {"message": "Request body must contain valid JSON"})
    except Exception as error:
        print(f"Failed to ingest telemetry: {error}")
        return response(500, {"message": "Failed to accept telemetry"})
