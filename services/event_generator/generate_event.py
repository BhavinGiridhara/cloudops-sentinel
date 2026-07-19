import argparse
import json
import uuid
from datetime import UTC, datetime


VALID_INCIDENT_TYPES = [
    "HighErrorRate",
    "HighLatency",
    "ServiceUnhealthy",
    "DatabaseConnectionFailure",
]

VALID_SEVERITIES = [
    "low",
    "medium",
    "high",
    "critical",
]


def create_incident_event(service, incident_type, severity):

    return {
        "event_id": str(uuid.uuid4()),
        "service": service,
        "environment": "development",
        "incident_type": incident_type,
        "severity": severity,
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": {
            "error_rate": round(0.02 + (hash(service) % 15) / 100, 2),
            "request_count": 4500,
        },
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--service", required=True)
    parser.add_argument("--incident", required=True)
    parser.add_argument("--severity", required=True)

    args = parser.parse_args()

    if args.incident not in VALID_INCIDENT_TYPES:
        raise ValueError(
            f"Incident type must be one of {VALID_INCIDENT_TYPES}"
        )

    if args.severity not in VALID_SEVERITIES:
        raise ValueError(
            f"Severity must be one of {VALID_SEVERITIES}"
        )

    event = create_incident_event(
        args.service,
        args.incident,
        args.severity,
    )

    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()