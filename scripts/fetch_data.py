
import json
import os
import urllib.request
from pathlib import Path

url = os.environ["DASHBOARD_API_URL"]

if (
    not url.startswith("https://script.google.com/macros/s/")
    or not url.endswith("/exec")
):
    raise ValueError("Invalid Apps Script URL")

request = urllib.request.Request(
    url,
    headers={"User-Agent": "HoangLietDashboard/3.0"}
)

with urllib.request.urlopen(request, timeout=45) as response:
    payload = json.load(response)

# Support both V2 and V3
if (
    payload.get("status") == "success"
    and isinstance(payload.get("data"), dict)
):
    source = payload["data"]
    api_version = "2"

elif (
    payload.get("version") == "3.0.0"
    and isinstance(payload.get("overview"), dict)
):
    source = payload["overview"]
    api_version = "3"

else:
    raise ValueError("Unexpected API response")

keys = ("students", "classes", "staff", "campuses")

clean = {key: source[key] for key in keys}

if any(
    type(value) is not int or value < 0
    for value in clean.values()
):
    raise ValueError("Invalid statistics")

output = {
    "school": "THCS Hoàng Liệt",
    "schoolYear": "2026-2027",
    "updatedAt": payload.get("updatedAt"),
    "data": clean
}

Path("public").mkdir(exist_ok=True)

Path("public/dashboard.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("API version:", api_version)
print("Validated dashboard data:", clean)
