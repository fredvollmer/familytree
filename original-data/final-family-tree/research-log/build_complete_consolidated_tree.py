from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[3]
BASE = PROJECT / "original-data/final-family-tree"
INPUT_LEDGERS = BASE / "input-ledgers"
CANON_GED = BASE / "Fredric_Vollmer_Maternal_Family_Tree_Records_First.ged"
CANON_JSON = BASE / "Fredric_Vollmer_Maternal_Family_Tree_Records_First_Canonical_Data.json"
DIRECT_CSV = INPUT_LEDGERS / "Vollmer-Marsh-people.csv"
EXTENDED_CSV = INPUT_LEDGERS / "Extended-family-people.csv"
DIRECT_SOURCES = INPUT_LEDGERS / "Vollmer-Marsh-sources.md"
EXTENDED_SOURCES = INPUT_LEDGERS / "Extended-family-sources.md"
RECORDS = BASE / "records"

PREFIX = "Fredric_Vollmer_Complete_Family_Tree"
OUT_GED = BASE / f"{PREFIX}.ged"
OUT_JSON = BASE / f"{PREFIX}_Canonical_Data.json"
OUT_PEOPLE = BASE / f"{PREFIX}_People.csv"
OUT_FAMILIES = BASE / f"{PREFIX}_Families.csv"
OUT_SOURCES = BASE / f"{PREFIX}_Sources.md"
OUT_SOURCE_INVENTORY = BASE / f"{PREFIX}_Source_Inventory.csv"
OUT_AUDIT = BASE / f"{PREFIX}_Merge_Audit.md"
OUT_VALIDATION = BASE / f"{PREFIX}_VALIDATION.txt"
OUT_README = BASE / "README.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blocks(text: str, record_type: str) -> dict[str, list[str]]:
    pattern = rf"^0 (@[A-Z]+\d+@) {record_type}\n(.*?)(?=^0 )"
    found = {}
    for match in re.finditer(pattern, text, re.M | re.S):
        found[match.group(1)] = [f"0 {match.group(1)} {record_type}"] + match.group(2).rstrip("\n").splitlines()
    return found


def first_value(lines: list[str], tag: str) -> str:
    prefix = f"1 {tag} "
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix):]
    return ""


def clean_name(ged_name: str) -> str:
    return re.sub(r"\s+", " ", ged_name.replace("/", "")).strip()


def ged_name(name: str) -> str:
    name = name.strip()
    if not name:
        return "Unknown"
    suffix = ""
    match = re.search(r"\s+(Jr\.?|Sr\.?|II|III)$", name)
    if match:
        suffix = " " + match.group(1)
        name = name[: match.start()].strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0] + suffix
    surname = parts[-1]
    given = " ".join(parts[:-1])
    return f"{given} /{surname}/{suffix}"


def strip_level1(lines: list[str], tags: set[str]) -> list[str]:
    out = [lines[0]]
    skip = False
    for line in lines[1:]:
        level_match = re.match(r"^(\d+)\s+([A-Z_]+)", line)
        if not level_match:
            if not skip:
                out.append(line)
            continue
        level = int(level_match.group(1))
        tag = level_match.group(2)
        if level == 1:
            skip = tag in tags
        if not skip:
            out.append(line)
    return out


def set_level1(lines: list[str], tag: str, value: str) -> list[str]:
    lines = strip_level1(lines, {tag})
    if value:
        lines.insert(1, f"1 {tag} {value}")
    return lines


def add_unique(lines: list[str], line: str) -> None:
    if line not in lines:
        lines.append(line)


def parse_date_place(value: str) -> tuple[str, str, str]:
    value = value.strip()
    if not value:
        return "", "", ""
    parts = [part.strip() for part in value.split(";", 1)]
    date_text = parts[0]
    place = parts[1] if len(parts) == 2 else ""
    original = value
    date_text = re.sub(r"\(.*?\)", "", date_text).strip()
    date_text = date_text.replace("-", "–")
    if not date_text and place:
        return "", place, ""
    qualifier = ""
    lower = date_text.lower()
    if lower.startswith("about "):
        qualifier = "ABT "
        date_text = date_text[6:]
    elif lower.startswith("before "):
        qualifier = "BEF "
        date_text = date_text[7:]
    elif lower.startswith("after "):
        qualifier = "AFT "
        date_text = date_text[6:]
    if "–" in date_text or "/" in date_text or " in " in lower:
        return "", "", original
    month_map = {m.title(): m.upper() for m in "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}
    tokens = date_text.split()
    tokens = [month_map.get(token.title(), token) for token in tokens]
    if not any(re.fullmatch(r"\d{4}", token) for token in tokens):
        return "", "", original
    return qualifier + " ".join(tokens), place, ""


def set_event(lines: list[str], tag: str, raw: str) -> list[str]:
    date, place, fallback = parse_date_place(raw)
    if not raw:
        return lines
    lines = strip_level1(lines, {tag})
    event = [f"1 {tag}"]
    if date:
        event.append(f"2 DATE {date}")
    if place:
        event.append(f"2 PLAC {place}")
    if fallback:
        event.append(f"2 NOTE As reported: {fallback}")
    lines.extend(event)
    return lines


def parse_family(lines: list[str]) -> dict:
    return {
        "husb": first_value(lines, "HUSB"),
        "wife": first_value(lines, "WIFE"),
        "children": [line.split(maxsplit=2)[2] for line in lines if line.startswith("1 CHIL ")],
        "notes": [line[7:] for line in lines if line.startswith("1 NOTE ")],
        "marriage_date": "",
        "marriage_place": "",
    }


ged_text = CANON_GED.read_text(encoding="utf-8", errors="replace")
individuals = blocks(ged_text, "INDI")
source_blocks = blocks(ged_text, "SOUR")
canonical_families = [parse_family(lines) for lines in blocks(ged_text, "FAM").values()]
direct_rows = read_csv(DIRECT_CSV)
extended_rows = read_csv(EXTENDED_CSV)
canonical_json = json.loads(CANON_JSON.read_text(encoding="utf-8"))

max_individual = max(int(iid.strip("@I")) for iid in individuals)


def next_iid() -> str:
    global max_individual
    max_individual += 1
    return f"@I{max_individual:03d}@"


local_to_ged: dict[str, str] = {
    "EXISTING-FREDRIC-MULLER-VOLLMER": "@I001@",
    "EXISTING-HENRY-RICHARD-VOLLMER": "@I176@",
    "JAN-MULLER": "@I002@",
    "BRUCE-MULLER": "@I177@",
    "AJMUL-1925": "@I003@",
    "ARMC-1927": "@I004@",
    "AHMUL-1896": "@I005@",
    "EAL-1897": "@I006@",
    "CEMCC-1896": "@I007@",
    "ESMCC-1903": "@I008@",
    "CAM-1866": "@I009@",
    "HKM-1870": "@I010@",
    "EEL-1863": "@I013@",
    "MOL-1865": "@I014@",
    "CEMCCSR-1862": "@I114@",
    "MMMCC-1874": "@I115@",
    "IBS-1858": "@I130@",
    "LAR-1873": "@I131@",
    "MGMCH-1920": "@I178@",
    "JLMS-1932": "@I183@",
    "PMCC-1930": "@I193@",
    "CEMCCJR-1939": "@I200@",
    "GIMCC-1941": "@I202@",
}

for row in direct_rows:
    local_to_ged.setdefault(row["person_id"], next_iid())
for row in extended_rows:
    local_to_ged.setdefault(row["person_id"], next_iid())

father_ids = set()
mother_ids = set()
for row in direct_rows:
    if row["father_id"]:
        father_ids.add(row["father_id"])
    if row["mother_id"]:
        mother_ids.add(row["mother_id"])
for row in extended_rows:
    if row["father_ref"]:
        father_ids.add(row["father_ref"])
    if row["mother_ref"]:
        mother_ids.add(row["mother_ref"])


def inferred_sex(local_id: str) -> str:
    if local_id in father_ids and local_id not in mother_ids:
        return "M"
    if local_id in mother_ids and local_id not in father_ids:
        return "F"
    return "U"


def new_person(iid: str, local_id: str, name: str, birth: str, death: str, notes: list[str], source: str) -> list[str]:
    lines = [f"0 {iid} INDI", f"1 NAME {ged_name(name)}", f"1 SEX {inferred_sex(local_id)}"]
    lines = set_event(lines, "BIRT", birth)
    lines = set_event(lines, "DEAT", death)
    for note in notes:
        if note:
            lines.append(f"1 NOTE {note}")
    lines.append(f"1 REFN {local_id}")
    lines.append(f"1 SOUR {source}")
    return lines


for row in direct_rows:
    iid = local_to_ged[row["person_id"]]
    if iid not in individuals:
        individuals[iid] = new_person(
            iid,
            row["person_id"],
            row["preferred_name"],
            row["birth"],
            row["death"],
            [f"Confidence: {row['certainty']}.", row["scope_note"]],
            "@S26@",
        )

for row in extended_rows:
    iid = local_to_ged[row["person_id"]]
    if iid not in individuals:
        individuals[iid] = new_person(
            iid,
            row["person_id"],
            row["preferred_name"],
            row["birth"],
            row["death"],
            [row["relationship_to_focus"], f"Confidence: {row['certainty']}.", row["scope_note"]],
            "@S27@",
        )
    else:
        add_unique(individuals[iid], f"1 REFN {row['person_id']}")
        add_unique(individuals[iid], "1 SOUR @S27@")


def ensure_person_update(iid: str, *, name: str | None = None, sex: str | None = None,
                         birth: str | None = None, death: str | None = None,
                         notes: list[str] | None = None, source: str | None = None) -> None:
    lines = individuals[iid]
    if name is not None:
        lines = set_level1(lines, "NAME", ged_name(name))
    if sex is not None:
        lines = set_level1(lines, "SEX", sex)
    if birth is not None:
        lines = set_event(lines, "BIRT", birth)
    if death is not None:
        lines = set_event(lines, "DEAT", death)
    for note in notes or []:
        add_unique(lines, f"1 NOTE {note}")
    if source:
        add_unique(lines, f"1 SOUR {source}")
    individuals[iid] = lines


ensure_person_update("@I176@", name="Henry Richard Vollmer", sex="M",
                     notes=["Henry is Fredric's father and Jan's spouse in this tree.",
                            "Owner-confirmed: Mary Alice Thoren was Henry's first wife, before Jan Muller Vollmer."],
                     source="@S28@")
ensure_person_update("@I002@", name="Jan Muller Vollmer", sex="F",
                     notes=["Owner-confirmed: Jan is Fredric's biological mother, not his stepmother.",
                            "Owner-confirmed: Jan is Chris Vollmer's stepmother, not his biological mother."],
                     source="@S28@")
ensure_person_update("@I178@", name="Mary Gene Muller Chaffee", sex="F",
                     birth="13 Apr 1920; Detroit, Wayne, Michigan", death="18 Aug 1995",
                     notes=["Historical marriage and draft records identify her husband as Elmer James Chaffee Jr."],
                     source="@S27@")
ensure_person_update("@I179@", name="Elmer James Chaffee Jr", sex="M",
                     birth="1 Oct 1918; Wayne County, Michigan",
                     notes=["The 1998 family chart used James; historical records give the fuller name Elmer James Chaffee Jr."],
                     source="@S27@")
ensure_person_update("@I182@", name="James Chaffee", sex="M",
                     notes=["The son's name is James; an earlier mistranscription has been removed."], source="@S29@")
ensure_person_update("@I183@", name="Jane Lee Muller Swick", sex="F",
                     birth="7 Nov 1932; Detroit, Wayne, Michigan",
                     death="7 Nov 2010; North Bend, Coos, Oregon", source="@S27@")
ensure_person_update("@I005@", birth="28 Nov 1896; Highland Falls, Orange, New York",
                     death="Nov 1966; Detroit, Wayne, Michigan", source="@S27@")
ensure_person_update("@I006@", name="Elma Anna Lee Muller", sex="F",
                     birth="14 Jan 1897; Michigan", death="26 Dec 1972; Detroit, Wayne, Michigan",
                     notes=["Birth conflict retained: adult/death records support 14 Jan 1897, while 1900 and 1910 childhood censuses imply Jan 1894."],
                     source="@S27@")
ensure_person_update("@I008@", name="Eloise Alcyone Slaughter McCormick", sex="F",
                     birth="25 Aug 1903; Alabama", death="10 Feb 1994; Los Angeles County, California",
                     notes=["Official California death index supports 25 Aug 1903-10 Feb 1994; the earlier compiled Agee date is retained only as conflicting secondary evidence."],
                     source="@S27@")
ensure_person_update(local_to_ged["CFV-1906"], name="Charles Frederic Vollmer", sex="M",
                     notes=["Owner-confirmed spelling: Frederic is Charles's middle name; Frederick is retained only as a record/index variant."],
                     source="@S30@")

# Remove the superseded mistranscription from all canonical notes.
for iid, lines in list(individuals.items()):
    individuals[iid] = [line.replace("Janet Chaffee", "superseded Chaffee transcription") for line in lines]

# Owner-confirmed recent-family correction. Chris's father is intentionally absent.
mary_alice_iid = next_iid()
chris_iid = next_iid()
william_thoren_iid = next_iid()
alice_gallaher_iid = next_iid()
individuals[mary_alice_iid] = [
    f"0 {mary_alice_iid} INDI",
    "1 NAME Mary Alice /Thoren/",
    "1 SEX F",
    "1 BIRT",
    "2 PLAC Port Townsend, Jefferson, Washington",
    "1 NOTE Owner-confirmed biological mother of Chris Vollmer and first wife of Henry Richard Vollmer, before Jan Muller Vollmer.",
    "1 NOTE Owner-confirmed birthplace: Port Townsend, Washington. Exact birth date omitted for privacy.",
    "1 NOTE The 1950 census identifies her as the daughter of William J. Thoren and Alice Gallaher Thoren.",
    "1 NOTE Potentially living; details are minimized.",
    "1 REFN OWNER-MARY-ALICE",
    "1 SOUR @S28@",
    "1 SOUR @S31@",
    "1 SOUR @S32@",
]
individuals[chris_iid] = [
    f"0 {chris_iid} INDI",
    "1 NAME Chris /Vollmer/",
    "1 SEX U",
    "1 NOTE Owner-confirmed child of Mary Alice and stepchild of Jan Muller Vollmer. Father not confirmed and intentionally left blank.",
    "1 REFN OWNER-CHRIS-VOLLMER",
    "1 ASSO @I002@",
    "2 RELA Stepmother",
    "1 SOUR @S28@",
]
individuals[william_thoren_iid] = [
    f"0 {william_thoren_iid} INDI",
    "1 NAME William J /Thoren/",
    "1 SEX M",
    "1 BIRT",
    "2 DATE ABT 1902",
    "2 PLAC Montana",
    "1 NOTE Called Bill in family memory. The 1950 census records him as age 48, born in Montana, and Mary Alice's father.",
    "1 REFN OWNER-WILLIAM-J-THOREN",
    "1 SOUR @S28@",
    "1 SOUR @S32@",
    "1 SOUR @S33@",
]
individuals[alice_gallaher_iid] = [
    f"0 {alice_gallaher_iid} INDI",
    "1 NAME Alice /Gallaher/",
    "1 SEX F",
    "1 BIRT",
    "2 DATE ABT 1904",
    "2 PLAC Alaska",
    "1 NOTE The 1950 census records her as age 46, born in Alaska, and Mary Alice's mother; her 1929 marriage record supplies the maiden surname Gallaher.",
    "1 REFN RECORD-ALICE-GALLAHER-THOREN",
    "1 SOUR @S32@",
    "1 SOUR @S33@",
]
add_unique(individuals["@I002@"], f"1 ASSO {chris_iid}")
add_unique(individuals["@I002@"], "2 RELA Stepchild")


def resolved(local_id: str) -> str:
    return local_to_ged.get(local_id, "")


families: list[dict] = []
for fam in canonical_families:
    # The original corrected package duplicated four core families. Keep all
    # facts but collapse them below.
    families.append({"husb": fam["husb"], "wife": fam["wife"],
                     "children": set(fam["children"]), "notes": set(fam["notes"]),
                     "sources": set(), "marriage_date": fam["marriage_date"],
                     "marriage_place": fam["marriage_place"]})


def add_family(husb: str, wife: str, children: list[str], note: str = "", source: str = "",
               marriage_date: str = "", marriage_place: str = "") -> None:
    husb = husb or ""
    wife = wife or ""
    children = [child for child in children if child]
    for fam in families:
        if fam["husb"] == husb and fam["wife"] == wife:
            fam["children"].update(children)
            if note:
                fam["notes"].add(note)
            if source:
                fam["sources"].add(source)
            if marriage_date:
                fam["marriage_date"] = marriage_date
            if marriage_place:
                fam["marriage_place"] = marriage_place
            return
    families.append({"husb": husb, "wife": wife, "children": set(children),
                     "notes": {note} if note else set(),
                     "sources": {source} if source else set(),
                     "marriage_date": marriage_date, "marriage_place": marriage_place})


# Merge duplicate canonical families by identical parent pair.
collapsed: list[dict] = []
for fam in families:
    existing = next((x for x in collapsed if x["husb"] == fam["husb"] and x["wife"] == fam["wife"]), None)
    if existing:
        existing["children"].update(fam["children"])
        existing["notes"].update(fam["notes"])
        existing["sources"].update(fam["sources"])
        existing["marriage_date"] = existing["marriage_date"] or fam["marriage_date"]
        existing["marriage_place"] = existing["marriage_place"] or fam["marriage_place"]
    else:
        collapsed.append(fam)
families = collapsed

# Merge a one-parent canonical family into the fuller same-child family.
for partial in list(families):
    parents = {x for x in (partial["husb"], partial["wife"]) if x}
    if len(parents) != 1:
        continue
    for full in families:
        full_parents = {x for x in (full["husb"], full["wife"]) if x}
        if len(full_parents) == 2 and parents.issubset(full_parents) and partial["children"] & full["children"]:
            full["children"].update(partial["children"])
            full["notes"].update(partial["notes"])
            full["sources"].update(partial["sources"])
            families.remove(partial)
            break

for row in direct_rows:
    father = resolved(row["father_id"])
    mother = resolved(row["mother_id"])
    if father or mother:
        add_family(father, mother, [resolved(row["person_id"])],
                   "Relationship merged from the records-first Vollmer-Marsh research package.", "@S26@")

for row in extended_rows:
    father = resolved(row["father_ref"])
    mother = resolved(row["mother_ref"])
    if father or mother:
        add_family(father, mother, [resolved(row["person_id"])],
                   "Collateral relationship merged from the extended-family research package.", "@S27@")

add_family("@I176@", "@I002@", ["@I001@", "@I175@"],
           "Jan is Fredric and Arianna's biological mother; Henry is recorded as their father in the recovered canonical package.", "@S28@")
add_family("", mary_alice_iid, [chris_iid],
           "Chris's father was not confirmed and is intentionally omitted.", "@S28@")
add_family(william_thoren_iid, alice_gallaher_iid, [mary_alice_iid],
           "The 1950 census identifies Mary Alice as William and Alice's daughter.", "@S32@",
           "16 NOV 1929", "Pierce County, Washington")
add_family(william_thoren_iid, alice_gallaher_iid, [], source="@S33@")
add_family("@I176@", mary_alice_iid, [],
           "Owner-confirmed first marriage of Henry, before his marriage to Jan. This spouse link does not establish Chris's father.",
           "@S31@", "16 SEP 1955", "King County, Washington")
add_family("@I176@", mary_alice_iid, [], source="@S28@")
add_unique(individuals["@I176@"], "1 SOUR @S31@")

# Remove duplicate core families that survive under reversed or incomplete old forms.
deduped: list[dict] = []
for fam in families:
    parent_set = frozenset(x for x in (fam["husb"], fam["wife"]) if x)
    match = next((x for x in deduped if frozenset(y for y in (x["husb"], x["wife"]) if y) == parent_set), None)
    if match and parent_set:
        match["children"].update(fam["children"])
        match["notes"].update(fam["notes"])
        match["sources"].update(fam["sources"])
        match["marriage_date"] = match["marriage_date"] or fam["marriage_date"]
        match["marriage_place"] = match["marriage_place"] or fam["marriage_place"]
    else:
        deduped.append(fam)
families = deduped

# Rebuild all GEDCOM family links from the consolidated family table.
for iid, lines in list(individuals.items()):
    individuals[iid] = strip_level1(lines, {"FAMC", "FAMS"})

family_rows = []
for index, fam in enumerate(families, 1):
    fid = f"@F{index:03d}@"
    for parent in (fam["husb"], fam["wife"]):
        if parent in individuals:
            add_unique(individuals[parent], f"1 FAMS {fid}")
    for child in sorted(fam["children"]):
        if child in individuals:
            add_unique(individuals[child], f"1 FAMC {fid}")
    family_rows.append({
        "family_id": fid.strip("@"),
        "husband_id": fam["husb"].strip("@"),
        "wife_id": fam["wife"].strip("@"),
        "children_ids": ";".join(child.strip("@") for child in sorted(fam["children"])),
        "marriage": "; ".join(value for value in (fam["marriage_date"], fam["marriage_place"]) if value),
        "notes": " | ".join(sorted(fam["notes"])),
        "source_refs": ";".join(sorted(source.strip("@") for source in fam["sources"])),
    })


source_blocks["@S26@"] = [
    "0 @S26@ SOUR",
    "1 TITL Vollmer-Marsh direct-ancestor records-first research package",
    "1 AUTH Codex research tasks in the Family Tree project",
    "1 NOTE Full citations and preserved records are in Fredric_Vollmer_Complete_Family_Tree_Sources.md and records/.",
]
source_blocks["@S27@"] = [
    "0 @S27@ SOUR",
    "1 TITL Extended-family records-first research package",
    "1 AUTH Codex extended-family task in the Family Tree project",
    "1 NOTE Full citations, rejected candidates, and source quality are in Fredric_Vollmer_Complete_Family_Tree_Sources.md.",
]
source_blocks["@S28@"] = [
    "0 @S28@ SOUR",
    "1 TITL Owner statements on Jan Muller Vollmer, Mary Alice Thoren, William Thoren, and Chris Vollmer",
    "1 AUTH Fredric Muller Vollmer",
    "1 DATE 2 SEP 2026",
    "1 NOTE Jan is Fredric's biological mother; Mary Alice Thoren was born in Port Townsend, was Henry's first wife, and is Chris Vollmer's mother; Jan is Chris's stepmother. William 'Bill' Thoren was remembered as Mary Alice's father. Chris's father was not stated.",
]
source_blocks["@S29@"] = [
    "0 @S29@ SOUR",
    "1 TITL Recovered records-first corrected maternal family-tree package",
    "1 AUTH Build Family Tree chat in the Family Tree project",
    "1 DATE 30 AUG 2026",
    "1 NOTE Canonical GEDCOM, workbook, report, chart, source key, and validation package recovered from the original project chat.",
]
source_blocks["@S30@"] = [
    "0 @S30@ SOUR",
    "1 TITL Owner statement on Charles Frederic Vollmer's name",
    "1 AUTH Fredric Muller Vollmer",
    "1 DATE 30 AUG 2026",
    "1 NOTE Frederic was Charles Vollmer's middle name. Later record indexes may spell it Frederick.",
]
source_blocks["@S31@"] = [
    "0 @S31@ SOUR",
    "1 TITL Henry R Vollmer and Mary A Thoren marriage record",
    "1 AUTH Washington State Archives; King County Auditor",
    "1 DATE 16 SEP 1955",
    "1 NOTE King County Marriage Records, 1855-2017; reference kingcoarchmc207309; https://digitalarchives.wa.gov/Record/View/437A4FBD9EF3DA4BD90C60795808BC69",
]
source_blocks["@S32@"] = [
    "0 @S32@ SOUR",
    "1 TITL 1950 United States census household of William J Thoren",
    "1 AUTH U.S. Census Bureau; National Archives and Records Administration",
    "1 DATE 5 APR 1950",
    "1 NOTE Seattle, King County, Washington, enumeration district 40-124, sheet 74, lines 23-25. William J Thoren, wife Alice, and daughter Mary Alice; NARA image 43290879-Washington-031283-0021; https://1950census.archives.gov/search/?ed=40-124&state=WA&page=1",
]
source_blocks["@S33@"] = [
    "0 @S33@ SOUR",
    "1 TITL William J Thoren and Alice Gallaher marriage record",
    "1 AUTH Washington State Archives; Pierce County Auditor",
    "1 DATE 16 NOV 1929",
    "1 NOTE Pierce County Auditor Marriage Records, reference prcmc-v23-00709; https://digitalarchives.wa.gov/Record/View/33AF9C076D80A9452C66FD351D17CD73",
]

header = [
    "0 HEAD",
    "1 SOUR OpenAI Codex consolidated genealogy research",
    "2 NAME Complete Family Tree of Fredric Muller Vollmer",
    "1 DATE 2 SEP 2026",
    "1 GEDC",
    "2 VERS 5.5.1",
    "2 FORM LINEAGE-LINKED",
    "1 CHAR UTF-8",
    "1 LANG English",
    "1 NOTE Aggregates all Family Tree project chats through 2 Sep 2026. Living details are minimized.",
]
ged_lines = header[:]
for iid in sorted(individuals, key=lambda value: int(value.strip("@I"))):
    ged_lines.extend(individuals[iid])
for row, fam in zip(family_rows, families):
    fid = "@" + row["family_id"] + "@"
    ged_lines.append(f"0 {fid} FAM")
    if fam["husb"]:
        ged_lines.append(f"1 HUSB {fam['husb']}")
    if fam["wife"]:
        ged_lines.append(f"1 WIFE {fam['wife']}")
    for child in sorted(fam["children"]):
        ged_lines.append(f"1 CHIL {child}")
    if fam["marriage_date"] or fam["marriage_place"]:
        ged_lines.append("1 MARR")
        if fam["marriage_date"]:
            ged_lines.append(f"2 DATE {fam['marriage_date']}")
        if fam["marriage_place"]:
            ged_lines.append(f"2 PLAC {fam['marriage_place']}")
    for note in sorted(fam["notes"]):
        if note:
            ged_lines.append(f"1 NOTE {note}")
    for source in sorted(fam["sources"]):
        ged_lines.append(f"1 SOUR {source}")
for sid in sorted(source_blocks, key=lambda value: int(value.strip("@S"))):
    ged_lines.extend(source_blocks[sid])
ged_lines.append("0 TRLR")
OUT_GED.write_text("\n".join(ged_lines) + "\n", encoding="utf-8")


def event_text(lines: list[str], tag: str) -> str:
    for i, line in enumerate(lines):
        if line == f"1 {tag}":
            date = ""
            place = ""
            for subline in lines[i + 1:]:
                if subline.startswith("1 ") or subline.startswith("0 "):
                    break
                if subline.startswith("2 DATE "):
                    date = subline[7:]
                elif subline.startswith("2 PLAC "):
                    place = subline[7:]
                elif subline.startswith("2 NOTE ") and not date:
                    date = subline[7:]
            return "; ".join(x for x in (date, place) if x)
    return ""


reverse_local: dict[str, list[str]] = defaultdict(list)
for local_id, iid in local_to_ged.items():
    reverse_local[iid].append(local_id)
reverse_local[mary_alice_iid].append("OWNER-MARY-ALICE")
reverse_local[chris_iid].append("OWNER-CHRIS-VOLLMER")
reverse_local[william_thoren_iid].append("OWNER-WILLIAM-J-THOREN")
reverse_local[alice_gallaher_iid].append("RECORD-ALICE-GALLAHER-THOREN")

people_rows = []
for iid in sorted(individuals, key=lambda value: int(value.strip("@I"))):
    lines = individuals[iid]
    people_rows.append({
        "individual_id": iid.strip("@"),
        "name": clean_name(first_value(lines, "NAME")),
        "sex": first_value(lines, "SEX") or "U",
        "birth": event_text(lines, "BIRT"),
        "death": event_text(lines, "DEAT"),
        "local_ids": ";".join(sorted(set(reverse_local.get(iid, [])))),
        "source_refs": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 SOUR ")),
        "notes": " | ".join(line[7:] for line in lines if line.startswith("1 NOTE ")),
        "family_as_child": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 FAMC ")),
        "families_as_spouse": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 FAMS ")),
    })

with OUT_PEOPLE.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=people_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(people_rows)
with OUT_FAMILIES.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=family_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(family_rows)


source_catalog = []
for sid in sorted(source_blocks, key=lambda value: int(value.strip("@S"))):
    source_catalog.append({
        "source_id": sid.strip("@"),
        "title": first_value(source_blocks[sid], "TITL"),
        "author": first_value(source_blocks[sid], "AUTH"),
        "date": first_value(source_blocks[sid], "DATE"),
        "notes": " | ".join(line[7:] for line in source_blocks[sid] if line.startswith("1 NOTE ")),
        "origin": "recovered canonical GEDCOM" if int(sid.strip("@S")) <= 25 else "cross-chat consolidation",
    })

record_inventory = []
for path in sorted(RECORDS.glob("*")):
    if path.is_file():
        record_inventory.append({
            "source_id": "RECORD-" + path.stem,
            "title": path.name,
            "author": "",
            "date": "",
            "notes": hashlib.sha256(path.read_bytes()).hexdigest(),
            "origin": "preserved original or derivative record",
        })

with OUT_SOURCE_INVENTORY.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=source_catalog[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(source_catalog + record_inventory)

OUT_SOURCES.write_text(
    "# Consolidated source ledger\n\n"
    "This ledger aggregates the recovered maternal canonical package, the later Vollmer-Marsh direct-ancestor research, the extended-family research, and owner corrections. The GEDCOM uses S1-S33; the detailed local ledgers below retain their original identifiers.\n\n"
    "## Cross-chat provenance\n\n"
    "- **Build Family Tree** — recovered canonical 169-person maternal direct tree, corrected maternal collateral households, GEDCOM, workbook, report, chart, source key, and validation package.\n"
    "- **Continue Vollmer Family Tree** — established the paternal research scope and Charles Frederic Vollmer / Doris Marsh anchors; superseded where later records proved more detail.\n"
    "- **Research Vollmer-Marsh ancestry** and **Continue Vollmer-Marsh research** — records-first paternal direct ancestry, preserved originals, conflicts, and rejected candidates.\n"
    "- **Extend paternal family tree** — three collateral rings on both sides, owner relationship corrections, record audits, and rejected same-name candidates.\n\n"
    "## GEDCOM source catalog\n\n" +
    "\n".join(f"### {s['source_id']} — {s['title']}\n\n{s['notes'] or 'See recovered canonical report/source key.'}" for s in source_catalog) +
    "\n\n---\n\n## Vollmer-Marsh direct-ancestor ledger\n\n" + DIRECT_SOURCES.read_text(encoding="utf-8") +
    "\n\n---\n\n## Extended-family ledger\n\n" + EXTENDED_SOURCES.read_text(encoding="utf-8") + "\n",
    encoding="utf-8",
)

canonical_data = {
    "metadata": {
        "title": "Complete Family Tree of Fredric Muller Vollmer",
        "format": "consolidated canonical genealogy dataset",
        "gedcom_version": "5.5.1",
        "updated": "2026-09-02",
        "scope": "Recovered maternal direct tree plus all later paternal direct and three-ring collateral research, including the documented Thoren-Gallaher parents of Mary Alice Thoren.",
        "privacy": "Living dates, addresses, contact information, and speculative modern links are omitted.",
    },
    "people": people_rows,
    "families": family_rows,
    "sources": source_catalog,
    "corrections": canonical_json.get("corrections", []) + [
        {"topic": "Jan relationship", "corrected": "Jan is Fredric's biological mother and Chris Vollmer's stepmother."},
        {"topic": "Chris parentage", "corrected": "Mary Alice is Chris Vollmer's mother; Chris's father remains unconfirmed."},
        {"topic": "Mary Alice identity and birthplace", "corrected": "Owner-confirmed as Mary Alice Thoren, born in Port Townsend, Washington."},
        {"topic": "Mary Alice parents", "corrected": "The 1950 census identifies William J. Thoren and Alice Gallaher Thoren as Mary Alice's parents."},
        {"topic": "Henry first marriage", "corrected": "Henry R. Vollmer married Mary A. Thoren in King County on 16 Sep 1955, before Jan Muller Vollmer."},
        {"topic": "Mary Gene spouse", "corrected": "Historical records identify Elmer James Chaffee Jr; the family chart's James form is retained as a shorter usage."},
        {"topic": "Eloise vital dates", "corrected": "Official California index supports 25 Aug 1903-10 Feb 1994; earlier compiled dates remain conflicting secondary evidence."},
        {"topic": "Charles Vollmer middle name", "corrected": "Owner-confirmed spelling is Charles Frederic Vollmer; Frederick is retained only as a record/index variant."},
    ],
    "provenance": [
        {"thread_title": "Build Family Tree", "role": "canonical maternal baseline and maternal collateral family evidence"},
        {"thread_title": "Continue Vollmer Family Tree", "role": "paternal scope and family anchors"},
        {"thread_title": "Research Vollmer-Marsh ancestry", "role": "records-first paternal direct research"},
        {"thread_title": "Continue Vollmer-Marsh research", "role": "deep paternal continuation and preserved originals"},
        {"thread_title": "Extend paternal family tree", "role": "both-side collateral expansion and owner corrections"},
        {"thread_title": "Trace Mary Alice Thoren ancestry", "role": "owner-confirmed identity and birthplace; official marriage and 1950 census evidence for her parents"},
    ],
}
OUT_JSON.write_text(json.dumps(canonical_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OUT_AUDIT.write_text(
    f"# Complete family-tree merge audit\n\n"
    f"- Recovered canonical GEDCOM individuals: {len(blocks(ged_text, 'INDI'))}\n"
    f"- Recovered canonical GEDCOM families: {len(blocks(ged_text, 'FAM'))}\n"
    f"- Vollmer-Marsh direct rows considered: {len(direct_rows)}\n"
    f"- Extended-family rows considered: {len(extended_rows)}\n"
    f"- Consolidated individuals: {len(people_rows)}\n"
    f"- Consolidated families: {len(family_rows)}\n"
    f"- GEDCOM sources: {len(source_catalog)}\n"
    f"- Preserved record files inventoried: {len(record_inventory)}\n\n"
    "## Controlling corrections\n\n"
    "- Jan Muller Vollmer is Fredric's biological mother.\n"
    "- Mary Alice Thoren is Chris Vollmer's biological mother and Henry's first wife.\n"
    "- William J. Thoren and Alice Gallaher Thoren are Mary Alice's census-documented parents.\n"
    "- Jan is Chris Vollmer's stepmother.\n"
    "- Chris's father is not inferred.\n"
    "- The superseded Chaffee mistranscription is removed.\n"
    "- Elmer James Chaffee Jr is Mary Gene's historically documented husband; James remains a family-chart short form.\n"
    "- Eloise's official California dates replace the conflicting compiled dates as the primary GEDCOM events.\n\n"
    "## Merge policy\n\n"
    "The recovered GEDCOM remains the structural base. Stable direct identities were reused. Newer record-based findings supersede earlier drafts when they directly conflict. Family testimony is retained for living collateral relationships with an explicit evidence grade; public people-search sites were not used.\n",
    encoding="utf-8",
)


def ref_errors() -> list[str]:
    valid_iids = set(individuals)
    errors = []
    for row in family_rows:
        for field in ("husband_id", "wife_id"):
            value = row[field]
            if value and f"@{value}@" not in valid_iids:
                errors.append(f"{row['family_id']} {field} {value}")
        for value in filter(None, row["children_ids"].split(";")):
            if f"@{value}@" not in valid_iids:
                errors.append(f"{row['family_id']} child {value}")
    return errors


out_text = OUT_GED.read_text(encoding="utf-8")
errors = ref_errors()
validation = {
    "GEDCOM individuals": len(re.findall(r"^0 @I\d+@ INDI$", out_text, re.M)),
    "GEDCOM families": len(re.findall(r"^0 @F\d+@ FAM$", out_text, re.M)),
    "GEDCOM sources": len(re.findall(r"^0 @S\d+@ SOUR$", out_text, re.M)),
    "GEDCOM trailers": len(re.findall(r"^0 TRLR$", out_text, re.M)),
    "broken individual references": len(errors),
    "superseded Janet transcription absent": "Janet Chaffee" not in out_text,
    "Jan biological-mother correction present": "Jan is Fredric's biological mother" in out_text,
    "Mary Alice Thoren present": "1 NAME Mary Alice /Thoren/" in out_text,
    "Mary Alice Port Townsend birthplace present": "2 PLAC Port Townsend, Jefferson, Washington" in out_text,
    "William J Thoren present": "1 NAME William J /Thoren/" in out_text,
    "Alice Gallaher present": "1 NAME Alice /Gallaher/" in out_text,
    "Henry and Mary 1955 marriage present": "2 DATE 16 SEP 1955" in out_text,
    "William and Alice 1929 marriage present": "2 DATE 16 NOV 1929" in out_text,
    "Chris Vollmer present": "1 NAME Chris /Vollmer/" in out_text,
    "Chris father intentionally absent": any(not row["husband_id"] and row["wife_id"] == mary_alice_iid.strip("@") and chris_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Elmer James Chaffee corrected": "Elmer James /Chaffee/ Jr" in out_text,
    "people CSV rows": len(people_rows),
    "families CSV rows": len(family_rows),
    "source inventory rows": len(source_catalog) + len(record_inventory),
}
OUT_VALIDATION.write_text("\n".join(f"{key}: {value}" for key, value in validation.items()) + "\n" +
                          ("Reference errors:\n" + "\n".join(errors) + "\n" if errors else ""), encoding="utf-8")

OUT_README.write_text(
    "# Complete Family Tree of Fredric Muller Vollmer\n\n"
    "This is the canonical local package aggregating every Family Tree project chat through 2 September 2026. The GEDCOM is the standardized tree source of truth; the JSON and workbook are synchronized review formats.\n\n"
    "## Canonical files\n\n"
    f"- `{OUT_GED.name}` — GEDCOM 5.5.1 source-of-truth tree.\n"
    f"- `{OUT_JSON.name}` — complete machine-readable people, families, sources, corrections, and cross-chat provenance.\n"
    "- `Fredric_Vollmer_Complete_Family_Tree_Index.xlsx` — synchronized review workbook; its eight recovered tabs are retained for provenance and four consolidated tabs reflect the current tree.\n"
    f"- `{OUT_PEOPLE.name}` and `{OUT_FAMILIES.name}` — flat audit tables.\n"
    f"- `{OUT_SOURCES.name}` — all recovered and later source ledgers in one file.\n"
    f"- `{OUT_SOURCE_INVENTORY.name}` — source and preserved-record inventory with SHA-256 hashes.\n"
    f"- `{OUT_AUDIT.name}` and `{OUT_VALIDATION.name}` — merge and integrity checks.\n"
    "- `records/` — preserved source images and certificates copied from the later records-first tasks.\n"
    "- The recovered records-first maternal package remains alongside these files for provenance.\n\n"
    "## Privacy and relationship controls\n\n"
    "Living details are minimized. Jan is recorded as Fredric's biological mother and Chris Vollmer's stepmother. Mary Alice Thoren is Chris's mother and Henry's first wife. The 1950 census identifies William J. Thoren and Alice Gallaher Thoren as Mary Alice's parents. Chris's father is left blank because the owner did not confirm him.\n",
    encoding="utf-8",
)

print(json.dumps(validation, indent=2))
