from openai import OpenAI
import os, socket, time, json, pathlib

# load the instruction file
def loader(file):
    abs_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(abs_path)
    path =  pathlib.Path(os.path.join(current_dir, file))
    text = path.read_text()
    lines = text.split("\n")
    res = []
    for line in lines:
        try:
            line = line.strip()
            if not line.startswith("{"):
                continue
            res.append(json.loads(line))
        except:
            print("error parsing line:", line)
    print(f"loaded #{len(res)} instructions from {file}")
    return res

class LLM:
    def __init__(self, args, cluster_ctx=""):
        # params
        self.base_url  = args.get("AI_BASE_URL", os.getenv("AI_BASE_URL", "missing AI_BASE_URL"))
        self.api_key = args.get("AI_API_KEY", os.getenv("AI_API_KEY", "missing AI_API_KEY"))
        self.model = args.get("AI_CHAT_MODEL", os.getenv("AI_CHAT_MODEL", "missing AI_CHAT_MODEL"))
        self.rate = 0.01
        # urls
        self.ai = OpenAI(base_url=self.base_url, api_key=self.api_key)

        self.instruct = loader("doc.jsonl")
        self.cluster_ctx = cluster_ctx
        print(self.model)

        # Base messages: system instructions from RAG
        self.messages = list(self.instruct)

        # Inject live cluster context as a system message
        if cluster_ctx:
            self.messages.append({
                "role": "system",
                "content": (
                    "You are an AI assistant for a Kubernetes dashboard called Truk8s. "
                    "You have real-time access to the cluster state below. "
                    "Use this data to answer questions about pods, nodes, PVCs, and deployments. "
                    "If the user asks about resources, refer to the actual cluster data. "
                    "Be concise and helpful.\n\n"
                    f"--- LIVE CLUSTER DATA ---\n{cluster_ctx}\n--- END CLUSTER DATA ---"
                )
            })

        # Add conversation history
        self.context = []
        if "messages" in args:
            self.context = args.get("messages", [])
            self.messages += self.context

    def welcome(self, args, cluster_summary=None):
        text = f"Welcome to Truk8s Chat\nHost: {self.base_url}\nModel: {self.model}\n"
        if cluster_summary:
            text += f"\nCluster connected.\n"
            text += f"Nodes: {cluster_summary['node_count']} ({cluster_summary['nodes']['Ready']} Ready)\n"
            text += f"Pods: {cluster_summary['pod_count']} ({cluster_summary['pods']['Running']} Running, {cluster_summary['pods']['Failed']} Failed)\n"
            text += f"PVCs: {cluster_summary['pvc_count']} ({cluster_summary['pvcs']['Bound']} Bound)\n"
            text += f"Deployments: {cluster_summary['deployment_count']}\n"
            text += f"\nAsk me anything about your cluster!"
        else:
            text += f"\nNo kubeconfig found. Upload a kubeconfig file to enable cluster-aware answers.\n"
            text += f"You can still ask general questions."
        return self.text(args, text)

    def message(self, role, content):
        self.messages.append({"role": role, "content":content})

    def stream(self, args, lines):
        out = ""
        sock = None
        host = args.get("STREAM_HOST", "")
        port = int(args.get("STREAM_PORT") or "0")
        if host and port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host,port))
        try:
            for line in lines:
                if sock is not None:
                    sock.sendall(json.dumps(line).encode("utf-8"))
                    time.sleep(self.rate)
                out += line
        except Exception as e:
            print(e)
            print("interrupted")
        if sock is not None:
            sock.close()
        return out

    def _ask(self, inp):
        self.messages.append({"role": "user", "content": inp})
        print(f"context: {len(self.context)} instruct: {len(self.instruct)} messages: {len(self.messages)} cluster_ctx: {bool(self.cluster_ctx)}")
        stream = self.ai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content

    def ask(self, args, inp):
        st = self._ask(inp)
        return self.stream(args, st)

    def _text(self, lines):
        for line in lines.splitlines():
            for word in line.split(" "):
                yield word+" "
            yield "\n"

    def text(self, args, lines):
        return self.stream(args, self._text(lines))
