from typing import Any

ERROR_THRESHOLDS = {
    "MEDIUM": 5.0,
    "HIGH": 10.0,
    "CRITICAL": 15.0,
}

LATENCY_THRESHOLDS_MS = {
    "MEDIUM": 1000,
    "HIGH": 2000,
    "CRITICAL": 3000,
}

SEVERITY_RANK = {"HEALTHY": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _severity_for_error_rate(error_rate_percent: float) -> str:
    if error_rate_percent >= ERROR_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    if error_rate_percent >= ERROR_THRESHOLDS["HIGH"]:
        return "HIGH"
    if error_rate_percent >= ERROR_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "HEALTHY"


def _severity_for_latency(latency_p95_ms: float) -> str:
    if latency_p95_ms >= LATENCY_THRESHOLDS_MS["CRITICAL"]:
        return "CRITICAL"
    if latency_p95_ms >= LATENCY_THRESHOLDS_MS["HIGH"]:
        return "HIGH"
    if latency_p95_ms >= LATENCY_THRESHOLDS_MS["MEDIUM"]:
        return "MEDIUM"
    return "HEALTHY"


def classify_telemetry(telemetry: dict[str, Any]) -> dict[str, Any]:
    request_count = int(telemetry["request_count"])
    error_count = int(telemetry["error_count"])
    latency_p95_ms = float(telemetry["latency_p95_ms"])

    error_rate_percent = (
        (error_count / request_count) * 100 if request_count > 0 else 0.0
    )

    error_severity = _severity_for_error_rate(error_rate_percent)
    latency_severity = _severity_for_latency(latency_p95_ms)
    severity = max(
        (error_severity, latency_severity),
        key=lambda value: SEVERITY_RANK[value],
    )

    reasons: list[str] = []
    if error_severity != "HEALTHY":
        reasons.append(f"error rate {error_rate_percent:.1f}%")
    if latency_severity != "HEALTHY":
        reasons.append(f"p95 latency {latency_p95_ms:.0f} ms")

    if error_severity != "HEALTHY" and latency_severity != "HEALTHY":
        incident_type = "ServiceDegradation"
    elif error_severity != "HEALTHY":
        incident_type = "ElevatedErrorRate"
    elif latency_severity != "HEALTHY":
        incident_type = "HighLatency"
    else:
        incident_type = None

    return {
        "is_anomaly": severity != "HEALTHY",
        "severity": severity,
        "incident_type": incident_type,
        "error_rate_percent": round(error_rate_percent, 2),
        "reasons": reasons,
    }
