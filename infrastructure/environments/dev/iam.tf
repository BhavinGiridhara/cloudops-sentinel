locals {
  lambda_assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "ingestion_lambda" {
  name               = "cloudops-sentinel-dev-ingestion-role"
  assume_role_policy = local.lambda_assume_role_policy

  tags = {
    Purpose = "Ingestion Lambda execution role"
  }
}

resource "aws_iam_role" "detection_lambda" {
  name               = "cloudops-sentinel-dev-detection-role"
  assume_role_policy = local.lambda_assume_role_policy

  tags = {
    Purpose = "Detection Lambda execution role"
  }
}

resource "aws_iam_role" "health_check_lambda" {
  name               = "cloudops-sentinel-dev-health-check-role"
  assume_role_policy = local.lambda_assume_role_policy

  tags = {
    Purpose = "Health-check Lambda execution role"
  }
}

resource "aws_iam_role_policy_attachment" "ingestion_basic_execution" {
  role       = aws_iam_role.ingestion_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "detection_basic_execution" {
  role       = aws_iam_role.detection_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "health_check_basic_execution" {
  role       = aws_iam_role.health_check_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "ingestion_queue_access" {
  name = "cloudops-sentinel-dev-ingestion-queue-access"
  role = aws_iam_role.ingestion_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.incident_queue.arn
    }]
  })
}

resource "aws_iam_role_policy" "health_check_queue_access" {
  name = "cloudops-sentinel-dev-health-check-queue-access"
  role = aws_iam_role.health_check_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.incident_queue.arn
    }]
  })
}

resource "aws_iam_role_policy" "detection_data_access" {
  name = "cloudops-sentinel-dev-detection-data-access"
  role = aws_iam_role.detection_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ConsumeIncidentQueue"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.incident_queue.arn
      },
      {
        Sid      = "StoreIncident"
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.incidents.arn
      },
      {
        Sid      = "PublishIncidentAlert"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.incident_alerts.arn
      }
    ]
  })
}

output "lambda_execution_role_arns" {
  value = {
    ingestion    = aws_iam_role.ingestion_lambda.arn
    detection    = aws_iam_role.detection_lambda.arn
    health_check = aws_iam_role.health_check_lambda.arn
  }
}
