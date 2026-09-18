import sys
from pathlib import Path

DETECTION_DIR = Path(__file__).resolve().parents[2] / "services" / "detection"
sys.path.insert(0, str(DETECTION_DIR))

from detector import classify_telemetry


def telemetry(errors: int, latency: int = 250, requests: int = 1000):
    return {
        "request_count": requests,
        "error_count": errors,
        "latency_p95_ms": latency,
    }


def test_healthy_telemetry():
    result = classify_telemetry(telemetry(10, 500))
    assert result["severity"] == "HEALTHY"
    assert result["is_anomaly"] is False


def test_medium_error_rate_boundary():
    result = classify_telemetry(telemetry(50))
    assert result["severity"] == "MEDIUM"
    assert result["incident_type"] == "ElevatedErrorRate"


def test_high_error_rate_boundary():
    result = classify_telemetry(telemetry(100))
    assert result["severity"] == "HIGH"


def test_critical_error_rate_boundary():
    result = classify_telemetry(telemetry(150))
    assert result["severity"] == "CRITICAL"


def test_latency_can_escalate_severity():
    result = classify_telemetry(telemetry(10, 3500))
    assert result["severity"] == "CRITICAL"
    assert result["incident_type"] == "HighLatency"


def test_combined_degradation():
    result = classify_telemetry(telemetry(120, 2500))
    assert result["severity"] == "HIGH"
    assert result["incident_type"] == "ServiceDegradation"
