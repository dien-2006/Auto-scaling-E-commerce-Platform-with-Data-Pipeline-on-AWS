"""Bounded secret-pattern scan of Git-visible files; never prints matched values."""

import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
files = (
    subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    .decode()
    .split("\0")
)
patterns = {
    "aws-access-id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
}
issues = []
checked = 0
for name in sorted(set(files)):
    if not name:
        continue
    path = root / name
    if path.name.startswith(".env") and path.name != ".env.example":
        issues.append({"file": name, "rule": "git-visible-private-env"})
    if not path.is_file() or path.stat().st_size > 2_000_000:
        continue
    data = path.read_bytes()
    checked += 1
    for rule, pattern in patterns.items():
        if pattern.search(data):
            issues.append({"file": name, "rule": rule})
assert not issues, issues
print(f"PASS {checked} Git-visible files: no configured secret patterns/private env files")
print("Limited pattern scan; not a complete secret or Git-history audit")
