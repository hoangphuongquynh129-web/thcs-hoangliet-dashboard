
import json
import os
import urllib.request
from pathlib import Path

url = os.environ["DASHBOARD_API_V31_URL"].strip()

if not (
    url.startswith("https://script.google.com/macros/s/")
    and url.endswith("/exec")
):
    raise ValueError("Invalid Apps Script URL")

request = urllib.request.Request(
    url,
    headers={"User-Agent": "HoangLietDashboard/3.1"}
)

with urllib.request.urlopen(request, timeout=45) as response:
    payload = json.load(response)

if payload.get("status") != "success":
    raise ValueError("API V3.1 returned an error")

source = payload.get("data")

if not isinstance(source, dict):
    raise ValueError("Missing overview data")

keys = ("students", "classes", "staff", "campuses")
overview = {key: source[key] for key in keys}

if any(type(v) is not int or v < 0 for v in overview.values()):
    raise ValueError("Invalid overview statistics")

students = payload.get("students", {})
personnel = payload.get("personnel", {})

if not isinstance(students, dict):
    raise ValueError("Invalid student statistics")

if not isinstance(personnel, dict):
    raise ValueError("Invalid personnel statistics")

allowed_student_groups = ("byGrade", "byCampus")
allowed_personnel_groups = (
    "byPosition",
    "bySubject",
    "byQualification",
    "byContract",
    "byCampus"
)

def approved_groups(source, names):
    result = {}
    for name in names:
        value = source.get(name, [])
        if not isinstance(value, list):
            raise ValueError("Invalid group: " + name)
        result[name] = value
    return result

output = {
    "school": "THCS Hoàng Liệt",
    "schoolYear": "2026-2027",
    "updatedAt": payload.get("updatedAt"),
    "data": overview,
    "students": approved_groups(
        students, allowed_student_groups
    ),
    "personnel": approved_groups(
        personnel, allowed_personnel_groups
    )
}

# Write to a separate test file
Path("public").mkdir(exist_ok=True)

Path("public/dashboard-v31-test.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("V3.1 overview:", overview)
print("Student groups:", list(output["students"]))
print("Personnel groups:", list(output["personnel"]))
print("V3.1 JSON generated successfully")

print("\n=== KIEM TRA DU LIEU CHI TIET ===")

for name, rows in output["students"].items():
    print("Hoc sinh -", name, ":", len(rows), "dong")
    if rows:
        print("  Mau:", json.dumps(rows[0], ensure_ascii=False))

for name, rows in output["personnel"].items():
    print("Nhan su -", name, ":", len(rows), "dong")
    if rows:
        print("  Mau:", json.dumps(rows[0], ensure_ascii=False))

print("=== KET THUC KIEM TRA ===")
