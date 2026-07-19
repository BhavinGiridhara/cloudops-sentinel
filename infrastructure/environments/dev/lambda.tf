resource "aws_lambda_function" "ingestion" {
  function_name = "cloudops-sentinel-dev-ingestion"

  filename         = "${path.module}/../../../services/ingestion/ingestion.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../services/ingestion/ingestion.zip")

  role    = aws_iam_role.lambda_execution_role.arn
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
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_data_access
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

  filename         = "${path.module}/../../../services/detection/detection.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../services/detection/detection.zip")

  role    = aws_iam_role.lambda_execution_role.arn
  handler = "handler.lambda_handler"
  runtime = "python3.12"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      INCIDENT_TABLE_NAME = aws_dynamodb_table.incidents.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_data_access
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