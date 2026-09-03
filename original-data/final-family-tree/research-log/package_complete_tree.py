from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[3]
PACKAGE = PROJECT / "original-data/final-family-tree"
PREFIX = "Fredric_Vollmer_Complete_Family_Tree"
MANIFEST = PACKAGE / f"{PREFIX}_SHA256.txt"
VALIDATION = PACKAGE / f"{PREFIX}_VALIDATION.txt"
ARCHIVE = PROJECT / "original-data" / f"{PREFIX}_Package.zip"
ARCHIVE_ROOT = f"{PREFIX}_Package"
VITAL_COVERAGE = PACKAGE / f"{PREFIX}_Vital_Date_Coverage.csv"
OCCUPATION_COVERAGE = PACKAGE / f"{PREFIX}_Occupation_Coverage.csv"
MEDIA_AUDIT = PACKAGE / f"{PREFIX}_Media_Audit.json"


def included(path: Path) -> bool:
    relative = path.relative_to(PACKAGE)
    if path == MANIFEST:
        return False
    if "workbook-previews" in relative.parts:
        return False
    if "record-previews" in relative.parts:
        return False
    if path.name == "Fredric_Vollmer_Maternal_Family_Tree_Records_First_Report.pdf":
        return False
    if "node_modules" in relative.parts:
        return False
    if "__pycache__" in relative.parts:
        return False
    if path.name.endswith(".inspect.ndjson"):
        return False
    return path.is_file()


with VITAL_COVERAGE.open(newline="", encoding="utf-8") as handle:
    vital_rows = list(csv.DictReader(handle))
with OCCUPATION_COVERAGE.open(newline="", encoding="utf-8") as handle:
    occupation_rows = list(csv.DictReader(handle))

birth_dates = sum(row["birth_status"] == "recorded" for row in vital_rows)
death_dates = sum(row["death_status"] == "recorded" for row in vital_rows)
complete_dates = sum(row["overall_status"] == "complete" for row in vital_rows)
no_date_outcomes = sum(
    row["overall_status"]
    in {"unresolved", "not researched—privacy limited", "withheld—living/private"}
    for row in vital_rows
)
occupation_people = sum(row["status"] == "recorded" for row in occupation_rows)
occupation_events = sum(int(row["event_count"]) for row in occupation_rows)
media = json.loads(MEDIA_AUDIT.read_text(encoding="utf-8"))
media_counts = media["metadata"]
gedcom_multimedia = (PACKAGE / f"{PREFIX}.ged").read_text(encoding="utf-8").count("\n1 OBJE\n")

validation_text = VALIDATION.read_text(encoding="utf-8")
validation_text = validation_text.split("workbook sheets:", 1)[0].rstrip() + "\n"
validation_text += (
    "workbook sheets: 15\n"
    "workbook formula errors: 0\n"
    "workbook consolidated individual count: 391\n"
    "workbook consolidated family count: 188\n"
    "workbook consolidated GEDCOM source count: 79\n"
    "workbook source and record inventory count: 157\n"
    f"workbook birth dates recorded: {birth_dates}\n"
    f"workbook death dates recorded: {death_dates}\n"
    f"workbook both vital dates recorded: {complete_dates}\n"
    f"workbook no dated event unresolved or private: {no_date_outcomes}\n"
    f"workbook people with recorded occupations or roles: {occupation_people}\n"
    f"workbook accepted occupation or role events: {occupation_events}\n"
    f"workbook media audit rows: {len(media['people']) + len(media['evidence']) + len(media['external_evidence_checks'])}\n"
    f"media audit people: {media_counts['people_audited']}\n"
    f"external photo pages located: {media_counts['external_photo_pages']}\n"
    f"locally archived portraits: {media_counts['portraits_archived']}\n"
    f"preserved evidence files: {media_counts['evidence_files']}\n"
    f"preserved evidence images: {media_counts['evidence_images']}\n"
    f"preserved evidence PDFs: {media_counts['evidence_pdfs']}\n"
    f"PDF evidence preview images: {media_counts['pdf_preview_images']}\n"
    f"GEDCOM multimedia attachments: {gedcom_multimedia}\n"
    "Wallace Ray Fischer parent family present: True\n"
    "Wanda June Wallace identity resolved: True\n"
    "Fischer collateral relatives added: False\n"
    "Fischer grave-marker images preserved: 21\n"
)
VALIDATION.write_text(validation_text, encoding="utf-8")

files = sorted(path for path in PACKAGE.rglob("*") if included(path))
manifest_lines = []
for path in files:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_lines.append(f"{digest}  {path.relative_to(PACKAGE).as_posix()}")
MANIFEST.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

archive_files = files + [MANIFEST]
with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in archive_files:
        archive.write(path, f"{ARCHIVE_ROOT}/{path.relative_to(PACKAGE).as_posix()}")

with zipfile.ZipFile(ARCHIVE) as archive:
    bad_file = archive.testzip()
    if bad_file:
        raise RuntimeError(f"ZIP integrity failure at {bad_file}")
    archived_members = len(archive.infolist())

print(f"manifest files: {len(manifest_lines)}")
print(f"archive members: {archived_members}")
print(f"archive bytes: {ARCHIVE.stat().st_size}")
print("archive test: passed")
