import os
import json
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import urllib.error

UPSTREAM_API_URL = os.environ.get("UPSTREAM_API_URL", "").strip()

def normalize_account(item, params):
    if not isinstance(item, dict):
        return None

    uid = item.get("uid") or item.get("external_uid") or item.get("id")
    account_id = item.get("account_id") or item.get("external_id") or item.get("id") or uid

    if uid is None or account_id is None:
        return None

    return {
        "uid": str(uid).replace("-", "").strip(),
        "account_id": str(account_id).replace("-", "").strip(),
        "password": str(
            item.get("password")
            or item.get("pass")
            or item.get("passwd")
            or ""
        ).strip(),
        "name": str(
            item.get("name")
            or item.get("nickname")
            or params.get("name", [""])[0]
        ).strip(),
        "region": str(
            item.get("region")
            or item.get("country_code")
            or params.get("region", [""])[0]
        ).strip(),
    }

def normalize_response(data, params):
    # Lipzx.py expects: {"accounts": [ {...} ], ...}
    if isinstance(data, dict):
        raw_accounts = data.get("accounts")
        if isinstance(raw_accounts, list):
            source = raw_accounts
        elif isinstance(raw_accounts, dict):
            source = [raw_accounts]
        else:
            source = [data]
    elif isinstance(data, list):
        source = data
    else:
        source = []

    accounts = []
    for item in source:
        normalized = normalize_account(item, params)
        if normalized:
            accounts.append(normalized)

    requested = 1
    try:
        requested = max(1, int(params.get("count", ["1"])[0]))
    except Exception:
        pass

    return {
        "accounts": accounts,
        "attempts_made": data.get("attempts_made", 1) if isinstance(data, dict) else 1,
        "rare_count": data.get("rare_count", 0) if isinstance(data, dict) else 0,
        "success": bool(accounts),
        "total_created": len(accounts),
        "total_requested": requested,
    }

class handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)

        if not UPSTREAM_API_URL:
            self.send_json({
                "accounts": [],
                "attempts_made": 0,
                "rare_count": 0,
                "success": False,
                "total_created": 0,
                "total_requested": int(params.get("count", ["1"])[0] or 1),
                "error": "UPSTREAM_API_URL is not configured"
            }, 500)
            return

        query = []
        for key in ("name", "count", "region", "password_prefix", "ghost", "detect_rare"):
            if key in params:
                query.append(
                    urllib.parse.quote(key, safe="") + "=" +
                    urllib.parse.quote(params[key][0], safe="")
                )

        url = UPSTREAM_API_URL
        separator = "&" if "?" in url else "?"
        url = url + (separator + "&".join(query) if query else "")

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Lipzx-API-Adapter/1.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                data = json.loads(raw.decode("utf-8"))
            self.send_json(normalize_response(data, params))
        except urllib.error.HTTPError as e:
            self.send_json({
                "accounts": [],
                "attempts_made": 1,
                "rare_count": 0,
                "success": False,
                "total_created": 0,
                "total_requested": int(params.get("count", ["1"])[0] or 1),
                "error": f"upstream_http_{e.code}"
            }, 502)
        except Exception as e:
            self.send_json({
                "accounts": [],
                "attempts_made": 1,
                "rare_count": 0,
                "success": False,
                "total_created": 0,
                "total_requested": int(params.get("count", ["1"])[0] or 1),
                "error": "upstream_unavailable"
            }, 502)
