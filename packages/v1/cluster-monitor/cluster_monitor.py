import os
import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def main(args, ctx=None):
    try:
        # Load kubeconfig
        if 'KUBECONFIG' in os.environ:
            config.load_kube_config(os.environ['KUBECONFIG'])
        else:
            config.load_kube_config()
        
        # Create API instances
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        
        # Get pods
        pods = v1.list_pod_for_all_namespaces(watch=False)
        
        # Get PVCs
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
        
        # Get nodes
        nodes = v1.list_node(watch=False)
        
        # Process pods data with more detailed information
        pods_data = []
        pod_status_counts = {
            "Running": 0,
            "Pending": 0,
            "Failed": 0,
            "Succeeded": 0
        }
        
        for pod in pods.items:
            pod_data = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase if pod.status else "Unknown",
                "node": pod.spec.node_name,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                        "ready": False  # Simplified, real API would have more detail
                    }
                    for container in pod.spec.containers
                ]
            }
            
            # Count pod statuses
            if pod.status and pod.status.phase in pod_status_counts:
                pod_status_counts[pod.status.phase] += 1
            
            pods_data.append(pod_data)
        
        # Process PVCs data
        pvcs_data = []
        pvc_status_counts = {
            "Bound": 0,
            "Pending": 0,
            "Lost": 0
        }
        
        for pvc in pvcs.items:
            pvc_data = {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase if hasattr(pvc, 'status') and pvc.status else 'Unknown',
                "capacity": pvc.spec.resources.requests.get('storage') if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'resources') and hasattr(pvc.spec.resources, 'requests') else None,
                "access_modes": pvc.spec.access_modes if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'access_modes') else [],
                "volume_name": pvc.spec.volume_name if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'volume_name') else None
            }
            
            # Count PVC statuses
            if hasattr(pvc, 'status') and pvc.status and pvc.status.phase in pvc_status_counts:
                pvc_status_counts[pvc.status.phase] += 1
            
            pvcs_data.append(pvc_data)
        
        # Process nodes data
        nodes_data = []
        node_status_counts = {
            "Ready": 0,
            "NotReady": 0,
            "SchedulingDisabled": 0
        }
        
        for node in nodes.items:
            # Get node status (e.g., Ready, NotReady)
            node_status = "Unknown"
            if node.status and node.status.conditions:
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        node_status = condition.status
                        break
            
            node_data = {
                "name": node.metadata.name,
                "status": node_status,
                "conditions": [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message
                    }
                    for condition in node.status.conditions
                ] if node.status and node.status.conditions else [],
                "allocatable": node.status.allocatable if node.status and node.status.allocatable else {},
                "capacity": node.status.capacity if node.status and node.status.capacity else {},
                "labels": node.metadata.labels if node.metadata and node.metadata.labels else {}
            }
            
            # Count node statuses
            if node_status in node_status_counts:
                node_status_counts[node_status] += 1
            
            nodes_data.append(node_data)
        
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
            "timestamp": "2026-06-03T12:00:00Z",  # Add current timestamp
            "message": "Kubernetes cluster monitoring data successfully retrieved",
            "cluster": "Truk8s Dashboard"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        # More detailed error handling
        error_message = {
            "error": str(e),
            "message": "Failed to retrieve Kubernetes cluster data",
            "hint": "Make sure you have a valid kubeconfig file and permissions to access the cluster resources."
        }
        return json.dumps(error_message)
