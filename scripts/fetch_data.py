import json, os, urllib.request
from pathlib import Path
url=os.environ['DASHBOARD_API_URL']
if not url.startswith('https://script.google.com/macros/s/') or not url.endswith('/exec'):
    raise ValueError('Invalid Apps Script URL')
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HoangLietDashboard/1.0'}),timeout=45) as response:
    data=json.load(response)
if data.get('status')!='success' or not isinstance(data.get('data'),dict):
    raise ValueError('Unexpected API response')
keys=('students','classes','staff','campuses')
clean={k:data['data'][k] for k in keys}
if any(type(v)!=int or v<0 for v in clean.values()):
    raise ValueError('Invalid statistics')
output={'school':'THCS Hoàng Liệt','schoolYear':'2026-2027','updatedAt':data.get('updatedAt'),'data':clean}
Path('public').mkdir(exist_ok=True)
Path('public/dashboard.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print('Validated dashboard data:',clean)
