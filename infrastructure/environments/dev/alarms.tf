resource "aws_cloudwatch_metric_alarm" "detection_lambda_errors" {
  alarm_name          = "cloudops-sentinel-dev-detection-lambda-errors"
  alarm_description   = "Detection Lambda produced one or more errors."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  statistic   = "Sum"
  period      = 60

  dimensions = {
    FunctionName = aws_lambda_function.detection.function_name
  }

  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.incident_alerts.arn]
  ok_actions         = [aws_sns_topic.incident_alerts.arn]

  tags = {
    Purpose = "Detect failures in the incident-processing Lambda"
  }
}

resource "aws_cloudwatch_metric_alarm" "ingestion_lambda_errors" {
  alarm_name          = "cloudops-sentinel-dev-ingestion-lambda-errors"
  alarm_description   = "Ingestion Lambda produced one or more errors."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  statistic   = "Sum"
  period      = 60

  dimensions = {
    FunctionName = aws_lambda_function.ingestion.function_name
  }

  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.incident_alerts.arn]
  ok_actions         = [aws_sns_topic.incident_alerts.arn]

  tags = {
    Purpose = "Detect failures in the incident-ingestion Lambda"
  }
}

resource "aws_cloudwatch_metric_alarm" "sqs_queue_backlog" {
  alarm_name          = "cloudops-sentinel-dev-sqs-queue-backlog"
  alarm_description   = "Incident messages are accumulating in the SQS queue."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  threshold           = 10

  namespace   = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  statistic   = "Average"
  period      = 60

  dimensions = {
    QueueName = aws_sqs_queue.incident_queue.name
  }

  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.incident_alerts.arn]
  ok_actions         = [aws_sns_topic.incident_alerts.arn]

  tags = {
    Purpose = "Detect a growing incident-processing backlog"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx_errors" {
  alarm_name          = "cloudops-sentinel-dev-api-gateway-5xx-errors"
  alarm_description   = "The incident API returned one or more server errors."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1

  namespace   = "AWS/ApiGateway"
  metric_name = "5xx"
  statistic   = "Sum"
  period      = 60

  dimensions = {
    ApiId = aws_apigatewayv2_api.incident_api.id
    Stage = aws_apigatewayv2_stage.default.name
  }

  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.incident_alerts.arn]
  ok_actions         = [aws_sns_topic.incident_alerts.arn]

  tags = {
    Purpose = "Detect server errors from the public incident API"
  }
}