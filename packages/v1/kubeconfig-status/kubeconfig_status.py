"""
Kubeconfig management: list, delete, set-active.

GET  → list all kubeconfigs in S3, mark the active one.
POST → action=delete (key=...)       : remove a kubeconfig.
       action=set-active (key=...)   : mark a kubeconfig as active.
"""

import json
import yaml

ACTIVE_MARKER = "kubeconfigs/.active"


def list_kubeconfigs(ctx):
    """List all kubeconfigs in S3 with metadata. Returns (items, active_key)."""
    response = ctx.S3_CLIENT.list_objects_v2(
        Bucket=ctx.S3_DATA, Prefix="kubeconfigs/"
    )
    contents = response.get("Contents", [])

    # Read active marker
    active_key = ""
    try:
        marker = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=ACTIVE_MARKER)
        active_key = marker["Body"].read().decode("utf-8").strip()
    except Exception:
        active_key = ""

    items = []
    for obj in contents:
        key = obj["Key"]
        # Skip the marker file itself
        if key == ACTIVE_MARKER:
            continue
        # Only process files (not directory prefixes)
        if key.endswith("/"):
            continue

        # Extract filename from path: kubeconfigs/<uuid>/<filename>
        parts = key.split("/")
        filename = parts[-1] if parts else key

        items.append(
            {
                "key": key,
                "filename": filename,
                "uploaded_at": str(obj["LastModified"]),
                "size": obj.get("Size", 0),
                "active": key == active_key,
            }
        )

    # Sort by uploaded_at descending (newest first)
    items.sort(key=lambda x: x["uploaded_at"], reverse=True)

    # If no active marker, the first (newest) is implicitly active
    if not active_key and items:
        items[0]["active"] = True

    return items, active_key


def validate_kubeconfig(ctx, key):
    """Validate that the S3 object is a valid kubeconfig. Returns dict or None."""
    try:
        obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=key)
        raw = obj["Body"].read().decode("utf-8")
        config = yaml.safe_load(raw)
        if not config or "apiVersion" not in config:
            return None
        if "clusters" not in config or "users" not in config or "contexts" not in config:
            return None
        return {
            "filename": key.split("/")[-1],
            "clusters": len(config.get("clusters", [])),
            "contexts": len(config.get("contexts", [])),
            "users": len(config.get("users", [])),
            "current_context": config.get("current-context", ""),
        }
    except Exception:
        return None


def get_active_config(ctx):
    """
    Return the active kubeconfig dict and its S3 key.
    Reads .active marker; falls back to most recent by LastModified.
    Returns (key, config_dict) or (None, None).
    """
    if not ctx or not hasattr(ctx, "S3_CLIENT") or not ctx.S3_CLIENT:
        return None, None

    # Try active marker first
    active_key = ""
    try:
        marker = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=ACTIVE_MARKER)
        active_key = marker["Body"].read().decode("utf-8").strip()
    except Exception:
        pass

    if active_key:
        try:
            obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=active_key)
            raw = obj["Body"].read().decode("utf-8")
            config = yaml.safe_load(raw)
            return active_key, config
        except Exception:
            pass

    # Fallback: most recent
    try:
        response = ctx.S3_CLIENT.list_objects_v2(
            Bucket=ctx.S3_DATA, Prefix="kubeconfigs/"
        )
        contents = [
            o for o in response.get("Contents", []) if o["Key"] != ACTIVE_MARKER
        ]
        if not contents:
            return None, None
        latest = max(contents, key=lambda x: x["LastModified"])
        obj = ctx.S3_CLIENT.get_object(Bucket=ctx.S3_DATA, Key=latest["Key"])
        raw = obj["Body"].read().decode("utf-8")
        config = yaml.safe_load(raw)
        return latest["Key"], config
    except Exception:
        return None, None


def main(args, ctx=None):
    if not ctx or not hasattr(ctx, "S3_CLIENT") or not ctx.S3_CLIENT:
        return {"ok": False, "error": "S3 storage not configured"}

    import os as _os

    method = (args.get("__ow_method") or args.get("method") or "GET").upper()
    action = (args.get("action") or "").lower()

    # --- POST actions ---
    if method == "POST":
        key = args.get("key", "")

        if action == "delete":
            if not key:
                return {"ok": False, "error": "Missing 'key' parameter"}
            try:
                # Check if this key is the active one
                active_key = ""
                try:
                    marker = ctx.S3_CLIENT.get_object(
                        Bucket=ctx.S3_DATA, Key=ACTIVE_MARKER
                    )
                    active_key = marker["Body"].read().decode("utf-8").strip()
                except Exception:
                    pass

                ctx.S3_CLIENT.delete_object(Bucket=ctx.S3_DATA, Key=key)

                # Clear active marker if we deleted the active config
                if key == active_key:
                    try:
                        ctx.S3_CLIENT.delete_object(
                            Bucket=ctx.S3_DATA, Key=ACTIVE_MARKER
                        )
                    except Exception:
                        pass

                return {"ok": True, "deleted": key}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        if action == "set-active":
            if not key:
                return {"ok": False, "error": "Missing 'key' parameter"}
            try:
                # Verify the key exists
                ctx.S3_CLIENT.head_object(Bucket=ctx.S3_DATA, Key=key)
                # Write active marker
                ctx.S3_CLIENT.put_object(
                    Bucket=ctx.S3_DATA,
                    Key=ACTIVE_MARKER,
                    Body=key.encode("utf-8"),
                    ContentType="text/plain",
                )
                return {"ok": True, "active": key}
            except Exception as e:
                return {"ok": False, "error": f"Config not found: {e}"}

        return {"ok": False, "error": f"Unknown action: {action}"}

    # --- GET: list all ---
    try:
        items, active_key = list_kubeconfigs(ctx)
        configured = len(items) > 0

        # Build active config details
        active_info = None
        effective_active_key = active_key
        if not effective_active_key and items:
            effective_active_key = items[0]["key"]

        if effective_active_key:
            info = validate_kubeconfig(ctx, effective_active_key)
            if info:
                active_info = info

        return {
            "ok": True,
            "configured": configured,
            "error": "",
            "items": items,
            "count": len(items),
            "active_key": effective_active_key,
            "active_info": active_info,
        }
    except Exception as e:
        return {"ok": False, "configured": False, "error": str(e), "items": []}
