"""Query OSV for pinned backend packages; reports package names, never credentials."""

import json
import tomllib
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
packages = tomllib.loads((root / "backend/uv.lock").read_text(encoding="utf-8"))["package"]
packages = [p for p in packages if "registry" in p.get("source", {})]
payload = {
    "queries": [
        {"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]}
        for p in packages
    ]
}
request = urllib.request.Request(
    "https://api.osv.dev/v1/querybatch",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    results = json.load(response)["results"]
assert len(results) == len(packages)
findings = [
    {"package": p["name"], "version": p["version"], "ids": [v["id"] for v in r.get("vulns", [])]}
    for p, r in zip(packages, results, strict=True)
    if r.get("vulns")
]
print(json.dumps({"source": "OSV", "packages": len(packages), "findings": findings}))
if findings:
    raise SystemExit(1)
