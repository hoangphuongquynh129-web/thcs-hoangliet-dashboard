public_indicators = {}
for key in ('disability', 'policy'):
    entry = indicators.get(key)
    if not isinstance(entry, dict) or type(entry.get('count')) is not int:
        raise ValueError(f'Missing/invalid indicator count: {key}')
    count = entry['count']
    if not 0 <= count <= clean['students']:
        raise ValueError(f'Indicator out of range: {key}')
    public_indicators[key] = {'count': count}
students['indicators'] = public_indicators

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

# Validate grade x campus cross-tab against both published marginal totals.
raw_cross = student_source.get('byGradeCampus')
if not isinstance(raw_cross, list) or len(raw_cross) != 4:
    raise ValueError('Expected four grade-campus rows')
by_grade = {r['label']: r['count'] for r in students['byGrade']}
by_campus = {r['label']: r['count'] for r in students['byCampus']}
if len(by_grade) != 4 or len(by_campus) != 2:
    raise ValueError('Duplicate or missing grade/campus labels')
expected_grades = {f'Khối {n}' for n in range(6, 10)}
if set(by_grade) != expected_grades or set(by_campus) != {'Trụ sở chính', 'Phân hiệu'}:
    raise ValueError('Unexpected grade or campus labels')
cross = []
seen = set()
for item in raw_cross:
    if not isinstance(item, dict):
        raise ValueError('Invalid grade-campus row')
    label = item.get('label')
    if not isinstance(label, str) or label not in expected_grades or label in seen:
        raise ValueError(f'Unexpected/duplicate grade-campus label: {label}')
    seen.add(label)
    values = [item.get(k) for k in ('mainCampus', 'branchCampus', 'total')]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError(f'Invalid grade-campus counts: {label}')
    main, branch, total = values
    if main + branch != total or total != by_grade[label]:
        raise ValueError(f'Grade-campus totals do not reconcile: {label}')
    cross.append({'label': label, 'mainCampus': main,
                  'branchCampus': branch, 'total': total})
if seen != expected_grades:
    raise ValueError('Missing grade-campus row')
cross.sort(key=lambda r: int(r['label'].split()[-1]))
if sum(r['mainCampus'] for r in cross) != by_campus['Trụ sở chính']:
    raise ValueError('Main campus total does not reconcile')
if sum(r['branchCampus'] for r in cross) != by_campus['Phân hiệu']:
    raise ValueError('Branch campus total does not reconcile')
if sum(r['total'] for r in cross) != clean['students']:
    raise ValueError('Grade-campus grand total does not reconcile')
students['byGradeCampus'] = cross

# Party membership is sourced only from the dedicated DANG_VIEN sheet aggregate.
party_source = personnel_source.get('partyMembers')
if not isinstance(party_source, dict) or type(party_source.get('total')) is not int:
    raise ValueError('Missing/invalid personnel.partyMembers')
party_total = party_source['total']
if not 0 <= party_total <= clean['staff']:
    raise ValueError('Party member count exceeds staff total')
party_campuses = groups(party_source, 'byCampus', 'label', 'count')
party_branches = groups(party_source, 'byBranch', 'label', 'count')
if {x['label'] for x in party_campuses} != {'Trụ sở chính', 'Phân hiệu'}:
    raise ValueError('Unexpected party campus labels')
if sum(x['count'] for x in party_campuses) != party_total:
    raise ValueError('Party campus counts do not reconcile')
if sum(x['count'] for x in party_branches) != party_total:
    raise ValueError('Party branch counts do not reconcile')
committee = groups(party_source, 'byCommittee', 'label', 'count')
expected_roles = {'Bí thư Đảng ủy', 'Phó Bí thư Đảng ủy', 'Đảng ủy viên'}
if {r['label'] for r in committee} != expected_roles or len(committee) != 3:
    raise ValueError('Unexpected BCH role labels')
committee_total = party_source.get('committeeTotal')
if type(committee_total) is not int or committee_total != sum(r['count'] for r in committee) or committee_total > party_total:
    raise ValueError('BCH role counts do not reconcile')
personnel['partyMembers'] = {'total': party_total,
                             'byCampus': party_campuses,
                             'byBranch': party_branches,
                             'byCommittee': committee,
                             'committeeTotal': committee_total}

output = {
    'version': '3.2.0',
    'status': 'success',
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
path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
if not path.is_file() or path.stat().st_size == 0:
    raise RuntimeError('Failed to create public/dashboard.json')
print(f'Created {path.resolve()} ({path.stat().st_size} bytes)')
print('PASS: Dashboard V3.2 API, settings, grade-campus and student indicators validated')
print('Published approved totals:', clean)
print('Published student indicators:', public_indicators)
print('Published aggregate groups:', list(students), list(personnel))
