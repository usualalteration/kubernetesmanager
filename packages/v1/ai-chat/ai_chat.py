import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

def main(args, ctx=None):
    query = args.get("query", "").lower().strip()
    print(f"DEBUG: Query received: {query}")
    print(f"DEBUG: ctx type: {type(ctx)}")
    print(f"DEBUG: ctx.S3_CLIENT: {ctx.S3_CLIENT if ctx else 'No ctx'}")
    
    if not query:
        return json.dumps({
            "error": "No query provided",
            "message": "Please ask a question about your Kubernetes cluster"
        })
    
    try:
        # Load kubeconfig from S3
        if ctx and ctx.S3_CLIENT:
            try:
                print("DEBUG: Listing kubeconfigs in S3...")
                response = ctx.S3_CLIENT.list_objects_v2(Bucket=ctx.S3_DATA, Prefix='kubeconfigs/')
                print(f"DEBUG: S3 response: {response}")
                if 'Contents' in response and len(response['Contents']) > 0:
                    latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
                    print(f"DEBUG: Loading kubeconfig: {latest_file['Key']}")
                    obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=latest_file['Key'])
                    kubeconfig_content = obj['Body'].read().decode('utf-8')
                    print(f"DEBUG: Kubeconfig loaded, length: {len(kubeconfig_content)}")
                    kubeconfig_dict = yaml.safe_load(kubeconfig_content)
                    print(f"DEBUG: Kubeconfig parsed, clusters: {len(kubeconfig_dict.get('clusters', []))}")
                    config.load_kube_config_from_dict(kubeconfig_dict)
                    print("DEBUG: Kubeconfig loaded successfully")
                else:
                    print("DEBUG: No kubeconfigs found in S3")
                    return json.dumps({
                        "error": "No kubeconfig found",
                        "message": "Please upload a kubeconfig file first"
                    })
            except Exception as e:
                print(f"DEBUG: Error loading from S3: {str(e)}")
                import traceback
                traceback.print_exc()
                return json.dumps({
                    "error": f"Failed to load kubeconfig: {str(e)}",
                    "message": "Unable to connect to cluster"
                })
        else:
            print("DEBUG: No S3 client available")
            return json.dumps({
                "error": "No S3 client available",
                "message": "Configuration error"
            })
        
        # Create API instances
        print("DEBUG: Creating API instances...")
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        print("DEBUG: API instances created")
        
        # Get all resources
        print("DEBUG: Fetching pods...")
        pods = v1.list_pod_for_all_namespaces(watch=False)
        print(f"DEBUG: Pods fetched: {len(pods.items)}")
        
        print("DEBUG: Fetching PVCs...")
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
        print(f"DEBUG: PVCs fetched: {len(pvcs.items)}")
        
        print("DEBUG: Fetching nodes...")
        nodes = v1.list_node(watch=False)
        print(f"DEBUG: Nodes fetched: {len(nodes.items)}")
        
        print("DEBUG: Fetching deployments...")
        deployments = apps_v1.list_deployment_for_all_namespaces(watch=False)
        print(f"DEBUG: Deployments fetched: {len(deployments.items)}")
        
        # Extract relevant data for response
        pods_data = []
        for pod in pods.items:
            pods_data.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase if pod.status else "Unknown",
                "node": pod.spec.node_name,
                "containers": len(pod.spec.containers) if pod.spec else 0
            })
        
        pvcs_data = []
        for pvc in pvcs.items:
            pvcs_data.append({
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase if hasattr(pvc, 'status') and pvc.status else 'Unknown',
                "capacity": pvc.spec.resources.requests.get('storage') if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'resources') and hasattr(pvc.spec.resources, 'requests') else None
            })
        
        nodes_data = []
        for node in nodes.items:
            node_status = "Unknown"
            if node.status and node.status.conditions:
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        node_status = condition.status
                        break
            nodes_data.append({
                "name": node.metadata.name,
                "status": node_status,
                "capacity": node.status.capacity if node.status and node.status.capacity else {},
                "allocatable": node.status.allocatable if node.status and node.status.allocatable else {}
            })
        
        deployments_data = []
        for deployment in deployments.items:
            deployments_data.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.status.replicas if deployment.status else 0,
                "ready_replicas": deployment.status.ready_replicas if deployment.status else 0
            })
        
        # Generate response based on query
        response = generate_response(query, pods_data, pvcs_data, nodes_data, deployments_data)
        
        return json.dumps(response)
        
    except ApiException as e:
        return json.dumps({
            "error": f"Kubernetes API error: {e.reason}",
            "message": "Failed to retrieve cluster data",
            "details": str(e)
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "An unexpected error occurred"
        })

def generate_response(query, pods_data, pvcs_data, nodes_data, deployments_data):
    """Generate intelligent responses based on user query"""
    
    # Pod-related queries
    if 'pod' in query:
        if 'running' in query or 'status' in query:
            running = len([p for p in pods_data if p['status'] == 'Running'])
            pending = len([p for p in pods_data if p['status'] == 'Pending'])
            failed = len([p for p in pods_data if p['status'] == 'Failed'])
            return {
                "response": f"Pod Status Summary:\n- Total pods: {len(pods_data)}\n- Running: {running}\n- Pending: {pending}\n- Failed: {failed}",
                "data": {"pods": pods_data}
            }
        
        if 'namespace' in query:
            namespaces = list(set([p['namespace'] for p in pods_data]))
            return {
                "response": f"Pods found in namespaces: {', '.join(namespaces)}",
                "data": {"namespaces": namespaces}
            }
        
        if 'failed' in query or 'error' in query:
            failed_pods = [p for p in pods_data if p['status'] == 'Failed']
            if failed_pods:
                return {
                    "response": f"Failed pods found:\n" + "\n".join([f"- {p['name']} in {p['namespace']} on {p['node']}" for p in failed_pods]),
                    "data": {"failed_pods": failed_pods}
                }
            return {
                "response": "No failed pods found in the cluster.",
                "data": {"failed_pods": []}
            }
        
        if 'name' in query:
            pod_name = query.split('name')[-1].strip()
            matching = [p for p in pods_data if pod_name.lower() in p['name'].lower()]
            if matching:
                return {
                    "response": f"Found {len(matching)} pod(s) matching '{pod_name}':",
                    "data": {"matching_pods": matching}
                }
            return {
                "response": f"No pods found matching name '{pod_name}'",
                "data": {"matching_pods": []}
            }
        
        # Default pod response
        if pods_data:
            return {
                "response": f"Found {len(pods_data)} pods in your cluster. Here are some of them:\n" + 
                           "\n".join([f"- {p['name']} ({p['namespace']}) - {p['status']}" for p in pods_data[:10]]),
                "data": {"pods": pods_data}
            }
        return {
            "response": "No pods found in your cluster.",
            "data": {"pods": []}
        }
    
    # PVC-related queries
    elif 'pvc' in query or 'storage' in query or 'persistent' in query:
        if 'status' in query:
            bound = len([p for p in pvcs_data if p['status'] == 'Bound'])
            pending = len([p for p in pvcs_data if p['status'] == 'Pending'])
            return {
                "response": f"PVC Status Summary:\n- Total PVCs: {len(pvcs_data)}\n- Bound: {bound}\n- Pending: {pending}",
                "data": {"pvcs": pvcs_data}
            }
        
        if 'namespace' in query:
            namespaces = list(set([p['namespace'] for p in pvcs_data]))
            return {
                "response": f"PVCs found in namespaces: {', '.join(namespaces)}",
                "data": {"namespaces": namespaces}
            }
        
        if 'capacity' in query or 'size' in query:
            return {
                "response": f"Storage Capacity Summary:\n" + 
                           "\n".join([f"- {p['name']}: {p['capacity']}" for p in pvcs_data if p['capacity']]),
                "data": {"pvcs": pvcs_data}
            }
        
        # Default PVC response
        if pvcs_data:
            return {
                "response": f"Found {len(pvcs_data)} PVCs in your cluster. Here are some:\n" + 
                           "\n".join([f"- {p['name']} ({p['namespace']}) - {p['status']}" for p in pvcs_data[:10]]),
                "data": {"pvcs": pvcs_data}
            }
        return {
            "response": "No PVCs found in your cluster.",
            "data": {"pvcs": []}
        }
    
    # Node-related queries
    elif 'node' in query:
        if 'status' in query or 'ready' in query:
            ready = len([n for n in nodes_data if n['status'] == 'Ready'])
            not_ready = len([n for n in nodes_data if n['status'] == 'NotReady'])
            return {
                "response": f"Node Status Summary:\n- Total nodes: {len(nodes_data)}\n- Ready: {ready}\n- Not Ready: {not_ready}",
                "data": {"nodes": nodes_data}
            }
        
        if 'capacity' in query or 'cpu' in query or 'memory' in query:
            return {
                "response": f"Node Capacity Summary:\n" + 
                           "\n".join([f"- {n['name']}: CPU={n['capacity'].get('cpu', 'N/A')}, Memory={n['capacity'].get('memory', 'N/A')}" for n in nodes_data]),
                "data": {"nodes": nodes_data}
            }
        
        if 'not ready' in query or 'down' in query:
            not_ready_nodes = [n for n in nodes_data if n['status'] == 'NotReady']
            if not_ready_nodes:
                return {
                    "response": f"Not ready nodes:\n" + 
                               "\n".join([f"- {n['name']}" for n in not_ready_nodes]),
                    "data": {"not_ready_nodes": not_ready_nodes}
                }
            return {
                "response": "All nodes are ready.",
                "data": {"not_ready_nodes": []}
            }
        
        # Default node response
        if nodes_data:
            return {
                "response": f"Found {len(nodes_data)} nodes in your cluster. Here are some:\n" + 
                           "\n".join([f"- {n['name']} ({n['status']})" for n in nodes_data[:10]]),
                "data": {"nodes": nodes_data}
            }
        return {
            "response": "No nodes found in your cluster.",
            "data": {"nodes": []}
        }
    
    # Deployment-related queries
    elif 'deployment' in query or 'deploy' in query:
        if 'status' in query:
            total = len(deployments_data)
            ready = sum([d['ready_replicas'] for d in deployments_data])
            return {
                "response": f"Deployment Status:\n- Total deployments: {total}\n- Ready replicas: {ready}",
                "data": {"deployments": deployments_data}
            }
        
        if 'replica' in query or 'scale' in query:
            return {
                "response": f"Deployment Replicas:\n" + 
                           "\n".join([f"- {d['name']}: {d['ready_replicas']}/{d['replicas']} ready" for d in deployments_data]),
                "data": {"deployments": deployments_data}
            }
        
        # Default deployment response
        if deployments_data:
            return {
                "response": f"Found {len(deployments_data)} deployments in your cluster. Here are some:\n" + 
                           "\n".join([f"- {d['name']} ({d['namespace']}) - {d['ready_replicas']}/{d['replicas']} replicas" for d in deployments_data[:10]]),
                "data": {"deployments": deployments_data}
            }
        return {
            "response": "No deployments found in your cluster.",
            "data": {"deployments": []}
        }
    
    # Health/Status queries
    elif 'health' in query or 'status' in query or 'cluster' in query:
        return {
            "response": f"Cluster Health Report:\n" +
                       f"- Pods: {len(pods_data)} total (Running: {len([p for p in pods_data if p['status'] == 'Running'])})\n" +
                       f"- PVCs: {len(pvcs_data)} total (Bound: {len([p for p in pvcs_data if p['status'] == 'Bound'])})\n" +
                       f"- Nodes: {len(nodes_data)} total (Ready: {len([n for n in nodes_data if n['status'] == 'Ready'])})",
            "data": {
                "pods": pods_data,
                "pvcs": pvcs_data,
                "nodes": nodes_data
            }
        }
    
    # Default response
    return {
        "response": "I'm your Kubernetes assistant. I can help you with:\n" +
                   "- Pods: Ask about running pods, failed pods, pods by name, or pods in namespaces\n" +
                   "- PVCs: Ask about storage, PVC status, or capacity\n" +
                   "- Nodes: Ask about node status, capacity, or ready nodes\n" +
                   "- Deployments: Ask about deployment status or replicas\n" +
                   "\nTry asking: 'What is the status of my pods?' or 'Show me failed pods'",
        "data": {}
    }
