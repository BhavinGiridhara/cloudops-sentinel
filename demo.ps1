# CloudOps Sentinel - Telemetry Detection Demo
# Simulates degraded production telemetry. The caller does NOT provide severity.

$endpoint = "https://w1v2pqehn9.execute-api.us-east-1.amazonaws.com/incidents"

$telemetry = @{
    service        = "checkout-api"
    request_count  = 1000
    error_count    = 173
    latency_p95_ms = 3850
}

$errorRate = ($telemetry.error_count / $telemetry.request_count) * 100

Write-Host ""
Write-Host "========================================"
Write-Host "       CLOUDOPS SENTINEL DEMO"
Write-Host "========================================"
Write-Host ""
Write-Host "Simulating degraded production telemetry..."
Write-Host ""
Write-Host "  Service:       $($telemetry.service)"
Write-Host "  Requests:      $($telemetry.request_count)"
Write-Host "  Errors:        $($telemetry.error_count)"
Write-Host ("  Error Rate:    {0:N1}%" -f $errorRate)
Write-Host "  P95 Latency:   $($telemetry.latency_p95_ms) ms"
Write-Host ""
Write-Host "Notice: this client does NOT specify incident type or severity."
Write-Host "CloudOps Sentinel will determine those from the telemetry."
Write-Host ""

$body = $telemetry | ConvertTo-Json

try {
    $response = Invoke-RestMethod `
        -Uri $endpoint `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "Telemetry accepted successfully."
    Write-Host ""
    Write-Host "  Event ID:       $($response.event_id)"
    Write-Host "  SQS Message ID: $($response.sqs_message_id)"
    Write-Host ""
    Write-Host "Processing pipeline:"
    Write-Host ""
    Write-Host "  API Gateway"
    Write-Host "       |"
    Write-Host "       v"
    Write-Host "  Ingestion Lambda"
    Write-Host "       |"
    Write-Host "       v"
    Write-Host "  SQS"
    Write-Host "       |"
    Write-Host "       v"
    Write-Host "  Detection Engine"
    Write-Host "       |"
    Write-Host "       +----> calculate error rate + evaluate latency"
    Write-Host "       |"
    Write-Host "       +----> classify severity"
    Write-Host "       |"
    Write-Host "       +----> DynamoDB (anomalies only)"
    Write-Host "       |"
    Write-Host "       +----> SNS (HIGH/CRITICAL) ----> Email"
    Write-Host ""
    Write-Host "Expected classification for this demo: CRITICAL"
    Write-Host "Check email for the automatically classified alert."
}
catch {
    Write-Host "Demo request failed."
    Write-Host $_.Exception.Message
}
