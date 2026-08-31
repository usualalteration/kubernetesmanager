import os
import json
from datetime import datetime, timezone
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def calculate_age(created_at):
    """Calculate a human-readable age string from a creation timestamp."""
    if not created_at:
        return "Unknown"
    try:
        ts = created_at.replace('Z', '+00:00')
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


def main(args, ctx=None):
    try:
        # Load kubeconfig from S3
        if ctx and ctx.S3_CLIENT:
            try:
                print("DEBUG: Listing kubeconfigs in S3...")
                # List kubeconfigs in S3
                response = ctx.S3_CLIENT.list_objects_v2(Bucket=ctx.S3_DATA, Prefix='kubeconfigs/')
                if 'Contents' in response and len(response['Contents']) > 0:
                    print(f"DEBUG: Found {len(response['Contents'])} kubeconfig(s)")
                    # Get the most recent kubeconfig
                    latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
                    print(f"DEBUG: Loading kubeconfig: {latest_file['Key']}")
                    obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=latest_file['Key'])
                    kubeconfig_content = obj['Body'].read().decode('utf-8')
                    print(f"DEBUG: Kubeconfig loaded, length: {len(kubeconfig_content)}")
                    
                    # Load from memory using load_kube_config_from_dict
                    from kubernetes import config as k8s_config
                    import yaml
                    kubeconfig_dict = yaml.safe_load(kubeconfig_content)
                    print(f"DEBUG: Kubeconfig parsed, clusters: {len(kubeconfig_dict.get('clusters', []))}")
                    k8s_config.load_kube_config_from_dict(kubeconfig_dict)
                else:
                    return json.dumps({
                        "error": "Invalid kube-config file. No configuration found.",
                        "message": "No kubeconfig file found in storage"
                    })
            except Exception as e:
                print(f"DEBUG: Error loading from S3: {str(e)}")
                return json.dumps({
                    "error": f"Failed to load kubeconfig from S3: {str(e)}",
                    "message": "Please upload a valid kubeconfig file first"
                })
        else:
            print("DEBUG: No S3 client available")
            # Try to load from default location
            try:
                config.load_kube_config()
            except Exception as e:
                return json.dumps({
                    "error": "Invalid kube-config file. No configuration found.",
                    "message": f"No kubeconfig available: {str(e)}"
                })
        
        # Create API instances
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        
        # Get pods
        pods = v1.list_pod_for_all_namespaces(watch=False)
        
        # Get PVCs
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
        
        # Get nodes
        nodes = v1.list_node(watch=False)
        
        # Process pods data - extract only what we need
        pods_data = []
        pod_status_counts = {
            "Running": 0,
            "Pending": 0,
            "Failed": 0,
            "Succeeded": 0
        }
        
        for pod in pods.items:
            # Extract pod status phase safely
            pod_phase = "Unknown"
            if pod.status and hasattr(pod.status, 'phase'):
                pod_phase = str(pod.status.phase)
            
            # Extract node name safely
            node_name = ""
            if pod.spec and hasattr(pod.spec, 'node_name'):
                node_name = str(pod.spec.node_name) if pod.spec.node_name else ""
            
            # Extract creation timestamp and calculate age
            pod_created_at = ""
            if pod.metadata and hasattr(pod.metadata, 'creation_timestamp') and pod.metadata.creation_timestamp:
                pod_created_at = str(pod.metadata.creation_timestamp)
            pod_age = calculate_age(pod_created_at)
            
            # Count pod statuses
            if pod_phase in pod_status_counts:
                pod_status_counts[pod_phase] += 1
            
            pods_data.append({
                "name": str(pod.metadata.name) if pod.metadata and pod.metadata.name else "unknown",
                "namespace": str(pod.metadata.namespace) if pod.metadata and pod.metadata.namespace else "default",
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
        
        for pvc in pvcs.items:
            # Extract PVC status phase safely
            pvc_phase = "Unknown"
            if pvc.status and hasattr(pvc.status, 'phase'):
                pvc_phase = str(pvc.status.phase)
            
            # Extract capacity safely
            capacity = "N/A"
            if pvc.spec and hasattr(pvc.spec, 'resources') and hasattr(pvc.spec.resources, 'requests'):
                if hasattr(pvc.spec.resources.requests, 'get'):
                    storage = pvc.spec.resources.requests.get('storage')
                    if storage:
                        capacity = str(storage)
            
            # Extract access modes safely
            access_modes = []
            if pvc.spec and hasattr(pvc.spec, 'access_modes'):
                access_modes = [str(mode) for mode in pvc.spec.access_modes] if pvc.spec.access_modes else []
            
            # Extract storage class safely
            storage_class = ""
            if pvc.spec and hasattr(pvc.spec, 'storage_class_name') and pvc.spec.storage_class_name:
                storage_class = str(pvc.spec.storage_class_name)
            
            # Extract creation timestamp and calculate age
            pvc_created_at = ""
            if pvc.metadata and hasattr(pvc.metadata, 'creation_timestamp') and pvc.metadata.creation_timestamp:
                pvc_created_at = str(pvc.metadata.creation_timestamp)
            pvc_age = calculate_age(pvc_created_at)
            
            # Count PVC statuses
            if pvc_phase in pvc_status_counts:
                pvc_status_counts[pvc_phase] += 1
            
            pvcs_data.append({
                "name": str(pvc.metadata.name) if pvc.metadata and pvc.metadata.name else "unknown",
                "namespace": str(pvc.metadata.namespace) if pvc.metadata and pvc.metadata.namespace else "default",
                "status": pvc_phase,
                "capacity": capacity,
                "access_modes": access_modes,
                "storage_class": storage_class,
                "age": pvc_age,
                "volume_name": str(pvc.spec.volume_name) if pvc.spec and hasattr(pvc.spec, 'volume_name') and pvc.spec.volume_name else ""
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
        for pod in pods.items:
            if pod.spec and hasattr(pod.spec, 'node_name') and pod.spec.node_name:
                node_name = str(pod.spec.node_name)
                pods_per_node[node_name] = pods_per_node.get(node_name, 0) + 1
        
        for node in nodes.items:
            # Get node status from conditions
            node_status = "Unknown"
            conditions_list = []
            if node.status and hasattr(node.status, 'conditions') and node.status.conditions:
                for condition in node.status.conditions:
                    conditions_list.append({
                        "type": str(condition.type) if condition.type else "",
                        "status": str(condition.status) if condition.status else "",
                        "reason": str(condition.reason) if condition.reason else "",
                        "message": str(condition.message) if condition.message else ""
                    })
                    if condition.type == "Ready" and condition.status == "True":
                        node_status = "Ready"
            
            # Get labels safely
            labels = {}
            if node.metadata and hasattr(node.metadata, 'labels') and node.metadata.labels:
                labels = {str(k): str(v) for k, v in node.metadata.labels.items()}
            
            # Extract allocatable resources safely
            allocatable = {}
            if node.status and hasattr(node.status, 'allocatable') and node.status.allocatable:
                allocatable = {str(k): str(v) for k, v in node.status.allocatable.items()}
            
            # Extract capacity safely
            capacity = {}
            if node.status and hasattr(node.status, 'capacity') and node.status.capacity:
                capacity = {str(k): str(v) for k, v in node.status.capacity.items()}
            
            # Count node statuses
            if node_status in node_status_counts:
                node_status_counts[node_status] += 1
            
            # Extract creation timestamp safely
            created_at = ""
            if node.metadata and hasattr(node.metadata, 'creation_timestamp'):
                created_at = str(node.metadata.creation_timestamp) if node.metadata.creation_timestamp else ""
            
            # Calculate age
            age = "Unknown"
            if created_at and 'T' in created_at:
                try:
                    from datetime import datetime, timezone
                    # Parse ISO format timestamp
                    ts = created_at.replace('Z', '+00:00')
                    created_time = datetime.fromisoformat(ts)
                    if created_time.tzinfo is None:
                        created_time = created_time.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    diff = now - created_time
                    
                    if diff.days > 0:
                        if diff.days >= 365:
                            age = f"{diff.days // 365}y"
                        elif diff.days >= 30:
                            age = f"{diff.days // 30}mo"
                        else:
                            age = f"{diff.days}d"
                    elif diff.seconds >= 3600:
                        age = f"{diff.seconds // 3600}h"
                    elif diff.seconds >= 60:
                        age = f"{diff.seconds // 60}m"
                    else:
                        age = f"{diff.seconds}s"
                except Exception as e:
                    print(f"DEBUG: Error calculating age: {e}")
            elif created_at:
                # Try alternative formats (e.g., "2026-08-23 21:05:41+00:00")
                try:
                    from datetime import datetime, timezone
                    # Handle "YYYY-MM-DD HH:MM:SS+00:00" format
                    ts = created_at.replace(' ', 'T')
                    if '+' not in ts and '-' not in ts[10:]:
                        ts = ts + '+00:00'
                    created_time = datetime.fromisoformat(ts)
                    if created_time.tzinfo is None:
                        created_time = created_time.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    diff = now - created_time
                    
                    if diff.days > 0:
                        if diff.days >= 365:
                            age = f"{diff.days // 365}y"
                        elif diff.days >= 30:
                            age = f"{diff.days // 30}mo"
                        else:
                            age = f"{diff.days}d"
                    elif diff.seconds >= 3600:
                        age = f"{diff.seconds // 3600}h"
                    elif diff.seconds >= 60:
                        age = f"{diff.seconds // 60}m"
                    else:
                        age = f"{diff.seconds}s"
                except Exception as e:
                    print(f"DEBUG: Error calculating age (alt format): {e}")
            
            nodes_data.append({
                "name": str(node.metadata.name) if node.metadata and node.metadata.name else "unknown",
                "status": node_status,
                "conditions": conditions_list,
                "allocatable": allocatable,
                "capacity": capacity,
                "labels": labels,
                "pods_count": pods_per_node.get(str(node.metadata.name), 0) if node.metadata and node.metadata.name else 0,
                "created_at": created_at,
                "age": age
            })
        
        # Process data
        result = {
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
            "timestamp": "2026-06-03T12:00:00Z",
            "message": "Kubernetes cluster monitoring data successfully retrieved",
            "cluster": "Truk8s Dashboard"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        # More detailed error handling
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        error_message = {
            "error": str(e),
            "message": "Failed to retrieve Kubernetes cluster data",
            "hint": "Make sure you have a valid kubeconfig file and permissions to access the cluster resources."
        }
        return json.dumps(error_message)