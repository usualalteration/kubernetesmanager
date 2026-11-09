import json
from datetime import datetime, timezone

import k8sapi


def calculate_age(created_at):
    """Calculate a human-readable age string from a creation timestamp."""
    if not created_at:
        return "Unknown"
    try:
        ts = str(created_at).replace('Z', '+00:00')
        if 'T' not in ts:
            ts = ts.replace(' ', 'T')
        created_time = datetime.fromisoformat(ts)
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - created_time
        if diff.days > 0:
            if diff.days >= 365:
                return f"{diff.days // 365}y"
            if diff.days >= 30:
                return f"{diff.days // 30}mo"
            return f"{diff.days}d"
        if diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h"
        if diff.seconds >= 60:
            return f"{diff.seconds // 60}m"
        return f"{diff.seconds}s"
    except Exception as e:
        print(f"DEBUG: Error calculating age: {e}")
        return "Unknown"


def _metadata(item):
    meta = item.get("metadata") if isinstance(item, dict) else None
    return meta if isinstance(meta, dict) else {}


def _status(item):
    status = item.get("status") if isinstance(item, dict) else None
    return status if isinstance(status, dict) else {}


def _spec(item):
    spec = item.get("spec") if isinstance(item, dict) else None
    return spec if isinstance(spec, dict) else {}


def main(args, ctx=None):
    try:
        # Load kubeconfig from S3 (active marker, then most recent)
        key, kubeconfig_dict, load_error = k8sapi.load_kubeconfig_from_s3(ctx)
        if not key or not isinstance(kubeconfig_dict, dict):
            message = "No kubeconfig file found in storage"
            if load_error:
                message = f"No kubeconfig file found in storage: {load_error}"
            return {
                "error": "Invalid kube-config file. No configuration found.",
                "message": message
            }
        print(f"DEBUG: Loading kubeconfig: {key}")

        try:
            k8s = k8sapi.K8sClient(kubeconfig_dict)
        except k8sapi.KubeConfigError as e:
            return {
                "error": "Invalid kube-config file. No configuration found.",
                "message": str(e)
            }

        # Fetch all resources (plain JSON dicts, no kubernetes client)
        try:
            pods = k8s.list_all("/api/v1/pods")
            pvcs = k8s.list_all("/api/v1/persistentvolumeclaims")
            nodes = k8s.list_all("/api/v1/nodes")
        except k8sapi.KubeApiError as e:
            return {
                "error": f"Kubernetes API error: {e}",
                "message": "Failed to retrieve Kubernetes cluster data",
                "hint": "Make sure you have a valid kubeconfig file and permissions to access the cluster resources."
            }

        # Process pods data - extract only what we need
        pods_data = []
        pod_status_counts = {
            "Running": 0,
            "Pending": 0,
            "Failed": 0,
            "Succeeded": 0
        }

        for pod in pods:
            pod_meta = _metadata(pod)
            pod_status = _status(pod)
            pod_spec = _spec(pod)

            pod_phase = str(pod_status.get("phase") or "Unknown")
            node_name = str(pod_spec.get("nodeName") or "")
            pod_created_at = str(pod_meta.get("creationTimestamp") or "")
            pod_age = calculate_age(pod_created_at)

            if pod_phase in pod_status_counts:
                pod_status_counts[pod_phase] += 1

            pods_data.append({
                "name": str(pod_meta.get("name") or "unknown"),
                "namespace": str(pod_meta.get("namespace") or "default"),
                "status": pod_phase,
                "node": node_name,
                "age": pod_age
            })

        # Process PVCs data - extract only what we need
        pvcs_data = []
        pvc_status_counts = {
            "Bound": 0,
            "Pending": 0,
            "Lost": 0
        }

        for pvc in pvcs:
            pvc_meta = _metadata(pvc)
            pvc_status = _status(pvc)
            pvc_spec = _spec(pvc)

            pvc_phase = str(pvc_status.get("phase") or "Unknown")

            requests_ = pvc_spec.get("resources", {})
            requests_ = requests_.get("requests", {}) if isinstance(requests_, dict) else {}
            storage = requests_.get("storage") if isinstance(requests_, dict) else None
            capacity = str(storage) if storage else "N/A"

            access_modes_raw = pvc_spec.get("accessModes") or []
            access_modes = [str(mode) for mode in access_modes_raw] if isinstance(access_modes_raw, list) else []

            storage_class = str(pvc_spec.get("storageClassName") or "")
            pvc_created_at = str(pvc_meta.get("creationTimestamp") or "")
            pvc_age = calculate_age(pvc_created_at)

            if pvc_phase in pvc_status_counts:
                pvc_status_counts[pvc_phase] += 1

            pvcs_data.append({
                "name": str(pvc_meta.get("name") or "unknown"),
                "namespace": str(pvc_meta.get("namespace") or "default"),
                "status": pvc_phase,
                "capacity": capacity,
                "access_modes": access_modes,
                "storage_class": storage_class,
                "age": pvc_age,
                "volume_name": str(pvc_spec.get("volumeName") or "")
            })

        # Process nodes data - extract only what we need
        nodes_data = []
        node_status_counts = {
            "Ready": 0,
            "NotReady": 0,
            "SchedulingDisabled": 0
        }

        # Pre-calculate pods per node
        pods_per_node = {}
        for pod in pods:
            node_name = str(_spec(pod).get("nodeName") or "")
            if node_name:
                pods_per_node[node_name] = pods_per_node.get(node_name, 0) + 1

        for node in nodes:
            node_meta = _metadata(node)
            node_status = _status(node)

            # Get node status from conditions
            node_state = "Unknown"
            conditions_list = []
            conditions_raw = node_status.get("conditions") or []
            for condition in conditions_raw if isinstance(conditions_raw, list) else []:
                if not isinstance(condition, dict):
                    continue
                cond_type = str(condition.get("type") or "")
                cond_status = str(condition.get("status") or "")
                conditions_list.append({
                    "type": cond_type,
                    "status": cond_status,
                    "reason": str(condition.get("reason") or ""),
                    "message": str(condition.get("message") or "")
                })
                if cond_type == "Ready":
                    node_state = "Ready" if cond_status == "True" else "NotReady"
                if cond_type == "SchedulingDisabled" and cond_status == "True":
                    node_status_counts["SchedulingDisabled"] += 1

            if node_state in node_status_counts:
                node_status_counts[node_state] += 1

            # Labels
            labels_raw = node_meta.get("labels") or {}
            labels = {str(k): str(v) for k, v in labels_raw.items()} if isinstance(labels_raw, dict) else {}

            # Allocatable and capacity resources
            allocatable_raw = node_status.get("allocatable") or {}
            allocatable = {str(k): str(v) for k, v in allocatable_raw.items()} if isinstance(allocatable_raw, dict) else {}

            capacity_raw = node_status.get("capacity") or {}
            capacity = {str(k): str(v) for k, v in capacity_raw.items()} if isinstance(capacity_raw, dict) else {}

            node_name = str(node_meta.get("name") or "unknown")
            created_at = str(node_meta.get("creationTimestamp") or "")

            nodes_data.append({
                "name": node_name,
                "status": node_state,
                "conditions": conditions_list,
                "allocatable": allocatable,
                "capacity": capacity,
                "labels": labels,
                "pods_count": pods_per_node.get(node_name, 0),
                "created_at": created_at,
                "age": calculate_age(created_at)
            })

        result = {
            "version": "2.0-stdlib",
            "pods": {
                "items": pods_data,
                "summary": pod_status_counts
            },
            "pvcs": {
                "items": pvcs_data,
                "summary": pvc_status_counts
            },
            "nodes": {
                "items": nodes_data,
                "summary": node_status_counts
            },
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "message": "Kubernetes cluster monitoring data successfully retrieved",
            "cluster": "Truk8s Dashboard"
        }

        return result

    except k8sapi.KubeApiError as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Failed to retrieve Kubernetes cluster data",
            "hint": "Make sure you have a valid kubeconfig file and permissions to access the cluster resources."
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Failed to retrieve Kubernetes cluster data",
            "hint": "Make sure you have a valid kubeconfig file and permissions to access the cluster resources."
        }
