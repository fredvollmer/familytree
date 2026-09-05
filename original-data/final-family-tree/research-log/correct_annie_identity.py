"""Apply the owner's 5 September 2026 identity correction; retain prior inputs as evidence."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Fredric_Vollmer_Complete_Family_Tree'
path = ROOT / f'{PREFIX}_Canonical_Data.json'
data = json.loads(path.read_text())
note = ('Owner correction, 5 September 2026: Annie is Arianna Lynn Fischer, '
        'Fredric Muller Vollmer’s wife. I175 was an erroneous duplicate with an '
        'incorrect Vollmer surname and sister/child relationship; it is retired. '
        'Retain I356, her documented Fischer parents, and spouse family F156.')
data['people'] = [p for p in data['people'] if p['individual_id'] != 'I175']
annie = next(p for p in data['people'] if p['individual_id'] == 'I356')
annie['name'] = 'Arianna Lynn “Annie” Fischer'
if note not in annie['notes']:
    annie['notes'] += ' | ' + note
family = next(f for f in data['families'] if f['family_id'] == 'F095')
family['children_ids'] = ';'.join(i for i in family['children_ids'].split(';') if i != 'I175')
family['notes'] = 'Jan is Fredric’s biological mother; Henry is his father. Annie Fischer is Fredric’s wife, not a child of this family.'
data['metadata']['updated'] = '2026-09-05'
if not any(c['topic'] == 'Annie Fischer identity' for c in data['corrections']):
    data['corrections'].append({'topic': 'Annie Fischer identity', 'corrected': note})
source = next(s for s in data['sources'] if s['source_id'] == 'S49')
if note not in source['notes']:
    source['notes'] += ' ' + note
gedpath = ROOT / f'{PREFIX}.ged'
ged = gedpath.read_text()
ged = re.sub(r'^0 @I175@ INDI\n.*?(?=^0 )', '', ged, flags=re.M | re.S)
ged = ged.replace('1 CHIL @I175@\n', '')
ged = ged.replace('1 NAME Arianna Lynn /Fischer/\n', '1 NAME Arianna Lynn /Fischer/\n2 NICK Annie\n') if '2 NICK Annie\n' not in ged else ged
ged = ged.replace("Jan is Fredric and Arianna's biological mother; Henry is recorded as their father in the recovered canonical package.", family['notes'])
if note not in ged:
    ged = ged.replace('0 @S49@ SOUR\n', '0 @S49@ SOUR\n1 NOTE ' + note + '\n')
gedpath.write_text(ged)
assert '@I175@' not in ged
assert '1 WIFE @I356@' in ged

def write_csv(path, rows, fields):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

for suffix, key in [('People', 'people'), ('Families', 'families')]:
    write_csv(ROOT / f'{PREFIX}_{suffix}.csv', data[key], list(data[key][0]))
for suffix in ['Vital_Date_Coverage', 'Occupation_Coverage', 'Source_Inventory']:
    p = ROOT / f'{PREFIX}_{suffix}.csv'
    with p.open() as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    removed = [r for r in rows if r.get('individual_id') == 'I175']
    rows = [r for r in rows if r.get('individual_id') != 'I175']
    for r in rows:
        if r.get('individual_id') == 'I356': r['name'] = annie['name']
        if r.get('source_id') == 'S49': r['notes'] = source['notes']
    write_csv(p, rows, fields)
    if suffix != 'Source_Inventory':
        meta = data['metadata']['vital_date_coverage' if suffix.startswith('Vital') else 'occupation_coverage']
        meta['people'] = len(data['people'])
        for r in removed:
            status = r.get('overall_status', r.get('status'))
            key = {'withheld—living/private':'living_private', 'not researched—privacy limited':'privacy_limited'}.get(status, status)
            if key in meta: meta[key] -= 1
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
ledger = ROOT / f'{PREFIX}_Sources.md'
if '## Annie Fischer identity correction' not in ledger.read_text():
    with ledger.open('a') as f:
        f.write('\n## Annie Fischer identity correction — 5 September 2026\n\n' + note + '\n\nSource: direct owner statement in the Family Tree project; supplements S49. Earlier maternal-tree inputs are preserved as superseded evidence, not current relationships. No marriage date or new parentage was inferred.\n')
print(f'Validated Annie identity: {len(data["people"])} people, {len(data["families"])} families; I175 retired; I356 spouse of I001.')
