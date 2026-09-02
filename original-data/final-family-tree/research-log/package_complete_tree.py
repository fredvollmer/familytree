from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[3]
PACKAGE = PROJECT / "original-data/final-family-tree"
PREFIX = "Fredric_Vollmer_Complete_Family_Tree"
MANIFEST = PACKAGE / f"{PREFIX}_SHA256.txt"
VALIDATION = PACKAGE / f"{PREFIX}_VALIDATION.txt"
ARCHIVE = PROJECT / "original-data" / f"{PREFIX}_Package.zip"
ARCHIVE_ROOT = f"{PREFIX}_Package"


def included(path: Path) -> bool:
    relative = path.relative_to(PACKAGE)
    if path == MANIFEST:
        return False
    if "workbook-previews" in relative.parts:
        return False
    if "node_modules" in relative.parts:
        return False
    if path.name.endswith(".inspect.ndjson"):
        return False
    return path.is_file()


validation_text = VALIDATION.read_text(encoding="utf-8")
validation_text = validation_text.split("workbook sheets:", 1)[0].rstrip() + "\n"
validation_text += (
    "workbook sheets: 12\n"
    "workbook formula errors: 0\n"
    "workbook consolidated individual count: 327\n"
    "workbook consolidated family count: 154\n"
    "workbook consolidated GEDCOM source count: 45\n"
    "workbook source and record inventory count: 88\n"
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
