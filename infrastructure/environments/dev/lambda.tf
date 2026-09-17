data "archive_file" "ingestion" {
  type        = "zip"
  source_file = "${path.module}/../../../services/ingestion/handler.py"
  output_path = "${path.module}/ingestion.zip"
}

data "archive_file" "detection" {
  type        = "zip"
  source_file = "${path.module}/../../../services/detection/handler.py"
  output_path = "${path.module}/detection.zip"
}

data "archive_file" "health_check" {
  type        = "zip"
  source_file = "${path.module}/../../../services/health_check/handler.py"
  output_path = "${path.module}/health_check.zip"
}

resource "aws_lambda_function" "ingestion" {
  function_name = "cloudops-sentinel-dev-ingestion"

  filename         = data.archive_file.ingestion.output_path
  source_code_hash = data.archive_file.ingestion.output_base64sha256

  role    = aws_iam_role.ingestion_lambda.arn
  handler = "handler.lambda_handler"
  runtime = "python3.12"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      INCIDENT_QUEUE_URL = aws_sqs_queue.incident_queue.url
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.ingestion_basic_execution,
    aws_iam_role_policy.ingestion_queue_access
  ]

  tags = {
    Purpose = "Receives and queues incident events"
  }
}

output "ingestion_lambda_name" {
  value = aws_lambda_function.ingestion.function_name
}

output "ingestion_lambda_arn" {
  value = aws_lambda_function.ingestion.arn
}

resource "aws_lambda_function" "detection" {
  function_name = "cloudops-sentinel-dev-detection"

  filename         = data.archive_file.detection.output_path
  source_code_hash = data.archive_file.detection.output_base64sha256

  role    = aws_iam_role.detection_lambda.arn
  handler = "handler.lambda_handler"
  runtime = "python3.12"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      INCIDENT_TABLE_NAME = aws_dynamodb_table.incidents.name
      SNS_TOPIC_ARN       = aws_sns_topic.incident_alerts.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.detection_basic_execution,
    aws_iam_role_policy.detection_data_access
  ]

  tags = {
    Purpose = "Processes incident events and stores detections"
  }
}

output "detection_lambda_name" {
  value = aws_lambda_function.detection.function_name
}

output "detection_lambda_arn" {
  value = aws_lambda_function.detection.arn
}

resource "aws_lambda_function" "health_check" {
  function_name = "cloudops-sentinel-dev-health-check"

  filename         = data.archive_file.health_check.output_path
  source_code_hash = data.archive_file.health_check.output_base64sha256

  role    = aws_iam_role.health_check_lambda.arn
  handler = "handler.lambda_handler"
  runtime = "python3.12"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      INCIDENT_QUEUE_URL = aws_sqs_queue.incident_queue.url
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.health_check_basic_execution,
    aws_iam_role_policy.health_check_queue_access
  ]

  tags = {
    Purpose = "Generates scheduled synthetic health-check events"
  }
}

output "health_check_lambda_name" {
  value = aws_lambda_function.health_check.function_name
}

output "health_check_lambda_arn" {
  value = aws_lambda_function.health_check.arn
}
