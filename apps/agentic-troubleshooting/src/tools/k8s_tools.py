"""Kubernetes diagnostic tools — GET/LIST operations only.

Safety design:
- Every tool here only calls Kubernetes GET/LIST endpoints
- No write, patch, delete, or exec operations are present in this file
"""

import logging
from typing import Optional
from kubernetes import client, config
from strands import tool

logger = logging.getLogger(__name__)

# ── Kubernetes client setup ───────────────────────────────────────────────────
try:
    config.load_incluster_config()
except Exception:
    try:
        config.load_kube_config()
    except Exception as e:
        logger.warning(f"Could not load Kubernetes config: {e}")

# ── Pod tools ─────────────────────────────────────────────────────────────────

@tool
def get_pods(namespace: Optional[str] = None) -> str:
    """List pods and their status (like kubectl get pods).

    Args:
        namespace: Kubernetes namespace. If empty, lists all namespaces.

    Returns:
        Formatted table of pods with status, ready count, and restarts.
    """
    try:
        v1 = client.CoreV1Api()

        if namespace:
            pods = v1.list_namespaced_pod(namespace=namespace)
            header = f"Pods in namespace '{namespace}':\n"
        else:
            pods = v1.list_pod_for_all_namespaces()
            header = "Pods across all namespaces:\n"

        output = header
        output += f"{'NAMESPACE':<20} {'NAME':<45} {'READY':<7} {'STATUS':<18} {'RESTARTS':<8}\n"
        output += "-" * 100 + "\n"

        for pod in pods.items:
            ready = 0
            total = 0
            restarts = 0

            if pod.status.container_statuses:
                total = len(pod.status.container_statuses)
                for cs in pod.status.container_statuses:
                    if cs.ready:
                        ready += 1
                    restarts += cs.restart_count

            output += (
                f"{pod.metadata.namespace:<20} "
                f"{pod.metadata.name:<45} "
                f"{ready}/{total:<5} "
                f"{pod.status.phase:<18} "
                f"{restarts:<8}\n"
            )

        output += f"\nTotal pods: {len(pods.items)}"
        return output
    except Exception as e:
        return f"Error getting pods: {e}"


@tool
def describe_pod(namespace: str, pod_name: str) -> str:
    """Get detailed information about a specific pod (like kubectl describe pod).

    Args:
        namespace: The Kubernetes namespace.
        pod_name: Name of the pod to describe.

    Returns:
        Pod details including containers, status, conditions, and recent events.
    """
    try:
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        output = f"Name: {pod.metadata.name}\n"
        output += f"Namespace: {pod.metadata.namespace}\n"
        output += f"Node: {pod.spec.node_name}\n"
        output += f"Status: {pod.status.phase}\n"
        output += f"IP: {pod.status.pod_ip}\n"
        output += f"Service Account: {pod.spec.service_account_name}\n\n"

        # Conditions
        if pod.status.conditions:
            output += "Conditions:\n"
            for cond in pod.status.conditions:
                output += f"  {cond.type}: {cond.status}"
                if cond.reason:
                    output += f" ({cond.reason})"
                output += "\n"
            output += "\n"

        # Containers
        output += "Containers:\n"
        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                output += f"  {cs.name}:\n"
                output += f"    Image: {cs.image}\n"
                output += f"    Ready: {cs.ready}\n"
                output += f"    Restarts: {cs.restart_count}\n"
                if cs.state.running:
                    output += f"    State: Running (since {cs.state.running.started_at})\n"
                elif cs.state.waiting:
                    output += f"    State: Waiting ({cs.state.waiting.reason})\n"
                    if cs.state.waiting.message:
                        output += f"    Message: {cs.state.waiting.message}\n"
                elif cs.state.terminated:
                    output += f"    State: Terminated ({cs.state.terminated.reason})\n"
                    output += f"    Exit Code: {cs.state.terminated.exit_code}\n"
                if cs.last_state and cs.last_state.terminated:
                    output += f"    Last State: Terminated ({cs.last_state.terminated.reason}, exit {cs.last_state.terminated.exit_code})\n"

        # Events
        events = v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )
        if events.items:
            output += "\nRecent Events:\n"
            for event in sorted(events.items, key=lambda e: e.last_timestamp or e.event_time or "", reverse=True)[:10]:
                output += f"  [{event.type}] {event.reason}: {event.message}\n"

        return output
    except Exception as e:
        return f"Error describing pod: {e}"


@tool
def get_pod_logs(namespace: str, pod_name: str, container: Optional[str] = None, tail_lines: int = 100, previous: bool = False) -> str:
    """Get logs from a pod's container (like kubectl logs).

    Args:
        namespace: The Kubernetes namespace.
        pod_name: Name of the pod.
        container: Specific container name (optional, uses first container if omitted).
        tail_lines: Number of lines from the end to return (default 100).
        previous: If True, get logs from the previous terminated container (for CrashLoopBackOff).

    Returns:
        Container log output.
    """
    try:
        v1 = client.CoreV1Api()
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
            previous=previous,
        )
        if not logs:
            return f"No logs found for pod '{pod_name}'" + (" (previous container)" if previous else "")
        return f"Logs for {pod_name}" + (f"/{container}" if container else "") + f" (last {tail_lines} lines):\n\n{logs}"
    except Exception as e:
        return f"Error getting logs: {e}"


# ── Events ────────────────────────────────────────────────────────────────────

@tool
def get_events(namespace: Optional[str] = None, event_type: Optional[str] = None) -> str:
    """Get cluster events (like kubectl get events).

    Args:
        namespace: Namespace to filter by (optional, all namespaces if omitted).
        event_type: Filter by type: 'Warning' or 'Normal' (optional).

    Returns:
        Recent events with type, reason, object, and message.
    """
    try:
        v1 = client.CoreV1Api()

        if namespace:
            events = v1.list_namespaced_event(namespace=namespace)
        else:
            events = v1.list_event_for_all_namespaces()

        items = events.items
        if event_type:
            items = [e for e in items if e.type and e.type.lower() == event_type.lower()]

        # Sort by last seen
        items.sort(key=lambda e: e.last_timestamp or e.event_time or "", reverse=True)
        items = items[:30]

        if not items:
            return "No events found."

        output = f"{'TYPE':<9} {'NAMESPACE':<18} {'REASON':<22} {'OBJECT':<40} {'MESSAGE'}\n"
        output += "-" * 120 + "\n"

        for e in items:
            obj = f"{e.involved_object.kind}/{e.involved_object.name}"
            msg = (e.message or "")[:80]
            output += f"{e.type:<9} {e.involved_object.namespace or '-':<18} {e.reason:<22} {obj:<40} {msg}\n"

        return output
    except Exception as e:
        return f"Error getting events: {e}"


# ── Deployments & ReplicaSets ─────────────────────────────────────────────────

@tool
def get_deployments(namespace: Optional[str] = None) -> str:
    """List deployments and their status (like kubectl get deployments).

    Args:
        namespace: Namespace to filter by (optional).

    Returns:
        Deployment list with ready/desired replicas.
    """
    try:
        apps_v1 = client.AppsV1Api()

        if namespace:
            deps = apps_v1.list_namespaced_deployment(namespace=namespace)
        else:
            deps = apps_v1.list_deployment_for_all_namespaces()

        output = f"{'NAMESPACE':<20} {'NAME':<40} {'READY':<10} {'UP-TO-DATE':<12} {'AVAILABLE':<10}\n"
        output += "-" * 95 + "\n"

        for d in deps.items:
            ready = d.status.ready_replicas or 0
            desired = d.spec.replicas or 0
            updated = d.status.updated_replicas or 0
            available = d.status.available_replicas or 0
            output += (
                f"{d.metadata.namespace:<20} "
                f"{d.metadata.name:<40} "
                f"{ready}/{desired:<8} "
                f"{updated:<12} "
                f"{available:<10}\n"
            )

        return output
    except Exception as e:
        return f"Error getting deployments: {e}"


@tool
def describe_deployment(namespace: str, deployment_name: str) -> str:
    """Get detailed information about a deployment.

    Args:
        namespace: The Kubernetes namespace.
        deployment_name: Name of the deployment.

    Returns:
        Deployment details including strategy, conditions, and replica status.
    """
    try:
        apps_v1 = client.AppsV1Api()
        dep = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        output = f"Name: {dep.metadata.name}\n"
        output += f"Namespace: {dep.metadata.namespace}\n"
        output += f"Replicas: {dep.status.ready_replicas or 0}/{dep.spec.replicas} ready\n"
        output += f"Strategy: {dep.spec.strategy.type}\n"

        # Conditions
        if dep.status.conditions:
            output += "\nConditions:\n"
            for cond in dep.status.conditions:
                output += f"  {cond.type}: {cond.status} — {cond.message}\n"

        # Container specs
        output += "\nContainers:\n"
        for container in dep.spec.template.spec.containers:
            output += f"  {container.name}:\n"
            output += f"    Image: {container.image}\n"
            if container.resources:
                if container.resources.requests:
                    output += f"    Requests: {dict(container.resources.requests)}\n"
                if container.resources.limits:
                    output += f"    Limits: {dict(container.resources.limits)}\n"

        return output
    except Exception as e:
        return f"Error describing deployment: {e}"


# ── Services ──────────────────────────────────────────────────────────────────

@tool
def get_services(namespace: Optional[str] = None) -> str:
    """List services (like kubectl get svc).

    Args:
        namespace: Namespace to filter by (optional).

    Returns:
        Services with type, cluster IP, and ports.
    """
    try:
        v1 = client.CoreV1Api()

        if namespace:
            svcs = v1.list_namespaced_service(namespace=namespace)
        else:
            svcs = v1.list_service_for_all_namespaces()

        output = f"{'NAMESPACE':<20} {'NAME':<35} {'TYPE':<14} {'CLUSTER-IP':<18} {'PORTS'}\n"
        output += "-" * 110 + "\n"

        for svc in svcs.items:
            ports = ", ".join(
                f"{p.port}/{p.protocol}" + (f"→{p.target_port}" if p.target_port else "")
                for p in (svc.spec.ports or [])
            )
            output += (
                f"{svc.metadata.namespace:<20} "
                f"{svc.metadata.name:<35} "
                f"{svc.spec.type:<14} "
                f"{svc.spec.cluster_ip or '-':<18} "
                f"{ports}\n"
            )

        return output
    except Exception as e:
        return f"Error getting services: {e}"


# ── Nodes ─────────────────────────────────────────────────────────────────────

@tool
def get_nodes() -> str:
    """List cluster nodes with status and resource capacity (like kubectl get nodes).

    Returns:
        Node list with status, roles, CPU, and memory capacity.
    """
    try:
        v1 = client.CoreV1Api()
        nodes = v1.list_node()

        output = f"{'NAME':<40} {'STATUS':<12} {'ROLES':<18} {'CPU':<6} {'MEMORY':<12} {'VERSION'}\n"
        output += "-" * 110 + "\n"

        for node in nodes.items:
            # Status
            status = "Unknown"
            for cond in (node.status.conditions or []):
                if cond.type == "Ready":
                    status = "Ready" if cond.status == "True" else "NotReady"

            # Roles
            roles = [
                k.replace("node-role.kubernetes.io/", "")
                for k in (node.metadata.labels or {})
                if k.startswith("node-role.kubernetes.io/")
            ] or ["<none>"]

            cap = node.status.capacity or {}
            output += (
                f"{node.metadata.name:<40} "
                f"{status:<12} "
                f"{','.join(roles):<18} "
                f"{cap.get('cpu', '?'):<6} "
                f"{cap.get('memory', '?'):<12} "
                f"{node.status.node_info.kubelet_version if node.status.node_info else '?'}\n"
            )

        return output
    except Exception as e:
        return f"Error getting nodes: {e}"


@tool
def get_node_resource_usage(node_name: str) -> str:
    """Get allocated resources on a specific node (pods scheduled on it).

    Args:
        node_name: Name of the node.

    Returns:
        Summary of resource requests/limits for pods on that node.
    """
    try:
        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")

        total_cpu_req = 0
        total_mem_req = 0
        total_cpu_lim = 0
        total_mem_lim = 0

        for pod in pods.items:
            for container in pod.spec.containers:
                res = container.resources
                if res and res.requests:
                    total_cpu_req += _parse_cpu(res.requests.get("cpu", "0"))
                    total_mem_req += _parse_memory(res.requests.get("memory", "0"))
                if res and res.limits:
                    total_cpu_lim += _parse_cpu(res.limits.get("cpu", "0"))
                    total_mem_lim += _parse_memory(res.limits.get("memory", "0"))

        output = f"Node: {node_name}\n"
        output += f"Pods scheduled: {len(pods.items)}\n\n"
        output += f"Total CPU requests:  {total_cpu_req}m\n"
        output += f"Total CPU limits:    {total_cpu_lim}m\n"
        output += f"Total Memory requests: {total_mem_req}Mi\n"
        output += f"Total Memory limits:   {total_mem_lim}Mi\n"

        return output
    except Exception as e:
        return f"Error getting node resources: {e}"


# ── Namespaces ────────────────────────────────────────────────────────────────

@tool
def get_namespaces() -> str:
    """List all namespaces in the cluster.

    Returns:
        Namespace names and their status.
    """
    try:
        v1 = client.CoreV1Api()
        ns_list = v1.list_namespace()

        output = f"{'NAME':<30} {'STATUS':<12}\n"
        output += "-" * 42 + "\n"

        for ns in ns_list.items:
            output += f"{ns.metadata.name:<30} {ns.status.phase:<12}\n"

        return output
    except Exception as e:
        return f"Error getting namespaces: {e}"


# ── ConfigMaps & Secrets (metadata only) ──────────────────────────────────────

@tool
def get_configmaps(namespace: str) -> str:
    """List ConfigMaps in a namespace (names only, no sensitive data).

    Args:
        namespace: The Kubernetes namespace.

    Returns:
        List of ConfigMap names and their data key count.
    """
    try:
        v1 = client.CoreV1Api()
        cms = v1.list_namespaced_config_map(namespace=namespace)

        output = f"ConfigMaps in '{namespace}':\n\n"
        output += f"{'NAME':<45} {'DATA KEYS'}\n"
        output += "-" * 55 + "\n"

        for cm in cms.items:
            key_count = len(cm.data) if cm.data else 0
            output += f"{cm.metadata.name:<45} {key_count}\n"

        return output
    except Exception as e:
        return f"Error getting configmaps: {e}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_cpu(value: str) -> int:
    """Parse CPU string to millicores."""
    if not value:
        return 0
    if value.endswith("m"):
        return int(value[:-1])
    return int(float(value) * 1000)


def _parse_memory(value: str) -> int:
    """Parse memory string to Mi."""
    if not value:
        return 0
    units = {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024, "Ti": 1024 * 1024}
    for suffix, multiplier in units.items():
        if value.endswith(suffix):
            return int(float(value[: -len(suffix)]) * multiplier)
    return int(int(value) / (1024 * 1024))
