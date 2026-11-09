import json
import os

import k8sapi
import requests

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3.5:35b')


def main(args, ctx=None):
    query = (args.get("query") or "").strip()
    print(f"DEBUG: Query received: {query}")
    print(f"DEBUG: OLLAMA_URL: {OLLAMA_URL}")
    print(f"DEBUG: OLLAMA_MODEL: {OLLAMA_MODEL}")

    if not query:
        return {
            "error": "No query provided",
            "message": "Please ask a question about your Kubernetes cluster"
        }

    try:
        # Load kubeconfig from S3 (active marker, then most recent)
        if not ctx or not ctx.S3_CLIENT:
            print("DEBUG: No S3 client available")
            return {
                "error": "No S3 client available",
                "message": "Configuration error"
            }

        print(f"DEBUG: Listing kubeconfigs in S3...")
        key, kubeconfig_dict, load_error = k8sapi.load_kubeconfig_from_s3(ctx)
        if not key or not isinstance(kubeconfig_dict, dict):
            print(f"DEBUG: No kubeconfigs found in S3: {load_error}")
            response = {
                "error": "No kubeconfig found",
                "message": "Please upload a kubeconfig file first"
            }
            if load_error:
                response["details"] = load_error
            return response
        print(f"DEBUG: Loading kubeconfig: {key}")
        print(f"DEBUG: Kubeconfig parsed, clusters: {len(kubeconfig_dict.get('clusters', []))}")

        try:
            k8s = k8sapi.K8sClient(kubeconfig_dict)
        except k8sapi.KubeConfigError as e:
            return {
                "error": f"Invalid kubeconfig: {e}",
                "message": "Failed to parse the stored kubeconfig"
            }

        # Fetch all resources (plain JSON dicts, no kubernetes client)
        print("DEBUG: Fetching cluster resources...")
        try:
            pods = k8s.list_all("/api/v1/pods")
            print(f"DEBUG: Pods fetched: {len(pods)}")
            pvcs = k8s.list_all("/api/v1/persistentvolumeclaims")
            print(f"DEBUG: PVCs fetched: {len(pvcs)}")
            nodes = k8s.list_all("/api/v1/nodes")
            print(f"DEBUG: Nodes fetched: {len(nodes)}")
            deployments = k8s.list_all("/apis/apps/v1/deployments")
            print(f"DEBUG: Deployments fetched: {len(deployments)}")
        except k8sapi.KubeApiError as e:
            print(f"DEBUG: Kubernetes API error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Kubernetes API error: {str(e)}",
                "message": "Failed to retrieve cluster data",
                "details": str(e)
            }

        # Extract relevant data for response
        pods_data = []
        for pod in pods:
            meta = pod.get("metadata") or {}
            status = pod.get("status") or {}
            spec = pod.get("spec") or {}
            pods_data.append({
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
                "status": status.get("phase", "Unknown"),
                "node": spec.get("nodeName", ""),
                "containers": len(spec.get("containers") or [])
            })

        pvcs_data = []
        for pvc in pvcs:
            meta = pvc.get("metadata") or {}
            status = pvc.get("status") or {}
            spec = pvc.get("spec") or {}
            resources = spec.get("resources") or {}
            requests_map = resources.get("requests") or {} if isinstance(resources, dict) else {}
            storage = requests_map.get("storage") if isinstance(requests_map, dict) else None
            pvcs_data.append({
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
                "status": status.get("phase", "Unknown"),
                "capacity": storage
            })

        nodes_data = []
        for node in nodes:
            meta = node.get("metadata") or {}
            status = node.get("status") or {}
            node_status = "Unknown"
            for condition in status.get("conditions") or []:
                if isinstance(condition, dict) and condition.get("type") == "Ready":
                    node_status = "Ready" if condition.get("status") == "True" else "NotReady"
                    break
            nodes_data.append({
                "name": meta.get("name", ""),
                "status": node_status,
                "capacity": status.get("capacity") or {},
                "allocatable": status.get("allocatable") or {}
            })

        deployments_data = []
        for deployment in deployments:
            meta = deployment.get("metadata") or {}
            status = deployment.get("status") or {}
            deployments_data.append({
                "name": meta.get("name", ""),
                "namespace": meta.get("namespace", ""),
                "replicas": status.get("replicas", 0),
                "ready_replicas": status.get("readyReplicas", 0)
            })

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
            return {
                "response": ollama_response,
                "source": "llm"
            }
        except Exception as e:
            print(f"DEBUG: Ollama error: {str(e)}")
            print("DEBUG: Falling back to deterministic response")
            response = generate_response(query, pods_data, pvcs_data, nodes_data, deployments_data)
            return response

    except Exception as e:
        print(f"DEBUG: General error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "An unexpected error occurred"
        }


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
