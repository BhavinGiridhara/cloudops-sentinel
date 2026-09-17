resource "aws_lambda_event_source_mapping" "incident_queue_to_detection" {
  event_source_arn = aws_sqs_queue.incident_queue.arn
  function_name    = aws_lambda_function.detection.arn

  batch_size                         = 10
  enabled                            = true
  function_response_types            = ["ReportBatchItemFailures"]
  maximum_batching_window_in_seconds = 1

  depends_on = [
    aws_iam_role_policy.detection_data_access
  ]
}
