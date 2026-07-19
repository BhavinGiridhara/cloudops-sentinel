import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        request_data = event

        if "body" in event:
            body = event.get("body")

            if isinstance(body, str):
                request_data = json.loads(body)
            elif isinstance(body, dict):
                request_data = body
            else:
                request_data = {}

        incident = {
            "incident_id": str(uuid4()),
            "record_type": "INCIDENT",
            "service": request_data.get("service", "unknown-service"),
            "incident_type": request_data.get(
                "incident_type",
                "UnknownIncident",
            ),
            "severity": request_data.get("severity", "MEDIUM").upper(),
            "message": request_data.get("message", ""),
            "status": "RECEIVED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(incident),
        )

        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "message": "Incident accepted",
                    "incident_id": incident["incident_id"],
                    "sqs_message_id": response["MessageId"],
                }
            ),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "message": "Request body must contain valid JSON",
                }
            ),
        }

    except Exception as error:
        print(f"Failed to ingest incident: {error}")

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "message": "Failed to accept incident",
                }
            ),
        }