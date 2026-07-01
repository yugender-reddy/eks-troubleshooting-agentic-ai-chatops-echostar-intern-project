# K8s Troubleshooting Slack Agent

A Strands-based agent that monitors Slack conversations and provides Kubernetes troubleshooting assistance with EKS MCP server integration.

## Agent Workflow

1. **Message Detection**: User posts K8s-related message in Slack
2. **Orchestrator Agent Routes**: Checks memory first, then uses K8s specialist if needed
3. **Memory Agent**: Fast retrieval of stored solutions (using S3 Vectors DB)
4. **K8s Specialist**: Uses local tools + EKS MCP server for troubleshooting
5. **Response**: Formatted solution sent back to Slack

## Features

- **EKS MCP Integration**: Full cluster management and diagnostics
- **S3 Vectors Memory**: Fast similarity search for past troubleshooting solutions with 1024-dimensional embeddings
- **Direct Responses**: No back-and-forth, provides immediate actionable solutions
- **Thread Context**: Uses full conversation context for better understanding
- **Configurable Permissions**: Read-only or read-write EKS operations

## Prerequisites

### AWS Permissions Setup

Create an IAM role for Pod Identity with permissions for:
- EKS cluster access (describe, list operations)
- CloudWatch Logs (for Container Insights)
- CloudWatch Metrics
- Bedrock (for AI model access)

See `eks-mcp-policy.json` for the complete IAM policy template.


### EKS Cluster Access

The IAM role must be added to your EKS cluster's access entries:

```bash
# Add IAM role to EKS cluster access entries
aws eks create-access-entry \
  --cluster-name YOUR_CLUSTER_NAME \
  --principal-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE_NAME \
  --type STANDARD

# Associate with cluster admin policy
aws eks associate-access-policy \
  --cluster-name YOUR_CLUSTER_NAME \
  --principal-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE_NAME \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

### Pod Identity Setup

Configure EKS Pod Identity to associate the service account with the IAM role:

```bash
# Create Pod Identity association
aws eks create-pod-identity-association \
  --cluster-name YOUR_CLUSTER_NAME \
  --namespace k8s-troubleshooting \
  --service-account k8s-troubleshooting-agent \
  --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE_NAME
```

## Quick Start

### 1. Setup Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Slack
- Create Slack app with Socket Mode enabled
- Add required scopes and event subscriptions
- Get tokens and add to `.env`

### 4. Update Deployment Script
Edit `build-and-deploy.sh` and update:
- `ECR_REGISTRY` - Your ECR registry URL
- `CLUSTER_NAME` - Your EKS cluster name
- Region settings

### 5. Deploy Agent

**Option A: Using the deployment script**
```bash
# Set Slack credentials as environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_APP_TOKEN="xapp-your-token"
export SLACK_SIGNING_SECRET="your-secret"

# Run deployment script
./build-and-deploy.sh
```

**Option B: Using Helm directly**
```bash
# Install/upgrade with Helm
helm upgrade --install k8s-troubleshooting-agent ./helm/k8s-troubleshooting-agent \
  --namespace k8s-troubleshooting \
  --create-namespace \
  --set image.repository=YOUR_ECR_REGISTRY/k8s-troubleshooting-agent \
  --set image.tag=latest \
  --set config.clusterName=YOUR_CLUSTER_NAME \
  --set config.eksMcp.allowWrite=true \
  --set secrets.slack.botToken="xoxb-your-token" \
  --set secrets.slack.appToken="xapp-your-token" \
  --set secrets.slack.signingSecret="your-secret"
```

## Configuration

### Required Settings
```bash
# Cluster
CLUSTER_NAME=your-eks-cluster

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
SLACK_SIGNING_SECRET=your-secret

# AWS
AWS_REGION=us-west-2

# EKS MCP (optional)
ENABLE_EKS_MCP=true
EKS_MCP_ALLOW_WRITE=false  # Set to true for write operations
```

## EKS MCP Tools

### Read-Only Tools (default):
- `list_k8s_resources` - List pods, services, deployments
- `get_pod_logs` - Retrieve pod logs for debugging
- `get_k8s_events` - Get cluster events
- `get_cloudwatch_metrics` - Monitor resource usage
- `search_eks_troubleshoot_guide` - Built-in troubleshooting knowledge

### Write Tools (when `EKS_MCP_ALLOW_WRITE=true`):
- `manage_k8s_resource` - Create, update, delete resources
- `apply_yaml` - Deploy applications
- `manage_eks_stacks` - CloudFormation stack operations
- `generate_app_manifest` - Generate deployment manifests

## Demo

Try the multi-tier application demo:

```bash
# Deploy broken application
kubectl apply -f demo/multi-tier-app.yaml

# Check status
kubectl get pods -n demo-app

# Ask agent to troubleshoot
# "Check the status of pods in the demo-app namespace"
```

The demo includes realistic issues:
- ImagePullBackOff (monitoring agent)
- CrashLoopBackOff (backend Redis connection)
- Service connectivity (wrong nginx port)
- Resource limits (OOMKilled)

## Usage Examples

### Basic Troubleshooting
```
User: "My pod frontend-abc123 is in CrashLoopBackOff"
Agent: [Uses get_pod_logs and describes the issue with solution]
```

### Memory-Based Responses
```
User: "Pod keeps getting OOMKilled"
Agent: [Checks FAISS vector DB for similar issues, provides cached solution]
```

### Force Fresh Analysis
```
User: "Why is my pod pending? force troubleshoot"
Agent: [Bypasses memory, uses K8s specialist for fresh analysis]
```

## Project Structure

```
├── main.py                     # Entry point
├── src/
│   ├── slack_handler.py       # Slack event handling
│   ├── agents/
│   │   ├── agent_orchestrator.py  # Routes between memory and K8s specialist
│   │   ├── memory_agent.py        # FAISS vector DB operations
│   │   └── k8s_specialist.py      # K8s troubleshooting with EKS MCP
│   ├── config/settings.py     # Configuration
│   └── tools/k8s_tools.py     # Local Kubernetes tools
├── helm/k8s-troubleshooting-agent/  # Helm chart for deployment
├── demo/                       # Multi-tier demo application
└── eks-mcp-policy.json        # IAM policy template
```

## Requirements

- Python 3.8+
- Slack workspace with bot permissions
- Kubernetes cluster access
- AWS credentials (for EKS MCP)
- `uvx` package manager (for EKS MCP server)
- S3 Vectors for vector similarity search

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure Pod Identity is properly configured and IAM role has required permissions
2. **EKS MCP Connection Issues**: Verify cluster access entries and kubeconfig generation
3. **Bedrock Access Denied**: Check that IAM role has bedrock permissions for all required regions

### Logs

Check agent logs:
```bash
kubectl logs -n k8s-troubleshooting -l app.kubernetes.io/name=k8s-troubleshooting-agent -f
```

## License

MIT License