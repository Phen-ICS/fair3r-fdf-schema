#!/usr/bin/env python3
"""
Daily liveness check for the external APIs referenced in fdf_schema.json.

Usage:
    python tools/check_apis.py

For each entry in the top-level "apis" block, sends a minimal GET request
and reports whether the host responded. An API counts as DOWN only on a
connection error, timeout, DNS failure, or 5xx response — a 4xx response
still means the service is alive (the probe query just isn't a valid one),
so it's reported as UP. Entries whose "url" is a relative path (e.g.
xenbase_mutant_lines, which is proxied through the CKAN backend rather than
called directly) are skipped, since there's no standalone host to probe.

A failing attempt is retried a couple of times with a short delay before
being declared DOWN, since public research APIs (Ensembl in particular)
occasionally have a one-off slow request rather than a real outage.

Exits non-zero if any API is DOWN, so a scheduled GitHub Actions run fails
and surfaces the problem.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "fdf_schema.json"

TIMEOUT_SECONDS = 15
USER_AGENT = "fair3r-fdf-schema-api-check/1.0"
PROBE_VALUE = "test"
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


def build_probe_url(entry: dict) -> str:
    # Path template (e.g. .../overlap/region/{species}/{region}) — fill each
    # placeholder with a generic value so the request still reaches the real
    # route handler instead of an arbitrary/unknown path on the host.
    url = re.sub(r"\{[^}]+\}", PROBE_VALUE, entry["url"])

    params = {}
    query_param = entry.get("query_param")
    if query_param:
        params[query_param] = PROBE_VALUE
    for key, value in (entry.get("extra_params") or {}).items():
        if isinstance(value, (str, int, float)):
            params[key] = value

    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urllib.parse.urlencode(params)}"


def check_one(name: str, entry: dict) -> tuple[str, int | None, str | None]:
    """Returns (status, http_status, error_message). status is one of UP/DOWN/SKIPPED."""
    url = entry["url"]
    if not url.startswith("http"):
        return "SKIPPED", None, "relative/internal endpoint, not directly probeable"

    probe_url = build_probe_url(entry)
    headers = {"User-Agent": USER_AGENT, **(entry.get("headers") or {})}

    last_status, last_http_status, last_error = "DOWN", None, "unknown error"
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        request = urllib.request.Request(probe_url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return "UP", response.status, None
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                return "UP", exc.code, None
            last_status, last_http_status, last_error = "DOWN", exc.code, f"server error {exc.code}"
        except urllib.error.URLError as exc:
            last_status, last_http_status, last_error = "DOWN", None, str(exc.reason)
        except TimeoutError:
            last_status, last_http_status, last_error = "DOWN", None, "timed out"

        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)

    return last_status, last_http_status, f"{last_error} (after {RETRY_ATTEMPTS} attempts)"


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    apis = schema["apis"]

    down = []
    for name, entry in apis.items():
        status, http_status, error = check_one(name, entry)
        detail = f"HTTP {http_status}" if http_status else error
        print(f"[{status}] {name} ({entry.get('label', name)}) - {detail}")
        if status == "DOWN":
            down.append(name)

    if down:
        print(f"\n{len(down)} API(s) DOWN: {', '.join(down)}", file=sys.stderr)
        return 1

    print("\nAll checked APIs are up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
