resource "aws_apigatewayv2_api" "incident_api" {
  name          = "cloudops-sentinel-dev-api"
  protocol_type = "HTTP"

  tags = {
    Project     = "cloudops-sentinel"
    Environment = "dev"
  }
}

resource "aws_apigatewayv2_integration" "ingestion" {
  api_id                 = aws_apigatewayv2_api.incident_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ingestion.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_incident" {
  api_id    = aws_apigatewayv2_api.incident_api.id
  route_key = "POST /incidents"
  target    = "integrations/${aws_apigatewayv2_integration.ingestion.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.incident_api.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Project     = "cloudops-sentinel"
    Environment = "dev"
  }
}

resource "aws_lambda_permission" "allow_api_gateway_ingestion" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.incident_api.execution_arn}/*/*"
}

output "incident_api_endpoint" {
  description = "Base URL for the CloudOps Sentinel HTTP API"
  value       = aws_apigatewayv2_api.incident_api.api_endpoint
}

output "create_incident_endpoint" {
  description = "POST endpoint for creating incidents"
  value       = "${aws_apigatewayv2_api.incident_api.api_endpoint}/incidents"
}