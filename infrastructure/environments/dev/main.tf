resource "aws_dynamodb_table" "incidents" {
  name         = "cloudops-sentinel-dev-incidents"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "incident_id"
  range_key = "record_type"

  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Purpose = "Stores CloudOps Sentinel incidents"
  }
}