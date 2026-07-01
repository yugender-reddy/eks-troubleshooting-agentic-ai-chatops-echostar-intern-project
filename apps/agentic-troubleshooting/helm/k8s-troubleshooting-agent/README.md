# K8s Troubleshooting Agent Helm Chart

This Helm chart deploys the K8s Troubleshooting Agent to your EKS cluster.

## Prerequisites

- EKS cluster with Pod Identity configured
- IAM role with required permissions (see main README)
- Slack app credentials

## Installation

```bash
helm upgrade --install k8s-troubleshooting-agent . \
  --namespace k8s-troubleshooting \
  --create-namespace \
  --set image.repository=YOUR_ECR_REGISTRY/k8s-troubleshooting-agent \
  --set image.tag=latest \
  --set config.clusterName=YOUR_CLUSTER_NAME \
  --set secrets.slack.botToken="xoxb-your-token" \
  --set secrets.slack.appToken="xapp-your-token" \
  --set secrets.slack.signingSecret="your-secret"
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `""` |
| `image.tag` | Container image tag | `"latest"` |
| `config.clusterName` | EKS cluster name | `""` |
| `config.awsRegion` | AWS region | `"us-west-2"` |
| `config.eksMcp.enabled` | Enable EKS MCP server | `true` |
| `config.eksMcp.allowWrite` | Allow write operations | `false` |
| `secrets.slack.botToken` | Slack bot token | `""` |
| `secrets.slack.appToken` | Slack app token | `""` |
| `secrets.slack.signingSecret` | Slack signing secret | `""` |

## Uninstall

```bash
helm uninstall k8s-troubleshooting-agent -n k8s-troubleshooting
```