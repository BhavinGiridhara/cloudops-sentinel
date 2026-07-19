output "incident_table_name" {
  description = "Name of the DynamoDB table used to store incidents"
  value       = aws_dynamodb_table.incidents.name
}

output "incident_table_arn" {
  description = "ARN of the DynamoDB table used to store incidents"
  value       = aws_dynamodb_table.incidents.arn
}