"""Validate V3.2 Apps Script response without publishing student/staff data."""
import json
import os
import urllib.request
from pathlib import Path

url = os.environ['DASHBOARD_API_V32_URL'].strip()
if not (url.startswith('https://script.google.com/macros/s/') and '/exec' in url):
    raise ValueError('Invalid Apps Script deployment URL')
if 'v=32' not in url:
    raise ValueError('V3.2 URL must include ?v=32 (or &v=32)')
request = urllib.request.Request(url, headers={'User-Agent': 'HoangLietDashboard-V32-Test/1.0'})
with urllib.request.urlopen(request, timeout=60) as response:
    payload = json.load(response)
if payload.get('version') != '3.2.0' or payload.get('status') != 'success':
    raise ValueError('Unexpected API version/status')
expected = {'students': 6110, 'classes': 121, 'staff': 227, 'campuses': 2}
actual = payload.get('data', {})
for key, value in expected.items():
    if actual.get(key) != value:
        raise ValueError(f'{key}: expected {value}, got {actual.get(key)}')
checks = payload.get('v32Checks', {})
for key, value in {'studentRows': 6110, 'staffRows': 227, 'studentDifference': 0, 'staffDifference': 0, 'classCount': 121}.items():
    if checks.get(key) != value:
        raise ValueError(f'{key}: expected {value}, got {checks.get(key)}')
for name in ('students', 'personnel'):
    if not isinstance(payload.get(name), dict):
        raise ValueError(f'Missing group {name}')
# Private artifact: contains only diagnostic counts, not the complete API payload.
report = {
    'version': payload['version'],
    'status': payload['status'],
    'data': actual,
    'v32Checks': checks,
    'studentGroupNames': list(payload['students']),
    'personnelGroupNames': list(payload['personnel']),
}
Path('v32-test-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: V3.2 API validated; diagnostic report generated. No public JSON updated.')
