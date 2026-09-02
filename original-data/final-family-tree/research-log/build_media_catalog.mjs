import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {
  auditDate,
  evidenceRecords,
  externalEvidenceChecks,
  externalPortraits,
} from './media-audit-data.mjs';

const root = path.resolve(import.meta.dirname, '..');
const canonicalPath = path.join(
  root,
  'Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json',
);
const publicPath = path.resolve(root, '../../public/data/family-tree.json');
const mediaPath = path.join(
  root,
  'Fredric_Vollmer_Complete_Family_Tree_Media_Audit.json',
);
const csvPath = path.join(
  root,
  'Fredric_Vollmer_Complete_Family_Tree_Media_Inventory.csv',
);
const gedcomPath = path.join(root, 'Fredric_Vollmer_Complete_Family_Tree.ged');
const derivedPath = path.join(
  root,
  'Fredric_Vollmer_Complete_Family_Tree_Derived_Assets.json',
);

const data = JSON.parse(fs.readFileSync(canonicalPath, 'utf8'));
const peopleById = new Map(
  data.people.map((person) => [person.individual_id, person]),
);
const evidence = evidenceRecords.map((item, index) => ({
  evidence_id: `E${String(index + 1).padStart(3, '0')}`,
  media_type:
    path.extname(item.filename).toLowerCase() === '.pdf' ? 'pdf' : 'image',
  file_path: `records/${item.filename}`,
  ...item,
}));

for (const item of evidence) {
  const full = path.join(root, item.file_path);
  if (!fs.existsSync(full))
    throw new Error(`Missing evidence file: ${item.file_path}`);
  for (const personId of item.person_ids) {
    if (!peopleById.has(personId))
      throw new Error(`Unknown person ${personId} in ${item.evidence_id}`);
  }
  for (const preview of item.preview_paths) {
    if (!fs.existsSync(path.join(root, preview)))
      throw new Error(`Missing preview: ${preview}`);
  }
  item.sha256 = crypto
    .createHash('sha256')
    .update(fs.readFileSync(full))
    .digest('hex');
}

const evidenceByPerson = new Map();
for (const item of evidence) {
  for (const personId of item.person_ids) {
    evidenceByPerson.set(personId, [
      ...(evidenceByPerson.get(personId) ?? []),
      item.evidence_id,
    ]);
  }
}

const people = data.people.map((person) => {
  const portrait = externalPortraits[person.individual_id];
  const privateLiving =
    /\b(?:Living person|Potentially living|Living dates)\b/i.test(person.notes);
  return {
    individual_id: person.individual_id,
    name: person.name,
    portrait_status:
      portrait?.status ??
      (privateLiving ? 'privacy_withheld' : 'no_verified_photo_archived'),
    portrait_path: '',
    portrait_source_name: portrait?.source_name ?? '',
    portrait_source_url: portrait?.source_url ?? '',
    portrait_source_refs: portrait?.source_refs ?? [],
    portrait_rights:
      portrait?.rights ??
      (privateLiving ? 'Living-person privacy applies.' : ''),
    portrait_note:
      portrait?.note ??
      (privateLiving
        ? 'No portrait is displayed because the person is living.'
        : 'No verified portrait was present in the repository or canonical evidence ledger at audit time.'),
    evidence_ids: evidenceByPerson.get(person.individual_id) ?? [],
  };
});

const media = {
  metadata: {
    audited: auditDate,
    people_audited: people.length,
    portraits_archived: people.filter((person) => person.portrait_path).length,
    external_photo_pages: people.filter(
      (person) => person.portrait_status === 'external_photo_page',
    ).length,
    privacy_withheld: people.filter(
      (person) => person.portrait_status === 'privacy_withheld',
    ).length,
    no_verified_photo_archived: people.filter(
      (person) => person.portrait_status === 'no_verified_photo_archived',
    ).length,
    evidence_files: evidence.length,
    evidence_images: evidence.filter((item) => item.media_type === 'image')
      .length,
    evidence_pdfs: evidence.filter((item) => item.media_type === 'pdf').length,
    pdf_preview_images: evidence
      .filter((item) => item.media_type === 'pdf')
      .flatMap((item) => item.preview_paths).length,
    policy:
      'Use only verified person images; preserve living-person privacy; retain external or rights-restricted photos as links rather than copied files; attach evidence through explicit person mappings and retain exclusions as controls.',
  },
  people,
  evidence,
  external_evidence_checks: externalEvidenceChecks,
};

data.metadata.updated = auditDate;
data.metadata.media_audit = media.metadata;
data.media = media;
if (
  !data.provenance.some(
    (item) => item.thread_title === 'Photo and evidence media audit',
  )
) {
  data.provenance.push({
    thread_title: 'Photo and evidence media audit',
    role: 'repository-wide person-photo availability audit, exact person-to-record mappings, preserved evidence attachment catalog, PDF page previews, and Ancestry/Newspapers.com access controls',
  });
}
const canonicalJson = `${JSON.stringify(data, null, 2)}\n`;
fs.writeFileSync(canonicalPath, canonicalJson);
fs.writeFileSync(publicPath, canonicalJson);
fs.writeFileSync(mediaPath, `${JSON.stringify(media, null, 2)}\n`);
fs.writeFileSync(
  path.resolve(root, '../../public/data/media-audit.json'),
  `${JSON.stringify(media, null, 2)}\n`,
);

const csvEscape = (value) => {
  const text = Array.isArray(value) ? value.join(';') : String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};
const csvRows = [
  [
    'row_type',
    'id',
    'name_or_title',
    'portrait_status_or_evidence_status',
    'portrait_or_file_path',
    'external_url',
    'person_ids',
    'evidence_ids',
    'source_refs',
    'ledger_refs',
    'preview_paths',
    'rights_or_note',
  ],
  ...people.map((person) => [
    'person',
    person.individual_id,
    person.name,
    person.portrait_status,
    person.portrait_path,
    person.portrait_source_url,
    person.individual_id,
    person.evidence_ids,
    person.portrait_source_refs,
    '',
    '',
    `${person.portrait_rights} ${person.portrait_note}`.trim(),
  ]),
  ...evidence.map((item) => [
    'evidence',
    item.evidence_id,
    item.title,
    item.status,
    item.file_path,
    '',
    item.person_ids,
    '',
    item.canonical_source_refs,
    item.ledger_refs,
    item.preview_paths,
    item.note,
  ]),
  ...externalEvidenceChecks.map((item, index) => [
    'external_check',
    `XWEB${String(index + 1).padStart(2, '0')}`,
    item.platform,
    item.status,
    '',
    item.url,
    item.person_id,
    '',
    '',
    '',
    '',
    item.note,
  ]),
];
fs.writeFileSync(
  csvPath,
  `${csvRows.map((row) => row.map(csvEscape).join(',')).join('\n')}\n`,
);

let gedcom = fs.readFileSync(gedcomPath, 'utf8');
const mimeForm = (filename) => (filename.endsWith('.pdf') ? 'PDF' : 'JPEG');
const attachmentLines = (items) =>
  items.flatMap((item) => [
    '1 OBJE',
    `2 FILE records/${item.filename}`,
    `2 FORM ${mimeForm(item.filename)}`,
    `2 TITL ${item.title}`,
    `2 NOTE ${item.status === 'excluded_identity_control' ? 'Excluded identity-control evidence' : 'Preserved evidence'}; see media inventory for exact person links and interpretation.`,
  ]);
const attachToSource = (sourceId, items) => {
  if (
    !items.length ||
    items.every((item) => gedcom.includes(`2 FILE records/${item.filename}`))
  )
    return;
  const marker = `0 @${sourceId}@ SOUR`;
  const start = gedcom.indexOf(marker);
  if (start < 0) throw new Error(`Missing GEDCOM source ${sourceId}`);
  const next = gedcom.indexOf('\n0 ', start + marker.length);
  const insertAt = next < 0 ? gedcom.length : next;
  const missing = items.filter(
    (item) => !gedcom.includes(`2 FILE records/${item.filename}`),
  );
  gedcom = `${gedcom.slice(0, insertAt)}\n${attachmentLines(missing).join('\n')}${gedcom.slice(insertAt)}`;
};
attachToSource(
  'S26',
  evidence.filter((item) => !item.canonical_source_refs.includes('S32')),
);
attachToSource(
  'S32',
  evidence.filter((item) => item.canonical_source_refs.includes('S32')),
);
fs.writeFileSync(gedcomPath, gedcom.endsWith('\n') ? gedcom : `${gedcom}\n`);

const derived = JSON.parse(fs.readFileSync(derivedPath, 'utf8'));
derived.updated = auditDate;
const mediaAsset = {
  asset_id: 'family-media-audit',
  title: 'Person-photo coverage and preserved evidence-media catalog',
  status: 'approved',
  primary_data:
    'original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Media_Audit.json',
  inventory:
    'original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Media_Inventory.csv',
  evidence_directory: 'original-data/final-family-tree/records',
  preview_directory: 'original-data/final-family-tree/record-previews',
  generated: auditDate,
  counts: media.metadata,
  interpretation:
    'Portrait status records verified availability, not likeness inference. Evidence mappings are explicit; excluded identity controls remain visibly marked and do not alter relationships.',
};
const existingIndex = derived.assets.findIndex(
  (item) => item.asset_id === mediaAsset.asset_id,
);
if (existingIndex >= 0) derived.assets[existingIndex] = mediaAsset;
else derived.assets.push(mediaAsset);
fs.writeFileSync(derivedPath, `${JSON.stringify(derived, null, 2)}\n`);

console.log(JSON.stringify(media.metadata, null, 2));
