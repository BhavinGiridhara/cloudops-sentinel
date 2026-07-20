# CloudOps Sentinel

CloudOps Sentinel is a serverless AWS incident monitoring and alerting platform built with Terraform. It demonstrates an event-driven cloud architecture that ingests, processes, stores, monitors, and alerts on incidents using fully managed AWS services.

---

## Architecture

![CloudOps Sentinel Architecture](docs/architecture.png)

---

## Features

- REST API built with Amazon API Gateway
- Serverless incident processing using AWS Lambda
- Asynchronous event-driven architecture using Amazon SQS
- Incident storage using Amazon DynamoDB
- Email notifications for high and critical incidents using Amazon SNS
- Automated synthetic health checks using Amazon EventBridge
- CloudWatch dashboards for operational visibility
- CloudWatch alarms for automated monitoring
- Infrastructure managed entirely with Terraform
- Least-privilege IAM permissions

---

## Skills Demonstrated

- Infrastructure as Code (Terraform)
- Serverless Architecture
- Event-Driven Systems
- Cloud Monitoring & Alerting
- Infrastructure Automation
- IAM Least-Privilege Design
- Asynchronous Messaging
- Cloud Operations

---

## AWS Services Used

- Amazon API Gateway
- AWS Lambda
- Amazon SQS
- Amazon DynamoDB
- Amazon SNS
- Amazon EventBridge
- Amazon CloudWatch
- AWS IAM
- Terraform

---

## Architecture Flow

1. Client sends an incident to Amazon API Gateway.
2. API Gateway invokes the Ingestion Lambda.
3. Ingestion Lambda validates the request and publishes the incident to Amazon SQS.
4. Detection Lambda consumes the SQS message.
5. Detection Lambda stores the incident in Amazon DynamoDB.
6. High and Critical incidents are published to Amazon SNS.
7. Amazon SNS sends email notifications.
8. Amazon EventBridge runs a Health Check Lambda every five minutes to generate synthetic incidents.
9. CloudWatch dashboards and alarms continuously monitor the platform.

---

## Example Request

```bash
curl -X POST \
https://5wzgi9qewd.execute-api.us-east-1.amazonaws.com/incidents \
-H "Content-Type: application/json" \
-d '{
  "service":"checkout-api",
  "incident_type":"HighLatency",
  "severity":"HIGH",
  "message":"Checkout latency exceeded threshold"
}'
```

---

## Example Response

```json
{
  "message": "Incident accepted",
  "incident_id": "generated-incident-id",
  "sqs_message_id": "generated-message-id"
}
```

---

## Monitoring

CloudOps Sentinel uses Amazon CloudWatch to monitor:

- API Gateway requests and errors
- Lambda invocations and failures
- SQS queue depth
- SNS notification activity

CloudWatch alarms notify operators when:

- Lambda Errors > 0
- API Gateway 5XX Errors > 0
- SQS Queue Depth > 10

### CloudWatch Dashboard

![CloudWatch Dashboard](docs/cloudwatch-dashboard.png)
---

## Project Structure

```text
cloudops-sentinel/
│
├── docs/
│   ├── architecture.png
│   └── screenshots/
│       └── cloudwatch-dashboard.png
│
├── infrastructure/
│   └── environments/
│       └── dev/
│
├── services/
│   ├── ingestion/
│   ├── detection/
│   ├── health_check/
│   ├── notification/
│   ├── remediation/
│   └── verification/
│
├── tests/
│
├── requirements.txt
│
└── README.md
```

---

## What I Learned

- Designing production-style serverless cloud architectures
- Building event-driven systems using Amazon SQS
- Deploying AWS infrastructure with Terraform
- Implementing monitoring and alerting using CloudWatch and SNS
- Applying least-privilege IAM permissions
- Creating scalable cloud applications using managed AWS services

---

## Future Improvements

- Add GitHub Actions CI/CD pipeline
- Add Dead Letter Queue (DLQ) support
- Implement API authentication and authorization
- Refactor Terraform into reusable modules
- Support multiple deployment environments (dev, staging, production)