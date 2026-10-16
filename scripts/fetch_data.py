
"""Fetch approved Dashboard V3.2 statistics for GitHub Pages."""

import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

url = os.environ["DASHBOARD_API_V32_URL"].strip()

parsed = urlsplit(url)
if (
    parsed.scheme != "https"
    or parsed.netloc != "script.google.com"
    or not parsed.path.startswith("/macros/s/")
    or not parsed.path.endswith("/exec")
    or parse_qs(parsed.query).get("v") != ["32"]
):
    raise ValueError("Invalid V3.2 Apps Script URL")

request = urllib.request.Request(
    url,
    headers={"User-Agent": "HoangLietDashboard/3.2"}
)

with urllib.request.urlopen(request, timeout=60) as response:
    payload = json.load(response)

if (
    payload.get("version") != "3.2.0"
    or payload.get("status") != "success"
):
    raise ValueError("Unexpected V3.2 API response")

source = payload.get("data")
if not isinstance(source, dict):
    raise ValueError("Missing dashboard data")

keys = ("students", "classes", "staff", "campuses")
clean = {key: source.get(key) for key in keys}

if any(type(value) is not int or value < 0 for value in clean.values()):
    raise ValueError("Invalid dashboard statistics")

expected = {
    "students": 6110,
    "classes": 121,
    "staff": 227,
    "campuses": 2
}

if clean != expected:
    raise ValueError(
        f"Dashboard totals differ from approved baseline: {clean}"
    )

checks = payload.get("v32Checks", {})
if not isinstance(checks, dict):
    raise ValueError("Missing V3.2 checks")

for key, value in {
    "studentRows": 6110,
    "staffRows": 227,
    "studentDifference": 0,
    "staffDifference": 0,
    "classCount": 121
}.items():
    if checks.get(key) != value:
        raise ValueError(f"V3.2 validation failed: {key}")

# Preserve the JSON structure used by the existing website.
output = {
    "school": payload.get("school", "THCS Hoàng Liệt"),
    "schoolYear": payload.get("schoolYear", "2026-2027"),
    "updatedAt": payload.get("updatedAt"),
    "data": clean
}

# Do not publish detailed or sensitive groups at this stage.
path = Path("public/dashboard.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("PASS: Dashboard V3.2 API validated")
print("Published approved totals:", clean)
