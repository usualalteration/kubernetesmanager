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
        
        # Process data
        result = {
            "pods": {
                "items": [
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "node": pod.spec.node_name,
                        "containers": [
                            {
                                "name": container.name,
                                "image": container.image,
                                "ready": container_state.ready if hasattr(container_state, 'ready') else False
                            }
                            for container in pod.spec.containers
                        ]
                    }
                    for pod in pods.items
                ]
            },
            "pvcs": {
                "items": [
                    {
                        "name": pvc.metadata.name,
                        "namespace": pvc.metadata.namespace,
                        "status": pvc.status.phase if hasattr(pvc, 'status') and pvc.status else 'Unknown',
                        "capacity": pvc.spec.resources.requests.get('storage') if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'resources') and hasattr(pvc.spec.resources, 'requests') else None,
                        "access_modes": pvc.spec.access_modes if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'access_modes') else [],
                        "volume_name": pvc.spec.volume_name if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'volume_name') else None
                    }
                    for pvc in pvcs.items
                ]
            },
            "nodes": {
                "items": [
                    {
                        "name": node.metadata.name,
                        "status": [
                            condition.status for condition in node.status.conditions 
                            if condition.type == "Ready"
                        ][0] if node.status and node.status.conditions else "Unknown",
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
                    for node in nodes.items
                ]
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
