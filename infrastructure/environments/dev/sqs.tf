resource "aws_sqs_queue" "incident_dead_letter_queue" {
  name                      = "cloudops-sentinel-dev-incident-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Purpose = "Stores incident messages that repeatedly fail processing"
  }
}

resource "aws_sqs_queue" "incident_queue" {
  name = "cloudops-sentinel-dev-incident-queue"

  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.incident_dead_letter_queue.arn
    maxReceiveCount     = 3
  })

  tags = {
    Purpose = "Incident processing queue"
  }
}

resource "aws_sqs_queue_redrive_allow_policy" "incident_dlq" {
  queue_url = aws_sqs_queue.incident_dead_letter_queue.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.incident_queue.arn]
  })
}

output "incident_queue_url" {
  value = aws_sqs_queue.incident_queue.id
}

output "incident_queue_arn" {
  value = aws_sqs_queue.incident_queue.arn
}

output "incident_dlq_url" {
  value = aws_sqs_queue.incident_dead_letter_queue.id
}
