resource "aws_cloudwatch_log_group" "ingestion" {
  name              = "/aws/lambda/${aws_lambda_function.ingestion.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "detection" {
  name              = "/aws/lambda/${aws_lambda_function.detection.function_name}"
  retention_in_days = 14
}