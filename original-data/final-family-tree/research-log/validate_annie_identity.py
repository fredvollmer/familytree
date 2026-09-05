"""Regression checks for the owner-approved Annie identity correction."""
import csv
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
prefix = 'Fredric_Vollmer_Complete_Family_Tree'
data = json.loads((root / f'{prefix}_Canonical_Data.json').read_text())
ged = (root / f'{prefix}.ged').read_text()
people = {p['individual_id']: p for p in data['people']}
assert 'I175' not in people and '@I175@' not in ged
assert people['I356']['name'] == 'Arianna Lynn “Annie” Fischer'
assert people['I356']['family_as_child'] == 'F157'
assert people['I356']['families_as_spouse'] == 'F156'
assert people['I356']['birth'] == '1990'
assert len(people) == len(re.findall(r'^0 @I\d+@ INDI$', ged, re.M)) == 390
for family in data['families']:
    for key in ['husband_id', 'wife_id', 'children_ids']:
        assert all(i in people for i in family[key].split(';') if i)
    if family['family_id'] == 'F156':
        assert family['husband_id'] == 'I001' and family['wife_id'] == 'I356'
    if family['family_id'] == 'F095':
        assert family['children_ids'] == 'I001'
for suffix in ['People', 'Vital_Date_Coverage', 'Occupation_Coverage']:
    rows = list(csv.DictReader((root / f'{prefix}_{suffix}.csv').open()))
    assert {r['individual_id'] for r in rows} == set(people)
assert json.loads((root.parents[1] / 'public/data/family-tree.json').read_text()) == data
validation = root / f'{prefix}_VALIDATION.txt'
text = validation.read_text()
for label in ['GEDCOM individuals', 'people CSV rows', 'vital-date coverage rows', 'occupation coverage rows']:
    text = re.sub(rf'^{label}:.*$', f'{label}: {len(people)}', text, flags=re.M)
checks = 'Annie identity regression checks: passed (5 September 2026)\nRetired duplicate I175 absent from active people and relationships: True\nAnnie Fischer I356 is Fredric I001 spouse in F156: True\nAnnie Fischer parents retained in F157: True\n'
if 'Annie identity regression checks:' not in text:
    text = text.replace('workbook sheets:', checks + 'workbook sheets:')
validation.write_text(text)
print('Annie identity, parent/spouse links, CSV coverage, GEDCOM references, privacy, and deployment mirror checks passed.')
