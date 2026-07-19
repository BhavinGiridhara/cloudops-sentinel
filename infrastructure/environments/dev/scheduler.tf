resource "aws_cloudwatch_event_rule" "health_check_schedule" {
  name                = "cloudops-sentinel-dev-health-check"
  description         = "Runs the synthetic health-check Lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "health_check_target" {
  rule = aws_cloudwatch_event_rule.health_check_schedule.name
  arn  = aws_lambda_function.health_check.arn
}

resource "aws_lambda_permission" "allow_eventbridge_health_check" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.health_check_schedule.arn
}

output "health_check_schedule_name" {
  value = aws_cloudwatch_event_rule.health_check_schedule.name
}