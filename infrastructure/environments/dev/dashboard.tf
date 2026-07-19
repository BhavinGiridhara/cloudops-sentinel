resource "aws_cloudwatch_dashboard" "cloudops_dashboard" {
  dashboard_name = "cloudops-sentinel-dev"

  dashboard_body = jsonencode({
    widgets = [

      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          title = "Lambda Invocations"

          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.ingestion.function_name],
            [".", "Invocations", "FunctionName", aws_lambda_function.detection.function_name],
            [".", "Invocations", "FunctionName", aws_lambda_function.health_check.function_name]
          ]

          period = 300
          stat   = "Sum"
          region = "us-east-1"
        }
      },

      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          title = "Lambda Errors"

          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.ingestion.function_name],
            [".", "Errors", "FunctionName", aws_lambda_function.detection.function_name],
            [".", "Errors", "FunctionName", aws_lambda_function.health_check.function_name]
          ]

          period = 300
          stat   = "Sum"
          region = "us-east-1"
        }
      },

      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          title = "SQS Queue Depth"

          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.incident_queue.name]
          ]

          stat   = "Average"
          period = 300
          region = "us-east-1"
        }
      },

      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          title = "SNS Notifications"

          metrics = [
            ["AWS/SNS", "NumberOfMessagesPublished", "TopicName", aws_sns_topic.incident_alerts.name]
          ]

          stat   = "Sum"
          period = 300
          region = "us-east-1"
        }
      }
    ]
  })
}