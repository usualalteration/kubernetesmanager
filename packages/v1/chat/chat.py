import llm
import cluster
import traceback


def main(args, ctx=None):
    inp = args.get("input", "")

    # Ensure AI config is available in args (from generated wrapper params)
    if ctx:
        for key in ("AI_BASE_URL", "AI_API_KEY", "AI_CHAT_MODEL"):
            if key not in args and hasattr(ctx, key):
                args[key] = getattr(ctx, key)

    # Fetch live cluster data from Kubernetes (if kubeconfig exists in S3)
    cluster_ctx = ""
    cluster_summary = None
    if ctx:
        result = cluster.fetch_cluster_summary(ctx)
        if result.get("ok"):
            cluster_ctx = result.get("context", "")
            cluster_summary = result.get("summary")
        else:
            cluster_ctx = ""
            cluster_summary = None
            print(f"cluster fetch failed: {result.get('error', '')}")

    try:
        ai = llm.LLM(args, cluster_ctx)

        if inp == "":
            out = ai.welcome(args, cluster_summary)
        else:
            out = ai.ask(args, inp)

    except Exception as e:
        traceback.print_exc()
        out = f"Error: {str(e)}\n"

    return {"output": out, "streaming": True}
