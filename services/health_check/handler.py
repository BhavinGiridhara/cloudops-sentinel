import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3


sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INCIDENT_QUEUE_URL"]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    telemetry = {
        "event_id": str(uuid4()),
        "event_type": "TELEMETRY",
        "source": "scheduled-health-check",
        "service": "payments-api",
        "request_count": 100,
        "error_count": 1,
        "latency_p95_ms": 250.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(telemetry),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Synthetic healthy telemetry queued",
                "event_id": telemetry["event_id"],
                "sqs_message_id": response["MessageId"],
            }
        ),
    }
