# Personal AI Employee - Platinum Tier

Production-ready 24/7 deployment for autonomous AI employee operations.

## Overview

The Platinum tier provides enterprise-grade infrastructure for running the Personal AI Employee 24/7 in production environments. This includes:

- Containerized deployment with Docker
- Kubernetes orchestration
- Health monitoring and alerting
- Process supervision and auto-restart
- Metrics collection and monitoring
- CI/CD pipeline for automated deployment
- Production security and resource management

## Architecture

```
┌─────────────────────────────────────┐
│        Platinum Tier Layer          │
├─────────────────────────────────────┤
│  Health Checks & Monitoring         │
│  Process Supervision & Management   │
│  Metrics Collection & Alerting      │
│  Auto-scaling & Recovery            │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│         Gold Tier Services          │
│  (Cross-domain reasoning, MCP, etc) │
└─────────────────────────────────────┘
```

## Components

### 1. Process Supervisor (`process_supervisor.py`)
- Manages all long-running processes
- Auto-restarts failed processes
- Health monitoring and alerts
- Resource management

### 2. Health Checks (`health_checks.py`)
- Kubernetes liveness/readiness probes
- System resource monitoring
- Service availability checks
- Metrics endpoint for Prometheus

### 3. Monitoring System (`monitoring.py`)
- Metrics collection (Prometheus format)
- Alert management and notifications
- Email and Slack notifications
- Dashboard data aggregation

### 4. Configuration (`config.py`)
- Production-ready configuration
- Environment variable management
- Security settings
- Resource limits and timeouts

## Deployment

### Local Development
```bash
# Build and run locally
docker-compose up --build

# Access the application
curl http://localhost:8080/health
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f phase-4/kubernetes/

# Check deployment status
kubectl get pods -n ai-employee
kubectl get services -n ai-employee
```

### Production Deployment
```bash
# Set up systemd service (Linux)
sudo cp phase-4/systemd/ai-employee.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
```

## Environment Variables

Required for production deployment:

```bash
# Claude AI Configuration
ANTHROPIC_API_KEY=your_claude_api_key

# Gmail Configuration (optional)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/aiemployee

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Notification Configuration
SMTP_HOST=smtp.yourcompany.com
SMTP_USER=alerts@yourcompany.com
SMTP_PASSWORD=your_smtp_password
NOTIFICATION_EMAIL_TO=admin@yourcompany.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# MCP Server Ports
MCP_COMMUNICATION_PORT=8000
MCP_BROWSER_PORT=8001
MCP_SCHEDULING_PORT=8002

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Monitoring and Operations

### Health Endpoints
- `GET /health` - Overall system health
- `GET /ready` - Kubernetes readiness probe
- `GET /live` - Kubernetes liveness probe
- `GET /metrics` - Prometheus metrics
- `GET /status` - Detailed system status
- `GET /dashboard` - Operations dashboard

### Alerts
The system generates alerts for:
- Process failures and restarts
- High resource usage (CPU, memory, disk)
- Service unavailability
- Database and Redis connectivity issues
- MCP server failures

### Logs
Logs are structured in JSON format for easy parsing and analysis:
- Application logs: `logs/platinum.log`
- Process-specific logs: `logs/{process}.log`
- Error logs: `logs/{process}_error.log`

## Security

- HTTPS enforced in production
- Rate limiting for API endpoints
- Secure credential management
- Process isolation
- Network security policies (Kubernetes)
- Regular security scanning in CI/CD

## Scaling

The system supports horizontal scaling:
- MCP servers can be scaled independently
- Watcher processes are distributed
- Database connection pooling
- Redis for shared state
- Kubernetes HPA for auto-scaling

## Disaster Recovery

- Process auto-restart on failure
- Health-based service discovery
- Graceful degradation of features
- Alerting for critical failures
- Backup and restore procedures

## Development

For local development of Platinum tier components:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with development configuration
ENVIRONMENT=development python -m phase_4.main

# Run process supervisor separately
ENVIRONMENT=development python -m phase_4.process_supervisor --supervisor
```

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run health checks
curl http://localhost:8080/health
```

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/deploy.yml`) handles:
- Automated testing
- Docker image building
- Multi-platform builds
- Kubernetes deployment
- Health verification post-deployment