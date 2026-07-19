resource "aws_sqs_queue" "incident_queue" {
  name = "cloudops-sentinel-dev-incident-queue"

  visibility_timeout_seconds = 30

  message_retention_seconds = 345600

  receive_wait_time_seconds = 20

  sqs_managed_sse_enabled = true

  tags = {
    Purpose = "Incident processing queue"
  }
}

output "incident_queue_url" {
  value = aws_sqs_queue.incident_queue.id
}

output "incident_queue_arn" {
  value = aws_sqs_queue.incident_queue.arn
}