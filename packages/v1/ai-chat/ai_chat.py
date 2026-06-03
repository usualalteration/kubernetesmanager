import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml
import requests
import os

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3.5:35b')

def main(args, ctx=None):
    query = args.get("query", "").strip()
    print(f"DEBUG: Query received: {query}")
    print(f"DEBUG: ctx type: {type(ctx)}")
    print(f"DEBUG: ctx is None: {ctx is None}")
    print(f"DEBUG: ctx.S3_CLIENT: {ctx.S3_CLIENT if ctx else 'No ctx'}")
    print(f"DEBUG: OLLAMA_URL: {OLLAMA_URL}")
    print(f"DEBUG: OLLAMA_MODEL: {OLLAMA_MODEL}")
    
    if not query:
        return json.dumps({
            "error": "No query provided",
            "message": "Please ask a question about your Kubernetes cluster"
        })
    
    try:
        # Load kubeconfig from S3
        if not ctx or not ctx.S3_CLIENT:
            print("DEBUG: No S3 client available")
            return json.dumps({
                "error": "No S3 client available",
                "message": "Configuration error"
            })
        
        print("DEBUG: Listing kubeconfigs in S3...")
        print(f"DEBUG: ctx.S3_DATA: {ctx.S3_DATA}")
        response = ctx.S3_CLIENT.list_objects_v2(Bucket=ctx.S3_DATA, Prefix='kubeconfigs/')
        print(f"DEBUG: S3 response: {response}")
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            print("DEBUG: No kubeconfigs found in S3")
            return json.dumps({
                "error": "No kubeconfig found",
                "message": "Please upload a kubeconfig file first"
            })
        
        latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
        print(f"DEBUG: Loading kubeconfig: {latest_file['Key']}")
        obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=latest_file['Key'])
        kubeconfig_content = obj['Body'].read().decode('utf-8')
        print(f"DEBUG: Kubeconfig loaded, length: {len(kubeconfig_content)}")
        kubeconfig_dict = yaml.safe_load(kubeconfig_content)
        print(f"DEBUG: Kubeconfig parsed, clusters: {len(kubeconfig_dict.get('clusters', []))}")
        config.load_kube_config_from_dict(kubeconfig_dict)
        print("DEBUG: Kubeconfig loaded successfully")
        
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
        pods_data = [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase if pod.status else "Unknown",
                "node": pod.spec.node_name,
                "containers": len(pod.spec.containers) if pod.spec else 0
            }
            for pod in pods.items
        ]
        
        pvcs_data = [
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase if hasattr(pvc, 'status') and pvc.status else 'Unknown',
                "capacity": pvc.spec.resources.requests.get('storage') if hasattr(pvc, 'spec') and hasattr(pvc.spec, 'resources') and hasattr(pvc.spec.resources, 'requests') else None
            }
            for pvc in pvcs.items
        ]
        
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
        
        deployments_data = [
            {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.status.replicas if deployment.status else 0,
                "ready_replicas": deployment.status.ready_replicas if deployment.status else 0
            }
            for deployment in deployments.items
        ]
        
        # Prepare context for LLM
        cluster_context = {
            "pods": pods_data,
            "pvcs": pvcs_data,
            "nodes": nodes_data,
            "deployments": deployments_data
        }
        
        # Call Ollama LLM
        print("DEBUG: Calling Ollama LLM...")
        try:
            ollama_response = call_ollama(query, cluster_context)
            print(f"DEBUG: Ollama response: {ollama_response}")
            return json.dumps({
                "response": ollama_response,
                "source": "llm"
            })
        except Exception as e:
            print(f"DEBUG: Ollama error: {str(e)}")
            print("DEBUG: Falling back to deterministic response")
            response = generate_response(query, pods_data, pvcs_data, nodes_data, deployments_data)
            return json.dumps(response)
            
    except ApiException as e:
        print(f"DEBUG: Kubernetes API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "error": f"Kubernetes API error: {str(e)}",
            "message": "Failed to retrieve cluster data",
            "details": str(e)
        })
    except Exception as e:
        print(f"DEBUG: General error: {str(e)}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "message": "An unexpected error occurred"
        })

def call_ollama(query, cluster_context):
    """Call Ollama LLM with cluster context"""
    context_str = json.dumps(cluster_context, indent=2)
    
    prompt = f"""You are a Kubernetes assistant. Here is the current state of the cluster:

{context_str}

The user asked: "{query}"

Please provide a helpful and accurate response based on the cluster data above. Keep your response concise and focused on the user's question."""
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result.get('message', {}).get('content', 'No response from LLM')
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Ollama request failed: {str(e)}")
        raise Exception(f"Failed to connect to Ollama: {str(e)}")

def generate_response(query, pods_data, pvcs_data, nodes_data, deployments_data):
    """Generate deterministic responses based on query keywords"""
    if 'pod' in query:
        if 'failed' in query:
            failed = [p for p in pods_data if p['status'] == 'Failed']
            if failed:
                return {"response": f"Failed pods:\n" + "\n".join([f"- {p['name']}" for p in failed]), "data": {"failed_pods": failed}}
            return {"response": "No failed pods found.", "data": {"failed_pods": []}}
        return {"response": f"Found {len(pods_data)} pods.", "data": {"pods": pods_data}}
    
    elif 'pvc' in query or 'storage' in query:
        if 'capacity' in query:
            return {"response": f"Storage capacity info.", "data": {"pvcs": pvcs_data}}
        return {"response": f"Found {len(pvcs_data)} PVCs.", "data": {"pvcs": pvcs_data}}
    
    elif 'node' in query:
        if 'status' in query:
            ready = len([n for n in nodes_data if n['status'] == 'Ready'])
            return {"response": f"Nodes: {ready}/{len(nodes_data)} ready.", "data": {"nodes": nodes_data}}
        return {"response": f"Found {len(nodes_data)} nodes.", "data": {"nodes": nodes_data}}
    
    elif 'deployment' in query:
        return {"response": f"Found {len(deployments_data)} deployments.", "data": {"deployments": deployments_data}}
    
    elif 'health' in query or 'status' in query:
        return {"response": f"Cluster: {len(pods_data)} pods, {len(pvcs_data)} PVCs, {len(nodes_data)} nodes.", "data": {}}
    
    return {"response": "I can help with pods, PVCs, nodes, or deployments. Ask about their status!", "data": {}}
