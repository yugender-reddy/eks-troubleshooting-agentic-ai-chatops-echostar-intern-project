#!/bin/bash

# Variables
NAMESPACE="interdependent-services"
SERVICE_A_DEPLOYMENT="service-a"
SERVICE_B_DEPLOYMENT="service-b"

# Step 1: Create a namespace for the workload
kubectl create namespace $NAMESPACE || echo "Namespace $NAMESPACE already exists"

# Step 2: Deploy Service B (Backend) with stress-ng to induce OOMKill
cat <<EOF | kubectl apply -n $NAMESPACE -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $SERVICE_B_DEPLOYMENT
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-b
  template:
    metadata:
      labels:
        app: service-b
    spec:
      containers:
      - name: service-b
        image: polinux/stress-ng  # Use stress-ng to stress memory
        command: ['stress-ng', '--vm', '1', '--vm-bytes', '120M', '--timeout', '600s']  # Allocate 120MB of memory
        resources:
          limits:
            memory: "128Mi"  # Set memory limit to force OOMKill
            cpu: "500m"
          requests:
            memory: "64Mi"
            cpu: "250m"
        ports:
        - containerPort: 80
EOF

# Step 3: Deploy Service A (Frontend making requests to Service B)
cat <<EOF | kubectl apply -n $NAMESPACE -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $SERVICE_A_DEPLOYMENT
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-a
  template:
    metadata:
      labels:
        app: service-a
    spec:
      containers:
      - name: service-a
        image: busybox
        command: ['sh', '-c']
        args:
          - |
            while true; do
              wget -qO- http://service-b:80 || echo "Failed to reach Service B";
              sleep 5;
            done;
EOF

echo "Workload with interdependent services deployed."

# Step 4: Monitor the pod status
echo "Use 'kubectl get pods -n $NAMESPACE' to monitor the pod status and watch for the OOMKilled event."
