import json
import os
import urllib.request
from pathlib import Path

url = os.environ['DASHBOARD_API_V31_URL'].strip()
if not (url.startswith('https://script.google.com/macros/s/') and url.endswith('/exec')):
    raise ValueError('Invalid Apps Script URL')
request = urllib.request.Request(url, headers={'User-Agent':'HoangLietDashboard/3.1'})
with urllib.request.urlopen(request, timeout=45) as response:
    payload = json.load(response)
if payload.get('status') != 'success' or not isinstance(payload.get('data'), dict):
    raise ValueError('Unexpected API response')
source = payload['data']
keys = ('students','classes','staff','campuses')
clean = {key:source[key] for key in keys}
if any(type(value) is not int or value < 0 for value in clean.values()):
    raise ValueError('Invalid statistics')
if clean['students'] != 6110 or clean['classes'] != 121 or clean['staff'] != 227 or clean['campuses'] != 2:
    raise ValueError('Unexpected baseline statistics; review before publication')
output = {'school':'THCS Hoàng Liệt','schoolYear':'2026-2027','updatedAt':payload.get('updatedAt'),'data':clean}
Path('public').mkdir(exist_ok=True)
Path('public/dashboard.json').write_text(json.dumps(output, ensure_ascii=False, indent=2),encoding='utf-8')
print('Validated V3.1 overview:',clean)
