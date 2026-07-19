import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    incident = {
        "incident_id": str(uuid.uuid4()),
        "record_type": "INCIDENT",
        "source": "scheduled-health-check",
        "service": "payments-api",
        "severity": "LOW",
        "incident_type": "SyntheticHealthCheck",
        "message": "Scheduled synthetic health check completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "RECEIVED",
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(incident),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Synthetic health-check event queued",
                "incident_id": incident["incident_id"],
                "sqs_message_id": response["MessageId"],
            }
        ),
    }