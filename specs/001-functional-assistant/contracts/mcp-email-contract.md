# API Contract: MCP Server for Email Actions

## Overview
This contract defines the interface for the MCP server that handles email actions in the Personal AI Employee system.

## Endpoints

### POST /send-email
Initiates sending an email through the MCP server.

#### Request
```json
{
  "to": "recipient@example.com",
  "subject": "Email subject",
  "body": "Email body content",
  "approval_id": "unique-approval-id"
}
```

#### Response
```json
{
  "status": "success|error",
  "message_id": "generated-message-id-if-success",
  "error": "error-details-if-applicable"
}
```

#### Headers
- Content-Type: application/json
- Authorization: Bearer [token]

### GET /status/{approval_id}
Checks the status of a specific approval request.

#### Response
```json
{
  "approval_id": "unique-approval-id",
  "status": "pending|approved|rejected",
  "timestamp": "ISO-8601-timestamp"
}
```

## Authentication
All requests must include a valid authorization token in the header.

## Error Handling
- 400: Bad request (malformed request body)
- 401: Unauthorized (invalid or missing token)
- 403: Forbidden (insufficient permissions)
- 422: Unprocessable entity (business rule violation)
- 500: Internal server error

## Rate Limits
- 100 requests per minute per token
- 1000 emails per day per token