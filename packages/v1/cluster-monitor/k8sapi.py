"""Minimal Kubernetes REST client for Truk8s serverless actions.

The OpenServerless Python 3.12 runtime does not ship the official
``kubernetes`` client library, so this module implements the small subset
of the API the app needs using only the standard library and runtime-shipped
packages (``yaml``).

It parses a kubeconfig mapping directly and talks to the Kubernetes API
server over HTTPS:

- auth: bearer token (or tokenFile), client certificate (data or file),
  or basic auth (username/password)
- TLS: CA from inline ``certificate-authority-data`` (or file path),
  or ``insecure-skip-tls-verify``
- cross-namespace list operations with ``continue`` pagination
"""

import base64
import json
import os
import ssl
import tempfile
import urllib.error
import urllib.parse
import urllib.request

import yaml

ACTIVE_MARKER = "kubeconfigs/.active"


class KubeConfigError(Exception):
    """Raised when a kubeconfig cannot be parsed or is incomplete."""


class KubeApiError(Exception):
    """Raised when the Kubernetes API server returns an error."""

    def __init__(self, status, reason=""):
        self.status = status
        self.reason = reason
        super().__init__(
            "Kubernetes API error %s: %s" % (status, reason or "request failed")
        )


class KubeConfig:
    """Parsed kubeconfig: API server URL, auth header, and TLS context."""

    def __init__(self, server, auth_header, ssl_context):
        self.server = server
        self.auth_header = auth_header
        self.ssl_context = ssl_context


def _b64_decode(value):
    if value is None:
        return None
    raw = value if isinstance(value, bytes) else str(value).strip().encode("utf-8")
    try:
        return base64.b64decode(raw)
    except Exception:
        return None


def _materialize_temp(b64_value, suffix=""):
    """Write a base64 kubeconfig value to a temp file (certs need paths)."""
    data = _b64_decode(b64_value) or b""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return path


def _read_file(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (OSError, TypeError):
        return None


def _build_ssl_context(cluster_spec, user_spec, relaxed_hostname=False):
    ctx = ssl.create_default_context()

    if bool(cluster_spec.get("insecure-skip-tls-verify")):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    if relaxed_hostname:
        # A server override is in use: the certificate's SANs name the
        # original host (e.g. 127.0.0.1 from the machine that created the
        # kubeconfig). Verify the certificate chain against the kubeconfig
        # CA (verify_mode stays CERT_REQUIRED) but skip hostname matching.
        ctx.check_hostname = False

    ca_bytes = _b64_decode(cluster_spec.get("certificate-authority-data"))
    if ca_bytes is None:
        ca_bytes = _read_file(cluster_spec.get("certificate-authority") or "")
    if ca_bytes:
        try:
            ctx.load_verify_locations(cadata=ca_bytes.decode("utf-8", "replace"))
        except Exception as exc:
            print("k8sapi: warning: could not load CA data: %s" % exc)

    cert_path = None
    key_path = None
    temp_paths = []

    cert_data = user_spec.get("client-certificate-data")
    key_data = user_spec.get("client-key-data")
    cert_file = user_spec.get("client-certificate") or ""
    key_file = user_spec.get("client-key") or ""

    if cert_data:
        cert_path = _materialize_temp(cert_data, ".pem")
        temp_paths.append(cert_path)
    elif cert_file and os.path.exists(cert_file):
        cert_path = cert_file
    if key_data:
        key_path = _materialize_temp(key_data, ".key")
        temp_paths.append(key_path)
    elif key_file and os.path.exists(key_file):
        key_path = key_file

    if cert_path and key_path:
        try:
            ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        except Exception as exc:
            print("k8sapi: warning: could not load client cert: %s" % exc)
        finally:
            for path in temp_paths:
                try:
                    os.unlink(path)
                except OSError:
                    pass
    else:
        for path in temp_paths:
            try:
                os.unlink(path)
            except OSError:
                pass
    return ctx


def _build_auth_header(user_spec):
    token = str(user_spec.get("token") or "").strip()
    if not token:
        token_file = user_spec.get("tokenFile") or ""
        if token_file and os.path.exists(token_file):
            data = _read_file(token_file)
            if data:
                token = data.decode("utf-8", "replace").strip()
    if token:
        return "Bearer " + token

    username = str(user_spec.get("username") or "").strip()
    password = str(user_spec.get("password") or "").strip()
    if username:
        credentials = base64.b64encode(
            ("%s:%s" % (username, password)).encode("utf-8")
        ).decode("ascii")
        return "Basic " + credentials
    return ""


def _pick_entry(entries, name, label):
    entries = [e for e in (entries or []) if isinstance(e, dict)]
    if name:
        for entry in entries:
            if entry.get("name") == name:
                return entry
    if entries:
        return entries[0]
    raise KubeConfigError("no %s found in kubeconfig" % label)


def _normalize_override(override):
    """Normalize a server override into a full URL (or None)."""
    value = str(override or "").strip()
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if "://" not in value:
        return "https://" + value
    return value


def parse_kubeconfig(config_dict, server_override=None):
    """Parse a kubeconfig mapping into a :class:`KubeConfig`.

    ``server_override`` (optional) replaces the cluster's API server URL —
    used when the kubeconfig points at a machine-local address (e.g.
    127.0.0.1) that is unreachable from the action runtime.
    """
    if not isinstance(config_dict, dict) or not config_dict:
        raise KubeConfigError("kubeconfig is empty or not a mapping")

    current = str(config_dict.get("current-context") or "").strip()
    contexts = [c for c in (config_dict.get("contexts") or []) if isinstance(c, dict)]
    context = None
    if current:
        for entry in contexts:
            if entry.get("name") == current:
                context = entry
                break
    if context is None and contexts:
        context = contexts[0]
    if context is None:
        raise KubeConfigError("no context found in kubeconfig")

    context_spec = context.get("context") or {}
    cluster_name = str(context_spec.get("cluster") or "").strip()
    user_name = str(context_spec.get("user") or "").strip()

    cluster_entry = _pick_entry(config_dict.get("clusters"), cluster_name, "cluster")
    user_entry = _pick_entry(config_dict.get("users"), user_name, "user")

    cluster_spec = cluster_entry.get("cluster") or {}
    user_spec = user_entry.get("user") or {}
    server = str(cluster_spec.get("server") or "").strip()
    if not server:
        raise KubeConfigError("cluster has no server URL")

    override = _normalize_override(server_override)
    relaxed_hostname = False
    if override and override.rstrip("/") != server.rstrip("/"):
        print("k8sapi: server override active: %s -> %s" % (server, override))
        relaxed_hostname = True
        server = override

    return KubeConfig(
        server,
        _build_auth_header(user_spec),
        _build_ssl_context(cluster_spec, user_spec, relaxed_hostname=relaxed_hostname),
    )


def request(config, path, params=None, timeout=30):
    """GET a Kubernetes API path and return the parsed JSON document."""
    url = config.server.rstrip("/") + path
    if params:
        query = urllib.parse.urlencode(params)
        url += ("&" if "?" in url else "?") + query

    headers = {
        "Accept": "application/json",
        "User-Agent": "truk8s/1.0",
        "Content-Type": "application/json",
    }
    if config.auth_header:
        headers["Authorization"] = config.auth_header

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, context=config.ssl_context, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8") or "null")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        reason = body
        try:
            detail = json.loads(body)
            if isinstance(detail, dict):
                reason = str(detail.get("message") or detail.get("reason") or body)[:300]
        except Exception:
            reason = reason[:300]
        raise KubeApiError(exc.code, reason) from exc
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        raise KubeApiError(0, "cannot reach %s: %s" % (config.server, exc)) from exc


def list_all(config, path, page_limit=500, max_items=20000, timeout=30):
    """List all items at a collection path, following ``continue`` pagination."""
    items = []
    continue_token = None
    while True:
        params = {"limit": str(page_limit)}
        if continue_token:
            params["continue"] = continue_token
        data = request(config, path, params=params, timeout=timeout)
        if not isinstance(data, dict):
            break
        items.extend(data.get("items") or [])
        continue_token = (data.get("metadata") or {}).get("continue")
        if not continue_token or len(items) >= max_items:
            break
    return items


SETTINGS_FILE = "k8s_settings.json"


def load_settings():
    """Load the optional ``k8s_settings.json`` sitting next to this module.

    Supported keys:
      - ``server_override``: alternate API server URL for when the
        kubeconfig's server (e.g. 127.0.0.1) is only reachable on the
        machine that created the kubeconfig. Accepts a full URL or
        ``host:port`` (https assumed).

    Returns ``{}`` when the file is absent or unreadable.
    """
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SETTINGS_FILE)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class K8sClient:
    """Convenience wrapper around a parsed kubeconfig."""

    def __init__(self, config_dict, settings=None):
        if not isinstance(settings, dict):
            settings = load_settings()
        self.config = parse_kubeconfig(
            config_dict, server_override=settings.get("server_override")
        )

    def get(self, path, params=None, timeout=30):
        return request(self.config, path, params=params, timeout=timeout)

    def list_all(self, path, timeout=30, page_limit=500):
        return list_all(self.config, path, timeout=timeout, page_limit=page_limit)

    def fetch_cluster(self, timeout=30):
        """Return pods, pvcs, nodes, and deployments as plain JSON dicts."""
        pods = self.list_all("/api/v1/pods", timeout=timeout)
        pvcs = self.list_all("/api/v1/persistentvolumeclaims", timeout=timeout)
        nodes = self.list_all("/api/v1/nodes", timeout=timeout)
        deployments = self.list_all("/apis/apps/v1/deployments", timeout=timeout)
        return {"pods": pods, "pvcs": pvcs, "nodes": nodes, "deployments": deployments}


def _is_missing_key(exc):
    """True when an S3 GetObject failure means "object does not exist"."""
    code = ""
    try:
        code = str(exc.response.get("Error", {}).get("Code", ""))
    except Exception:
        pass
    return code in ("NoSuchKey", "NoSuchEntity")


def load_kubeconfig_from_s3(ctx):
    """Load the active (or most recent) kubeconfig from the app's S3 bucket.

    Reads the ``kubeconfigs/.active`` marker first; falls back to the most
    recently uploaded object under ``kubeconfigs/``. Returns a triple
    ``(key, config_dict, error)``: on success ``error`` is None; on failure
    ``key`` and ``config_dict`` are None and ``error`` describes the cause
    (None when the bucket simply holds no kubeconfig objects).
    """
    s3 = getattr(ctx, "S3_CLIENT", None) if ctx else None
    bucket = getattr(ctx, "S3_DATA", "") if ctx else ""
    if not s3 or not bucket:
        return None, None, "S3 client or bucket not configured"

    active_error = None
    active_key = ""
    try:
        marker = s3.get_object(Bucket=bucket, Key=ACTIVE_MARKER)
        active_key = marker["Body"].read().decode("utf-8").strip()
    except Exception as exc:
        if not _is_missing_key(exc):
            active_error = f"active marker unreadable: {exc}"

    if active_key:
        try:
            obj = s3.get_object(Bucket=bucket, Key=active_key)
            raw = obj["Body"].read().decode("utf-8")
            config = yaml.safe_load(raw)
            if isinstance(config, dict):
                return active_key, config, None
            active_error = f"stored kubeconfig {active_key!r} is not a YAML mapping"
        except Exception as exc:
            active_error = f"active kubeconfig {active_key!r} unreadable: {exc}"

    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix="kubeconfigs/")
        contents = [
            o
            for o in response.get("Contents", [])
            if isinstance(o, dict)
            and o.get("Key") != ACTIVE_MARKER
            and not str(o.get("Key", "")).endswith("/")
        ]
        if not contents:
            detail = f" (active marker error: {active_error})" if active_error else ""
            return None, None, f"no kubeconfig objects under kubeconfigs/ in bucket {bucket!r}{detail}"
        latest = max(contents, key=lambda o: str(o.get("LastModified") or ""))
        obj = s3.get_object(Bucket=bucket, Key=latest["Key"])
        raw = obj["Body"].read().decode("utf-8")
        config = yaml.safe_load(raw)
        if isinstance(config, dict):
            return latest["Key"], config, None
        return None, None, f"stored kubeconfig {latest['Key']!r} is not a YAML mapping"
    except Exception as exc:
        print("k8sapi: S3 kubeconfig listing failed: %s" % exc)
        detail = f" (marker: {active_error})" if active_error else ""
        return None, None, f"S3 list/read failed: {exc}{detail}"

