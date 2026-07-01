# Multi-Tier Application Troubleshooting Demo

## Demo Overview
This demo showcases the EKS MCP agent troubleshooting a realistic 3-tier application with multiple issues:

**Architecture:**
- **Frontend**: Nginx serving React app
- **Backend**: Node.js API with Redis connection  
- **Database**: Redis cache
- **Monitoring**: Fake monitoring agent

## Pre-Demo Setup

### Deploy the Broken Application:
```bash
kubectl apply -f demo/multi-tier-app.yaml
```

### Verify Issues Are Present:
```bash
kubectl get pods -n demo-app
# Should show: ImagePullBackOff, CrashLoopBackOff, etc.
```

## Demo Flow - Agent Troubleshooting

### 1. **Initial Assessment**
```
User: "Check the status of pods in the demo-app namespace"

Expected Agent Actions:
- Uses list_k8s_resources to show pod statuses
- Identifies multiple failing pods
- Provides overview of issues found
```

### 2. **Fix ImagePullBackOff Issue**
```
User: "The monitoring-agent pod is failing, what's wrong?"

Expected Agent Actions:
- Uses get_k8s_events to see ImagePullBackOff error
- Identifies nonexistent image: nonexistent/monitoring:latest
- Uses manage_k8s_resource to update deployment with busybox:latest
- Verifies pod is now running
```

### 3. **Troubleshoot Backend Crashes**
```
User: "The backend-api pods keep crashing, investigate the issue"

Expected Agent Actions:
- Uses get_pod_logs to see Redis connection errors
- Identifies wrong service name: redis-wrong-service
- Uses manage_k8s_resource to fix deployment (redis-wrong-service → redis-service)
- Shows pods are now running but may still have memory issues
```

### 4. **Resolve Memory Issues**
```
User: "The backend is getting OOMKilled, fix the memory limits"

Expected Agent Actions:
- Uses get_cloudwatch_metrics to show memory usage
- Identifies insufficient memory limits (32Mi request, 64Mi limit)
- Uses manage_k8s_resource to increase memory (128Mi request, 256Mi limit)
- Confirms pods are stable
```

### 5. **Fix Service Connectivity**
```
User: "Test the frontend to backend connection"

Expected Agent Actions:
- Uses get_pod_logs from frontend to see proxy errors
- Identifies wrong port in nginx config (8080 instead of 3000)
- Uses manage_k8s_resource to update nginx-config ConfigMap
- Restarts frontend pods to pick up new config
```

### 6. **End-to-End Validation**
```
User: "Verify the entire application is working"

Expected Agent Actions:
- Uses list_k8s_resources to show all pods running
- Uses get_pod_logs to verify healthy API responses
- Confirms frontend can reach backend successfully
- Shows application is fully functional
```

## Issues Fixed by Agent

| Issue | Component | Problem | Agent Solution |
|-------|-----------|---------|----------------|
| ImagePullBackOff | monitoring-agent | nonexistent/monitoring:latest | Update to busybox:latest |
| CrashLoopBackOff | backend-api | Wrong Redis service name | Fix service name in deployment |
| OOMKilled | backend-api | Insufficient memory (32Mi/64Mi) | Increase to 128Mi/256Mi |
| Connection Error | frontend | Wrong backend port (8080) | Fix nginx config to use port 3000 |

## EKS MCP Tools Demonstrated

- **list_k8s_resources** - Monitor pod status across namespace
- **get_k8s_events** - Investigate cluster events and errors
- **get_pod_logs** - Debug application issues and crashes
- **manage_k8s_resource** - Fix deployments, services, and configs
- **get_cloudwatch_metrics** - Monitor resource usage and performance

## Expected Demo Outcome

- **Before**: 4 broken components with various failure modes
- **After**: Fully functional 3-tier application
- **Demonstrates**: Real-world troubleshooting skills and EKS MCP capabilities
- **Time**: ~10-15 minutes of interactive troubleshooting

## Quick Commands

**Deploy**: `kubectl apply -f demo/multi-tier-app.yaml`
**Check**: `kubectl get pods -n demo-app -w`
**Cleanup**: `kubectl delete namespace demo-app`