"""Fetch and validate public Dashboard V3.2 aggregates for GitHub Pages."""
import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

URL = os.environ['DASHBOARD_API_V32_URL'].strip()
p = urlsplit(URL)
if (p.scheme != 'https' or p.netloc != 'script.google.com' or
        not p.path.startswith('/macros/s/') or not p.path.endswith('/exec') or
        parse_qs(p.query).get('v') != ['32']):
    raise ValueError('Invalid V3.2 Apps Script URL')

req = urllib.request.Request(URL, headers={'User-Agent': 'HoangLietDashboard/3.2'})
with urllib.request.urlopen(req, timeout=60) as response:
    payload = json.load(response)
if payload.get('version') != '3.2.0' or payload.get('status') != 'success':
    raise ValueError('Unexpected V3.2 API response')

source = payload.get('data')
if not isinstance(source, dict):
    raise ValueError('Missing dashboard data')
keys = ('students', 'classes', 'staff', 'campuses')
clean = {key: source.get(key) for key in keys}
if any(type(v) is not int or v < 0 for v in clean.values()):
    raise ValueError('Invalid dashboard statistics')
expected = {'students': 6110, 'classes': 121, 'staff': 227, 'campuses': 2}
if clean != expected:
    raise ValueError(f'Dashboard totals differ from approved baseline: {clean}')
checks = payload.get('v32Checks')
if not isinstance(checks, dict):
    raise ValueError('Missing V3.2 checks')
for key, value in {'studentRows': 6110, 'staffRows': 227,
                   'studentDifference': 0, 'staffDifference': 0,
                   'classCount': 121}.items():
    if type(checks.get(key)) is not int or checks[key] != value:
        raise ValueError(f'V3.2 validation failed: {key}')

settings = payload.get('settings')
if not isinstance(settings, dict):
    raise ValueError('Missing CAI_DAT settings')
for key in ('schoolName', 'schoolYear'):
    if not isinstance(settings.get(key), str) or not settings[key].strip():
        raise ValueError(f'Invalid setting: {key}')
campuses = settings.get('campuses')
if not isinstance(campuses, list) or len(campuses) != 2:
    raise ValueError('Expected two campuses in settings')
public_campuses = []
for c in campuses:
    if not isinstance(c, dict) or any(not isinstance(c.get(k), str) or not c[k].strip()
                                          for k in ('name', 'address')):
        raise ValueError('Invalid campus setting')
    public_campuses.append({'name': c['name'].strip(), 'address': c['address'].strip()})

# Strict allowlist: publish only these aggregate dimensions.
def groups(parent, key, label_key, count_key, *, allow_empty=False):
    items = parent.get(key)
    if not isinstance(items, list) or (not items and not allow_empty):
        raise ValueError(f'Missing or empty aggregate: {key}')
    result = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f'Invalid row in {key}')
        label, count = item.get(label_key), item.get(count_key)
        if not isinstance(label, str) or not label.strip() or type(count) is not int or count < 0:
            raise ValueError(f'Invalid label/count in {key}')
        result.append({'label': label.strip(), 'count': count})
    return result

student_source = payload.get('students')
personnel_source = payload.get('personnel')
if not isinstance(student_source, dict) or not isinstance(personnel_source, dict):
    raise ValueError('Missing aggregate sections')
students = {
    'byGrade': groups(student_source, 'byGrade', 'khối', 'danh sách'),
    'byCampus': groups(student_source, 'byCampus', 'cơ sở', 'danh sách'),
    'byGender': groups(student_source, 'byGender', 'label', 'count'),
}
personnel = {
    k: groups(personnel_source, k, 'label', 'count')
    for k in ('byPosition', 'bySubject', 'byQualification', 'byContract', 'byCampus')
}
for section, key, total in ((students, 'byGrade', clean['students']),
                            (students, 'byCampus', clean['students']),
                            (students, 'byGender', clean['students']),
                            (personnel, 'byPosition', clean['staff'])):
    actual = sum(x['count'] for x in section[key])
    if actual != total:
        raise ValueError(f'{key} totals {actual}, expected {total}')

output = {
    'school': settings['schoolName'].strip(),
    'schoolYear': settings['schoolYear'].strip(),
    'updatedAt': payload.get('updatedAt'),
    'data': clean,
    'settings': {'schoolName': settings['schoolName'].strip(),
                 'schoolYear': settings['schoolYear'].strip(),
                 'campuses': public_campuses},
    'students': students,
    'personnel': personnel,
}
path = Path('public/dashboard.json')
path.parent.mkdir(parents=True, exist_ok=True)
# Write only after all validations have passed.
path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: Dashboard V3.2 API and settings validated')
print('Published approved totals:', clean)
print('Published aggregate groups:', list(students), list(personnel))
