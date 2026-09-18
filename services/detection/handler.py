import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3

try:
    from .detector import classify_telemetry
except ImportError:
    from detector import classify_telemetry


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ["INCIDENT_TABLE_NAME"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
table = dynamodb.Table(TABLE_NAME)

ALERT_SEVERITIES = {"HIGH", "CRITICAL"}


def publish_incident_alert(incident: dict[str, Any]) -> None:
    severity = str(incident["severity"])
    service = str(incident["service"])
    incident_type = str(incident["incident_type"])
    reasons = ", ".join(incident.get("detection_reasons", []))

    subject = f"[{severity}] {service} - {incident_type}"
    alert_body = f"""CloudOps Sentinel Incident Alert

Severity      : {severity}
Service       : {service}
Incident Type : {incident_type}
Status        : {incident['status']}

Why it was detected
{reasons}

Observed telemetry
Requests       : {incident['request_count']}
Errors         : {incident['error_count']}
Error Rate     : {incident['error_rate_percent']}%
P95 Latency    : {incident['latency_p95_ms']} ms

Created At     : {incident['created_at']}
Detected At    : {incident['detected_at']}
Incident ID    : {incident['incident_id']}

This notification was generated automatically by CloudOps Sentinel.
"""

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=alert_body,
    )


def build_incident(telemetry: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "incident_id": telemetry["event_id"],
        "record_type": "INCIDENT",
        "source_event_type": "TELEMETRY",
        "service": telemetry["service"],
        "incident_type": result["incident_type"],
        "severity": result["severity"],
        "status": "DETECTED",
        "request_count": int(telemetry["request_count"]),
        "error_count": int(telemetry["error_count"]),
        "error_rate_percent": Decimal(str(result["error_rate_percent"])),
        "latency_p95_ms": Decimal(str(telemetry["latency_p95_ms"])),
        "detection_reasons": result["reasons"],
        "message": f"Anomaly detected: {', '.join(result['reasons'])}",
        "created_at": telemetry["created_at"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def process_legacy_incident(incident: dict[str, Any]) -> bool:
    """Preserves compatibility with any older queued incident messages."""
    severity = str(incident.get("severity", "UNKNOWN")).upper()
    incident["severity"] = severity
    incident["status"] = "DETECTED"
    incident["detected_at"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=incident)
    if severity in ALERT_SEVERITIES:
        publish_incident_alert(incident)
        return True
    return False


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    processed = 0
    anomalies_detected = 0
    alerts_published = 0

    for record in event.get("Records", []):
        payload = json.loads(record["body"])

        if payload.get("event_type") != "TELEMETRY":
            if process_legacy_incident(payload):
                alerts_published += 1
            processed += 1
            continue

        result = classify_telemetry(payload)
        print(
            json.dumps(
                {
                    "event_id": payload["event_id"],
                    "service": payload["service"],
                    "severity": result["severity"],
                    "error_rate_percent": result["error_rate_percent"],
                    "latency_p95_ms": payload["latency_p95_ms"],
                    "is_anomaly": result["is_anomaly"],
                }
            )
        )

        if result["is_anomaly"]:
            incident = build_incident(payload, result)
            table.put_item(Item=incident)
            anomalies_detected += 1

            if result["severity"] in ALERT_SEVERITIES:
                publish_incident_alert(incident)
                alerts_published += 1

        processed += 1

    return {
        "statusCode": 200,
        "processed_records": processed,
        "anomalies_detected": anomalies_detected,
        "alerts_published": alerts_published,
    }
