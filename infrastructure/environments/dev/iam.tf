resource "aws_iam_role" "lambda_execution_role" {
  name = "cloudops-sentinel-dev-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Purpose = "Lambda execution role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_data_access" {
  name = "cloudops-sentinel-dev-lambda-data-access"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "IncidentQueueAccess"
        Effect = "Allow"

        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]

        Resource = aws_sqs_queue.incident_queue.arn
      },
      {
        Sid    = "IncidentTableAccess"
        Effect = "Allow"

        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]

        Resource = aws_dynamodb_table.incidents.arn
      },
      {
        Sid    = "IncidentAlertPublish"
        Effect = "Allow"

        Action = [
          "sns:Publish"
        ]

        Resource = aws_sns_topic.incident_alerts.arn
      }
    ]
  })
}

output "lambda_execution_role_arn" {
  value = aws_iam_role.lambda_execution_role.arn
}