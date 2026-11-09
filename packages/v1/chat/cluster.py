"""
Cluster data fetcher for Truk8s chat.
Loads kubeconfig from S3, queries the Kubernetes cluster over the REST API
(using only stdlib + runtime-shipped libraries, see k8sapi.py), and returns
a concise context summary suitable for LLM injection.
"""

import k8sapi


def get_active_config(ctx):
    """
    Return (key, config_dict, error) of the active kubeconfig.
    Reads .active marker; falls back to most recent by LastModified.
    """
    return k8sapi.load_kubeconfig_from_s3(ctx)


def load_kubeconfig(ctx):
    """Load the active kubeconfig from S3. Returns the parsed dict or None."""
    try:
        key, config, error = get_active_config(ctx)
        if error:
            print(f"cluster.load_kubeconfig: {error}")
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
    try:
        key, kubeconfig, load_error = get_active_config(ctx)
    except Exception as e:
        return {"ok": False, "error": f"No kubeconfig found: {e}", "context": ""}
    if not kubeconfig or not isinstance(kubeconfig, dict):
        detail = f" {load_error}" if load_error else ""
        return {
            "ok": False,
            "error": f"No kubeconfig found. Upload a kubeconfig file first.{detail}",
            "context": "",
        }

    try:
        k8s = k8sapi.K8sClient(kubeconfig)
    except k8sapi.KubeConfigError as e:
        return {"ok": False, "error": f"Invalid kubeconfig: {e}", "context": ""}

    try:
        pods = k8s.list_all("/api/v1/pods")
        pvcs = k8s.list_all("/api/v1/persistentvolumeclaims")
        nodes = k8s.list_all("/api/v1/nodes")
        deployments = k8s.list_all("/apis/apps/v1/deployments")
    except k8sapi.KubeApiError as e:
        return {"ok": False, "error": f"Kubernetes API error: {e}", "context": ""}
    except Exception as e:
        return {"ok": False, "error": f"Cluster connection error: {e}", "context": ""}

    # --- Pods ---
    pod_items = []
    pod_counts = {"Running": 0, "Pending": 0, "Failed": 0, "Succeeded": 0}
    for pod in pods:
        meta = pod.get("metadata") or {}
        status = pod.get("status") or {}
        spec = pod.get("spec") or {}
        phase = str(status.get("phase") or "Unknown")
        if phase in pod_counts:
            pod_counts[phase] += 1
        container_statuses = status.get("containerStatuses") or []
        restarts = sum(
            (cs.get("restartCount") or 0)
            for cs in container_statuses
            if isinstance(cs, dict)
        )
        pod_items.append(
            {
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
                "status": phase,
                "node": spec.get("nodeName") or "",
                "restarts": restarts,
            }
        )

    # --- PVCs ---
    pvc_items = []
    pvc_counts = {"Bound": 0, "Pending": 0, "Lost": 0}
    for pvc in pvcs:
        meta = pvc.get("metadata") or {}
        status = pvc.get("status") or {}
        spec = pvc.get("spec") or {}
        phase = str(status.get("phase") or "Unknown")
        if phase in pvc_counts:
            pvc_counts[phase] += 1
        resources = spec.get("resources") or {}
        requests = resources.get("requests") or {} if isinstance(resources, dict) else {}
        storage = requests.get("storage") if isinstance(requests, dict) else None
        capacity = str(storage) if storage else "N/A"
        pvc_items.append(
            {
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
                "status": phase,
                "capacity": capacity,
                "storage_class": spec.get("storageClassName") or "",
            }
        )

    # --- Nodes ---
    node_items = []
    node_counts = {"Ready": 0, "NotReady": 0}
    for node in nodes:
        meta = node.get("metadata") or {}
        status = node.get("status") or {}
        state = "Unknown"
        for cond in status.get("conditions") or []:
            if isinstance(cond, dict) and cond.get("type") == "Ready":
                state = "Ready" if cond.get("status") == "True" else "NotReady"
                break
        if state in node_counts:
            node_counts[state] += 1
        alloc = {}
        allocatable = status.get("allocatable") or {}
        if isinstance(allocatable, dict):
            alloc = {k: str(v) for k, v in allocatable.items()}
        node_items.append(
            {
                "name": meta.get("name", ""),
                "status": state,
                "allocatable_cpu": alloc.get("cpu", ""),
                "allocatable_memory": alloc.get("memory", ""),
            }
        )

    # --- Deployments ---
    dep_items = []
    for dep in deployments:
        meta = dep.get("metadata") or {}
        status = dep.get("status") or {}
        replicas = status.get("replicas") or 0
        ready = status.get("readyReplicas") or 0
        dep_items.append(
            {
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
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
