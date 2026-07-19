resource "aws_sns_topic" "incident_alerts" {
  name = "cloudops-sentinel-dev-incident-alerts"

  tags = {
    Purpose = "High-severity incident notifications"
  }
}

output "incident_alerts_topic_arn" {
  value = aws_sns_topic.incident_alerts.arn
}