# API Contract: Cross-Domain Reasoning API

## Overview
This contract defines the interface for the cross-domain reasoning functionality that enables Claude to reason across personal and business domains.

## Endpoints

### POST /analyze-cross-domain
Analyzes information across personal and business domains and correlates relevant information.

#### Request
```json
{
  "personal_data": {
    "communications": [],
    "personal_tasks": [],
    "other_personal_info": {}
  },
  "business_data": {
    "business_tasks": [],
    "business_goals": [],
    "financial_logs": [],
    "other_business_info": {}
  },
  "correlation_rules": ["rule1", "rule2"],
  "safety_boundaries": ["boundary1", "boundary2"]
}
```

#### Response
```json
{
  "analysis_results": {
    "cross_domain_insights": [],
    "relevant_correlations": [],
    "potential_conflicts": [],
    "action_recommendations": []
  },
  "safety_compliance": {
    "boundaries_respected": true,
    "permissions_validated": true
  },
  "processing_metadata": {
    "timestamp": "ISO-8601-timestamp",
    "processing_duration_ms": 123
  }
}
```

#### Headers
- Content-Type: application/json
- Authorization: Bearer [token]

### POST /trigger-weekly-audit
Triggers the weekly business audit process.

#### Request
```json
{
  "audit_period_start": "YYYY-MM-DD",
  "audit_period_end": "YYYY-MM-DD",
  "business_goals_reference": "goal-reference-id"
}
```

#### Response
```json
{
  "audit_report_id": "report-uuid",
  "status": "completed|in_progress|failed",
  "report_location": "/phase-3/audits/report-uuid.md",
  "metrics_analyzed": {
    "tasks_completed": 123,
    "transactions_processed": 456,
    "anomalies_detected": 2
  }
}
```

### POST /generate-ceo-briefing
Generates the Monday morning CEO briefing.

#### Request
```json
{
  "briefing_date": "YYYY-MM-DD",
  "executive_level": "c_suite|senior_management",
  "reporting_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  }
}
```

#### Response
```json
{
  "briefing_id": "briefing-uuid",
  "status": "completed|in_progress|failed",
  "briefing_location": "/phase-3/briefings/briefing-uuid.md",
  "sections_generated": [
    "executive_summary",
    "revenue_overview",
    "completed_tasks",
    "bottlenecks",
    "recommendations"
  ]
}
```

## Logging Contract

### Audit Log Entry Format
All actions must generate log entries in the following format:

```json
{
  "log_id": "unique-log-identifier",
  "timestamp": "ISO-8601-timestamp",
  "action_type": "action-category",
  "target": "action-target",
  "approval_status": "approved|pending|rejected",
  "approver": "approver-identifier-or-null",
  "result": "success|failure|partial",
  "context_correlation": "cross-domain-context-id",
  "safety_boundary_checks": {
    "boundaries_respected": true,
    "permissions_validated": true
  }
}
```

## Error Handling Contract

### Error Response Format
All endpoints must return errors in the following format:

```json
{
  "error": {
    "type": "transient|authentication|logic|data|system",
    "code": "error-code",
    "message": "Human-readable error message",
    "details": {},
    "recovery_suggestion": "Suggested recovery approach"
  }
}
```

## Authentication
All requests must include a valid authorization token in the header.

## Rate Limits
- 100 requests per minute per token for analysis endpoints
- 10 requests per hour for audit generation endpoints
- 5 requests per day for CEO briefing generation endpoints