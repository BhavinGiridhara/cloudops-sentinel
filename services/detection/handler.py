import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3


dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["INCIDENT_TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    processed = 0

    for record in event.get("Records", []):
        incident = json.loads(record["body"])

        incident["status"] = "DETECTED"
        incident["detected_at"] = datetime.now(timezone.utc).isoformat()

        table.put_item(Item=incident)
        processed += 1

    return {
        "statusCode": 200,
        "processed_records": processed,
    }