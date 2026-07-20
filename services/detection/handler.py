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
    service = str(incident.get("service", "unknown-service"))
    incident_type = str(
        incident.get("incident_type", "UnknownIncident")
    )
    incident_id = str(incident.get("incident_id", "unknown"))
    message = str(
        incident.get("message", "No incident message provided")
    )
    status = str(incident.get("status", "UNKNOWN"))
    created_at = str(incident.get("created_at", "unknown"))
    detected_at = str(incident.get("detected_at", "unknown"))

    subject = f"[{severity}] {service} - {incident_type}"

    alert_body = f"""🚨 CloudOps Sentinel Incident Alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Severity      : {severity}
Service       : {service}
Incident Type : {incident_type}
Status        : {status}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description

{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Created At    : {created_at}
Detected At   : {detected_at}

Incident ID

{incident_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This notification was generated automatically by CloudOps Sentinel.
"""

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=alert_body,
    )


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    processed = 0
    alerts_published = 0

    for record in event.get("Records", []):
        incident = json.loads(record["body"])

        severity = str(
            incident.get("severity", "UNKNOWN")
        ).upper()

        incident["severity"] = severity
        incident["status"] = "DETECTED"
        incident["detected_at"] = datetime.now(
            timezone.utc
        ).isoformat()

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