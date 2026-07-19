import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    incident = {
        "incident_id": str(uuid4()),
        "record_type": "INCIDENT",
        "service": event.get("service", "unknown-service"),
        "incident_type": event.get("incident_type", "UnknownIncident"),
        "severity": event.get("severity", "medium"),
        "status": "RECEIVED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(incident),
    )

    return {
        "statusCode": 202,
        "body": json.dumps(
            {
                "message": "Incident accepted",
                "incident_id": incident["incident_id"],
                "sqs_message_id": response["MessageId"],
            }
        ),
    }