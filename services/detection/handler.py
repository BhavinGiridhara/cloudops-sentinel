import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ["INCIDENT_TABLE_NAME"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

table = dynamodb.Table(TABLE_NAME)

ALERT_SEVERITIES = {"HIGH", "CRITICAL"}


def publish_incident_alert(incident: dict[str, Any]) -> None:
    severity = str(incident.get("severity", "UNKNOWN")).upper()
    service = incident.get("service", "unknown-service")
    incident_type = incident.get("incident_type", "UnknownIncident")
    incident_id = incident.get("incident_id", "unknown")
    message = incident.get("message", "No incident message provided")

    subject = f"[{severity}] CloudOps Sentinel: {service}"

    alert_body = {
        "incident_id": incident_id,
        "service": service,
        "incident_type": incident_type,
        "severity": severity,
        "status": incident.get("status"),
        "message": message,
        "created_at": incident.get("created_at"),
        "detected_at": incident.get("detected_at"),
    }

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=json.dumps(alert_body, indent=2),
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    processed = 0
    alerts_published = 0

    for record in event.get("Records", []):
        incident = json.loads(record["body"])

        severity = str(incident.get("severity", "UNKNOWN")).upper()
        incident["severity"] = severity
        incident["status"] = "DETECTED"
        incident["detected_at"] = datetime.now(timezone.utc).isoformat()

        table.put_item(Item=incident)

        if severity in ALERT_SEVERITIES:
            publish_incident_alert(incident)
            alerts_published += 1

        processed += 1

    return {
        "statusCode": 200,
        "processed_records": processed,
        "alerts_published": alerts_published,
    }