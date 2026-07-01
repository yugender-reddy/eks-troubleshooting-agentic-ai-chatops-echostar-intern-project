#!/bin/bash

# Build and Deploy Script for K8s Troubleshooting Agent

set -e

# Load all variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/export_env.sh"
load_env "${SCRIPT_DIR}/.env"

# Validate required variables are set
required_vars=(ECR_REGISTRY IMAGE_NAME IMAGE_TAG CLUSTER_NAME NAMESPACE AWS_REGION SLACK_BOT_TOKEN SLACK_APP_TOKEN SLACK_SIGNING_SECRET)
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env"
        exit 1
    fi
done

echo "🚀 Building and deploying K8s Troubleshooting Agent..."

# 1. Build Docker image for AMD64 architecture
echo "📦 Building Docker image for AMD64..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Tag and push to ECR
echo "🏷️  Tagging and pushing to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin ${ECR_REGISTRY}
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# 3. Create namespace
echo "📁 Creating namespace..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 4. Install/upgrade Helm chart with comprehensive admin permissions
echo "⚙️  Installing Helm chart with comprehensive admin permissions..."
helm upgrade --install k8s-troubleshooting-agent ./helm/k8s-troubleshooting-agent \
  --namespace ${NAMESPACE} \
  --set image.repository=${ECR_REGISTRY}/${IMAGE_NAME} \
  --set image.tag=${IMAGE_TAG} \
  --set config.clusterName=${CLUSTER_NAME} \
  --set config.awsRegion=${AWS_REGION} \
  --set config.eksMcp.allowWrite=true \
  --set secrets.slack.botToken="${SLACK_BOT_TOKEN}" \
  --set secrets.slack.appToken="${SLACK_APP_TOKEN}" \
  --set secrets.slack.signingSecret="${SLACK_SIGNING_SECRET}" \
  --set-json 'rbac.rules=[
    {"apiGroups":[""],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["apps"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["extensions"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["batch"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["networking.k8s.io"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["rbac.authorization.k8s.io"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["apiextensions.k8s.io"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["metrics.k8s.io"],"resources":["*"],"verbs":["*"]},
    {"apiGroups":["*"],"resources":["*"],"verbs":["*"]},
    {"nonResourceURLs":["*"],"verbs":["*"]}
  ]' \
  --wait

echo "✅ Deployment complete!"
echo "📊 Check status with: kubectl get pods -n ${NAMESPACE}"
echo "📋 View logs with: kubectl logs -n ${NAMESPACE} -l app.kubernetes.io/name=k8s-troubleshooting-agent"