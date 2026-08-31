"""
Cluster data fetcher for Truk8s chat.
Loads kubeconfig from S3, queries the Kubernetes cluster, and returns
a concise context summary suitable for LLM injection.
"""

import json
import yaml
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

ACTIVE_MARKER = "kubeconfigs/.active"


def get_active_config(ctx):
    """
    Return (key, config_dict) of the active kubeconfig.
    Reads .active marker; falls back to most recent by LastModified.
    """
    if not ctx or not hasattr(ctx, "S3_CLIENT") or not ctx.S3_CLIENT:
        return None, None

    # Try active marker first
    active_key = ""
    try:
        marker = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=ACTIVE_MARKER)
        active_key = marker["Body"].read().decode("utf-8").strip()
    except Exception:
        pass

    if active_key:
        try:
            obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=active_key)
            raw = obj["Body"].read().decode("utf-8")
            config = yaml.safe_load(raw)
            return active_key, config
        except Exception:
            pass

    # Fallback: most recent
    try:
        response = ctx.S3_CLIENT.list_objects_v2(
            Bucket=ctx.S3_DATA, Prefix="kubeconfigs/"
        )
        contents = [
            o for o in response.get("Contents", []) if o["Key"] != ACTIVE_MARKER
        ]
        if not contents:
            return None, None
        latest = max(contents, key=lambda x: x["LastModified"])
        obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=latest["Key"])
        raw = obj["Body"].read().decode("utf-8")
        config = yaml.safe_load(raw)
        return latest["Key"], config
    except Exception:
        return None, None


def load_kubeconfig(ctx):
    """Load the active kubeconfig from S3. Returns the parsed dict or None."""
    try:
        key, config = get_active_config(ctx)
        return config
    except Exception as e:
        print(f"cluster.load_kubeconfig error: {e}")
        return None


def fetch_cluster_summary(ctx):
    """
    Connect to the cluster and return a dict with:
      - ok: bool
      - context: str (human-readable cluster summary for the LLM)
      - error: str (if not ok)
    """
    kubeconfig = load_kubeconfig(ctx)
    if not kubeconfig:
        return {
            "ok": False,
            "error": "No kubeconfig found. Upload a kubeconfig file first.",
            "context": "",
        }

    try:
        k8s_config.load_kube_config_from_dict(kubeconfig)
    except Exception as e:
        return {"ok": False, "error": f"Invalid kubeconfig: {e}", "context": ""}

    try:
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        pods = v1.list_pod_for_all_namespaces(watch=False)
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
        nodes = v1.list_node(watch=False)
        deployments = apps_v1.list_deployment_for_all_namespaces(watch=False)
    except ApiException as e:
        return {
            "ok": False,
            "error": f"Kubernetes API error: {e}",
            "context": "",
        }
    except Exception as e:
        return {"ok": False, "error": f"Cluster connection error: {e}", "context": ""}

    # --- Pods ---
    pod_items = []
    pod_counts = {"Running": 0, "Pending": 0, "Failed": 0, "Succeeded": 0}
    for pod in pods.items:
        phase = str(pod.status.phase) if pod.status and pod.status.phase else "Unknown"
        if phase in pod_counts:
            pod_counts[phase] += 1
        pod_items.append(
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": phase,
                "node": pod.spec.node_name or "",
                "restarts": sum(
                    cs.restart_count or 0
                    for cs in (pod.status.container_statuses or [])
                )
                if pod.status and pod.status.container_statuses
                else 0,
            }
        )

    # --- PVCs ---
    pvc_items = []
    pvc_counts = {"Bound": 0, "Pending": 0, "Lost": 0}
    for pvc in pvcs.items:
        phase = str(pvc.status.phase) if pvc.status and pvc.status.phase else "Unknown"
        if phase in pvc_counts:
            pvc_counts[phase] += 1
        capacity = "N/A"
        if (
            pvc.spec
            and hasattr(pvc.spec, "resources")
            and hasattr(pvc.spec.resources, "requests")
        ):
            storage = pvc.spec.resources.requests.get("storage")
            if storage:
                capacity = str(storage)
        pvc_items.append(
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": phase,
                "capacity": capacity,
                "storage_class": pvc.spec.storage_class_name or "",
            }
        )

    # --- Nodes ---
    node_items = []
    node_counts = {"Ready": 0, "NotReady": 0}
    for node in nodes.items:
        status = "Unknown"
        if node.status and node.status.conditions:
            for cond in node.status.conditions:
                if cond.type == "Ready":
                    status = "Ready" if cond.status == "True" else "NotReady"
                    break
        if status in node_counts:
            node_counts[status] += 1
        alloc = {}
        if node.status and node.status.allocatable:
            alloc = {k: str(v) for k, v in node.status.allocatable.items()}
        node_items.append(
            {
                "name": node.metadata.name,
                "status": status,
                "allocatable_cpu": alloc.get("cpu", ""),
                "allocatable_memory": alloc.get("memory", ""),
            }
        )

    # --- Deployments ---
    dep_items = []
    for dep in deployments.items:
        replicas = dep.status.replicas if dep.status else 0
        ready = dep.status.ready_replicas if dep.status and dep.status.ready_replicas else 0
        dep_items.append(
            {
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": replicas,
                "ready_replicas": ready,
            }
        )

    # --- Build LLM context string ---
    lines = []
    lines.append(f"CLUSTER STATE SUMMARY")
    lines.append(f"Nodes: {len(node_items)} total ({node_counts['Ready']} Ready, {node_counts['NotReady']} NotReady)")
    lines.append(f"Pods: {len(pod_items)} total ({pod_counts['Running']} Running, {pod_counts['Pending']} Pending, {pod_counts['Failed']} Failed, {pod_counts['Succeeded']} Succeeded)")
    lines.append(f"PVCs: {len(pvc_items)} total ({pvc_counts['Bound']} Bound, {pvc_counts['Pending']} Pending, {pvc_counts['Lost']} Lost)")
    lines.append(f"Deployments: {len(dep_items)} total")
    lines.append("")

    # List non-running pods
    problem_pods = [p for p in pod_items if p["status"] not in ("Running", "Succeeded")]
    if problem_pods:
        lines.append("PODS NOT RUNNING/SUCCEEDED:")
        for p in problem_pods:
            lines.append(f"  - {p['namespace']}/{p['name']} [{p['status']}]")
        lines.append("")

    # List not-ready nodes
    bad_nodes = [n for n in node_items if n["status"] != "Ready"]
    if bad_nodes:
        lines.append("NODES NOT READY:")
        for n in bad_nodes:
            lines.append(f"  - {n['name']} [{n['status']}]")
        lines.append("")

    # List failed deployments
    failed_deps = [d for d in dep_items if d["ready_replicas"] < d["replicas"]]
    if failed_deps:
        lines.append("DEPLOYMENTS NOT FULLY READY:")
        for d in failed_deps:
            lines.append(f"  - {d['namespace']}/{d['name']} ({d['ready_replicas']}/{d['replicas']} ready)")
        lines.append("")

    lines.append("DETAILED POD LIST:")
    for p in pod_items:
        lines.append(f"  - {p['namespace']}/{p['name']} [{p['status']}] node={p['node']} restarts={p['restarts']}")
    lines.append("")
    lines.append("DETAILED NODE LIST:")
    for n in node_items:
        lines.append(f"  - {n['name']} [{n['status']}] cpu={n['allocatable_cpu']} mem={n['allocatable_memory']}")
    lines.append("")
    lines.append("DETAILED PVC LIST:")
    for pvc in pvc_items:
        lines.append(f"  - {pvc['namespace']}/{pvc['name']} [{pvc['status']}] cap={pvc['capacity']} sc={pvc['storage_class']}")
    lines.append("")
    lines.append("DETAILED DEPLOYMENT LIST:")
    for d in dep_items:
        lines.append(f"  - {d['namespace']}/{d['name']} ({d['ready_replicas']}/{d['replicas']} ready)")

    return {
        "ok": True,
        "error": "",
        "context": "\n".join(lines),
        "summary": {
            "pods": pod_counts,
            "pvcs": pvc_counts,
            "nodes": node_counts,
            "pod_count": len(pod_items),
            "pvc_count": len(pvc_items),
            "node_count": len(node_items),
            "deployment_count": len(dep_items),
        },
    }
