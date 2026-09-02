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
THOREN_SOURCES = BASE / "research-log/Mary_Alice_Thoren_Research_Log.md"
RECORDS = BASE / "records"
VITAL_RESEARCH = BASE / "Fredric_Vollmer_Complete_Family_Tree_Vital_Dates_Research.csv"
OCCUPATION_RESEARCH = BASE / "Fredric_Vollmer_Complete_Family_Tree_Occupation_Research.csv"

PREFIX = "Fredric_Vollmer_Complete_Family_Tree"
OUT_GED = BASE / f"{PREFIX}.ged"
OUT_JSON = BASE / f"{PREFIX}_Canonical_Data.json"
OUT_PEOPLE = BASE / f"{PREFIX}_People.csv"
OUT_FAMILIES = BASE / f"{PREFIX}_Families.csv"
OUT_SOURCES = BASE / f"{PREFIX}_Sources.md"
OUT_SOURCE_INVENTORY = BASE / f"{PREFIX}_Source_Inventory.csv"
OUT_VITAL_COVERAGE = BASE / f"{PREFIX}_Vital_Date_Coverage.csv"
OUT_OCCUPATION_COVERAGE = BASE / f"{PREFIX}_Occupation_Coverage.csv"
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
    qualifier = ""
    lower = date_text.lower()
    if lower.startswith("between ") and " and " in lower:
        date_text = "BET " + date_text[8:]
    elif lower.startswith("about "):
        qualifier = "ABT "
        date_text = date_text[6:]
    elif lower.startswith("before "):
        qualifier = "BEF "
        date_text = date_text[7:]
    elif lower.startswith("after "):
        qualifier = "AFT "
        date_text = date_text[6:]
    if "–" in date_text or " in " in lower:
        return "", "", original
    month_map = {m.title(): m.upper() for m in "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}
    tokens = date_text.split()
    tokens = [month_map.get(token.title(), token) for token in tokens]
    if not any(re.fullmatch(r"\d{3,4}(?:/\d{2,4})?", token) for token in tokens):
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
vital_rows = read_csv(VITAL_RESEARCH)
occupation_rows = read_csv(OCCUPATION_RESEARCH)
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
                            "Owner-confirmed: Mary Alice Thoren was Henry's first wife, before Jan Muller Vollmer.",
                            "Owner-confirmed: Henry is Chris Vollmer's biological father; Chris is Fredric's paternal half-brother."],
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

# Owner-confirmed recent-family relationships.
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
    "1 NOTE Owner-confirmed biological mother of Chris Vollmer and first wife of Henry Richard Vollmer, before Jan Muller Vollmer. Henry and Mary Alice are Chris's biological parents.",
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
    "1 NOTE Owner-confirmed son of Henry Richard Vollmer and Mary Alice Thoren, stepchild of Jan Muller Vollmer, and paternal half-brother of Fredric Muller Vollmer.",
    "1 REFN OWNER-CHRIS-VOLLMER",
    "1 ASSO @I002@",
    "2 RELA Stepmother",
    "1 SOUR @S28@",
]
individuals[william_thoren_iid] = [
    f"0 {william_thoren_iid} INDI",
    "1 NAME William John /Thoren/",
    "1 SEX M",
    "1 BIRT",
    "2 DATE 19 JUL 1901",
    "2 PLAC Great Falls, Cascade, Montana",
    "1 DEAT",
    "2 DATE 26 OCT 1991",
    "2 PLAC Washington",
    "1 NOTE Called Bill in family memory. The 1910 census places him in Christian and Augusta Thoren's household; later records use William J. or William John.",
    "1 REFN OWNER-WILLIAM-J-THOREN",
    "1 SOUR @S28@",
    "1 SOUR @S32@",
    "1 SOUR @S33@",
    "1 SOUR @S34@",
]
individuals[alice_gallaher_iid] = [
    f"0 {alice_gallaher_iid} INDI",
    "1 NAME Alice /Gallaher/",
    "1 SEX F",
    "1 BIRT",
    "2 DATE 27 APR 1902",
    "2 PLAC Alaska",
    "1 DEAT",
    "2 DATE 23 AUG 1978",
    "2 PLAC Ocean Park, Pacific, Washington",
    "1 NOTE The 1950 census identifies her as Mary Alice's mother; her 1929 marriage record supplies the maiden surname Gallaher. Her parents remain unproved.",
    "1 REFN RECORD-ALICE-GALLAHER-THOREN",
    "1 SOUR @S32@",
    "1 SOUR @S33@",
    "1 SOUR @S35@",
]


def add_thoren_person(local_id: str, name: str, sex: str, birth: str = "", death: str = "",
                      notes: list[str] | None = None, sources: list[str] | None = None) -> str:
    iid = next_iid()
    lines = [f"0 {iid} INDI", f"1 NAME {ged_name(name)}", f"1 SEX {sex}"]
    lines = set_event(lines, "BIRT", birth)
    lines = set_event(lines, "DEAT", death)
    for note in notes or []:
        lines.append(f"1 NOTE {note}")
    lines.append(f"1 REFN {local_id}")
    for source in sources or []:
        lines.append(f"1 SOUR {source}")
    individuals[iid] = lines
    thoren_people_local_ids[iid] = local_id
    return iid


thoren_people_local_ids: dict[str, str] = {}
christian_thoren_iid = add_thoren_person(
    "RECORD-CHRISTIAN-ANDREW-THOREN", "Christian Andrew Thoren", "M",
    "27 Jan 1861; Ignaberga, Kristianstad, Sweden", "9 May 1921; Great Falls, Cascade, Montana",
    ["Swedish records use Christian Andersson and Christian Anders Thorén; U.S. records also use Andrew, Christia, and Christison.",
     "A 1900 census estimate of January 1862 conflicts with the 27 January 1861 indexed Swedish birth and is retained only as a record variation.",
     "The Montana death index misassigns his wife Augusta Nelson as his mother; the Swedish birth record identifies Anders Troedsson and Kjersti Månsdotter as his parents."],
    ["@S34@", "@S36@"],
)
augusta_nilsdotter_iid = add_thoren_person(
    "RECORD-AUGUSTA-NILSDOTTER-THOREN", "Augusta Nilsdotter", "F",
    "30 Nov 1860; Hjärnarp, Kristianstad, Sweden", "4 Dec 1913; Great Falls, Cascade, Montana",
    ["The Swedish household record uses the patronymic Nilsdotter; an indexed baptism uses Svensson, and U.S. records use Nilson, Nelson, and Thoren.",
     "A 1900 census estimate of November 1861 conflicts with the 30 November 1860 Swedish birth and baptism records."],
    ["@S34@", "@S37@"],
)
anders_troedsson_iid = add_thoren_person(
    "RECORD-ANDERS-TROEDSSON", "Anders Troedsson", "M",
    "2 May 1824; Norra Sandby, Kristianstad, Sweden", notes=["Household surveys link him first to parents Trued Andersson and Bortha Nilsdotter and later to wife Kjersti Månsdotter and son Christian."], sources=["@S38@"],
)
kjersti_mansdotter_iid = add_thoren_person(
    "RECORD-KJERSTI-MANSDOTTER", "Kjersti Månsdotter", "F",
    "31 Oct 1825; Mellby, Kristianstad, Sweden", notes=["The reviewed household survey establishes her as Christian's mother; no parent-naming birth or baptism record was located."], sources=["@S38@"],
)
trued_andersson_iid = add_thoren_person(
    "RECORD-TRUED-ANDERSSON", "Trued Andersson", "M",
    "25 Apr 1792; Norra Sandby, Kristianstad, Sweden", sources=["@S38@"],
)
bortha_nilsdotter_iid = add_thoren_person(
    "RECORD-BORTHA-NILSDOTTER", "Bortha Nilsdotter", "F",
    "1783; Gumlösa, Kristianstad, Sweden", notes=["No parent-naming baptism record was located; same-name baptism hints from other parishes were rejected."], sources=["@S38@"],
)
nils_svensson_iid = add_thoren_person(
    "RECORD-NILS-SVENSSON", "Nils Svensson", "M",
    "3 May 1825; Ränneslöv, Halland, Sweden", notes=["His baptism names Gunnilla Nilsdotter as mother but does not name a father; the unknown father remains blank despite the patronymic Svensson."], sources=["@S39@", "@S40@"],
)
christina_persdotter_iid = add_thoren_person(
    "RECORD-CHRISTINA-PERSDOTTER", "Christina Persdotter", "F",
    "24 Jan 1823; Hasslöv, Halland, Sweden", notes=["Indexed records also use Kristina Persdotter and Stina Parsdotter."], sources=["@S39@", "@S42@"],
)
gunnilla_nilsdotter_iid = add_thoren_person(
    "RECORD-GUNNILLA-NILSDOTTER", "Gunnilla Nilsdotter", "F",
    "20 Sep 1796; Ränneslöv, Halland, Sweden", notes=["Indexed records also use Gunla Nilsdotter. She is the only parent named in Nils Svensson's baptism."], sources=["@S40@", "@S41@"],
)
nils_johansson_iid = add_thoren_person(
    "RECORD-NILS-JOHANSSON", "Nils Johansson", "M",
    notes=["Named as Gunnilla Nilsdotter's father in her 1796 baptism; no further identity was proved."], sources=["@S41@"],
)
elna_nilsdotter_iid = add_thoren_person(
    "RECORD-ELNA-NILSDOTTER", "Elna Nilsdotter", "F",
    notes=["Named as Gunnilla Nilsdotter's mother in her 1796 baptism; no further identity was proved."], sources=["@S41@"],
)
pehr_erlandsson_iid = add_thoren_person(
    "RECORD-PEHR-ERLANDSSON", "Pehr Erlandsson", "M",
    "10 Feb 1790; Hishult, Halland, Sweden", notes=["A household survey reports 10 February 1791; the 1790 baptism is nearer to the event and controls the canonical birth date."], sources=["@S43@", "@S44@"],
)
ingier_hansdotter_iid = add_thoren_person(
    "RECORD-INGIER-HANSDOTTER", "Ingier Hansdotter", "F",
    "20 Mar 1794; Hasslöv, Halland, Sweden", sources=["@S43@", "@S45@"],
)
erland_palsson_iid = add_thoren_person(
    "RECORD-ERLAND-PALSSON", "Erland Pålsson", "M",
    notes=["Named as Pehr Erlandsson's father in the 1790 baptism. A possible 1756 Knäred baptism was not linked closely enough to import its parents."], sources=["@S44@"],
)
bengta_pehrsdotter_iid = add_thoren_person(
    "RECORD-BENGTA-PEHRSDOTTER", "Bengta Pehrsdotter", "F",
    notes=["Named as Pehr Erlandsson's mother in the 1790 baptism. A similar Bengta Persdotter baptism and marriage belonged to another woman and was rejected."], sources=["@S44@"],
)
hans_mansson_iid = add_thoren_person(
    "RECORD-HANS-MANSSON", "Hans Månsson", "M",
    notes=["Named as Ingier Hansdotter's father in her 1794 baptism; no further identity was proved."], sources=["@S45@"],
)
maria_hansdotter_iid = add_thoren_person(
    "RECORD-MARIA-HANSDOTTER", "Maria Hansdotter", "F",
    notes=["Named as Ingier Hansdotter's mother in her 1794 baptism; no further identity was proved."], sources=["@S45@"],
)
peter_iid = next_iid()
individuals[peter_iid] = [
    f"0 {peter_iid} INDI",
    "1 NAME Peter /Vollmer/",
    "1 SEX M",
    "1 NOTE Owner-confirmed brother of Chris Vollmer. The indexed obituary names Henry R Vollmer as Peter's father and Christopher as a sibling.",
    "1 NOTE Mary Alice appears only as a potential mother on one duplicate Ancestry profile, so Peter's mother is intentionally left blank.",
    "1 REFN OWNER-PETER-VOLLMER",
    "1 REFN ANCESTRY-282372364380",
    "1 REFN ANCESTRY-282618825108",
    f"1 ASSO {chris_iid}",
    "2 RELA Brother",
    "1 SOUR @S47@",
]
add_unique(individuals["@I002@"], f"1 ASSO {chris_iid}")
add_unique(individuals["@I002@"], "2 RELA Stepchild")
add_unique(individuals[chris_iid], f"1 ASSO {peter_iid}")
add_unique(individuals[chris_iid], "2 RELA Brother")
add_unique(individuals[chris_iid], "1 SOUR @S47@")

# Apply only explicitly accepted findings from the vital-date research ledger.
# Rejected candidates remain documented in that ledger and never alter GEDCOM events.
accepted_vital_rows = [row for row in vital_rows if row["decision"] == "accepted"]
for row in accepted_vital_rows:
    iid = f"@{row['individual_id']}@"
    if iid not in individuals:
        raise KeyError(f"Vital-date research row {row['research_id']} references missing {iid}")
    notes = [
        f"Vital-date research {row['research_id']} ({row['confidence']} confidence): {row['evidence_note']}",
    ]
    if row["conflict_note"]:
        notes.append(f"Vital-date conflict: {row['conflict_note']}")
    ensure_person_update(
        iid,
        birth=row["birth"] or None,
        death=row["death"] or None,
        notes=notes,
        source="@S46@",
    )
ensure_person_update("@I177@", name="Bruce Eric Muller", sex="M", source="@S47@")


def add_occupation_event(iid: str, row: dict[str, str]) -> None:
    lines = individuals[iid]
    event = [f"1 OCCU {row['occupation_or_role']}"]
    period = row["occupation_date_or_period"]
    if re.fullmatch(r"\d{4}-\d{4}", period):
        start, end = period.split("-", 1)
        event.append(f"2 DATE FROM {start} TO {end}")
    elif re.fullmatch(r"(?:\d{1,2} [A-Za-z]{3} )?\d{4}", period):
        event.append(f"2 DATE {period.upper()}")
    elif period:
        event.append(f"2 NOTE Reported period: {period}.")
    place_or_employer = row["place_or_employer"]
    if place_or_employer:
        if row["category"] == "military role":
            event.append(f"2 NOTE Unit: {place_or_employer}")
        else:
            place_parts = [part.strip() for part in place_or_employer.split(";") if part.strip()]
            if place_parts:
                event.append(f"2 PLAC {place_parts[0]}")
            if len(place_parts) > 1:
                event.append(f"2 NOTE Work context: {'; '.join(place_parts[1:])}")
    event.append(
        f"2 NOTE {row['category']}; {row['confidence']} confidence; "
        f"occupation research {row['research_id']}. {row['evidence_note']}"
    )
    if row["conflict_note"]:
        event.append(f"2 NOTE Conflict/control: {row['conflict_note']}")
    event.append("2 SOUR @S48@")
    lines.extend(event)
    add_unique(lines, "1 SOUR @S48@")
    individuals[iid] = lines


accepted_occupation_rows = [row for row in occupation_rows if row["decision"] == "accepted"]
for row in accepted_occupation_rows:
    iid = f"@{row['individual_id']}@"
    if iid not in individuals:
        raise KeyError(f"Occupation research row {row['research_id']} references missing {iid}")
    add_occupation_event(iid, row)


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
add_family("@I176@", mary_alice_iid, [chris_iid],
           "Owner-confirmed biological parents of Chris Vollmer. Chris is Fredric Muller Vollmer's paternal half-brother. The earlier unconfirmed-father status is superseded by the owner's 2 September 2026 clarification.",
           "@S28@", "16 SEP 1955", "King County, Washington")
add_family(william_thoren_iid, alice_gallaher_iid, [mary_alice_iid],
           "The 1950 census identifies Mary Alice as William and Alice's daughter.", "@S32@",
           "16 NOV 1929", "Pierce County, Washington")
add_family(william_thoren_iid, alice_gallaher_iid, [], source="@S33@")
add_family(christian_thoren_iid, augusta_nilsdotter_iid, [william_thoren_iid],
           "The 1910 Great Falls census records William as the son of Christian and Augusta Thoren; Swedish records identify both parents' earlier generations.", "@S34@")
add_family(anders_troedsson_iid, kjersti_mansdotter_iid, [christian_thoren_iid],
           "Christian's Swedish indexed birth and the linked household surveys identify Anders and Kjersti as his parents.", "@S36@")
add_family(trued_andersson_iid, bortha_nilsdotter_iid, [anders_troedsson_iid],
           "The Norra Sandby household survey records Anders as the son of Trued Andersson and Bortha Nilsdotter.", "@S38@")
add_family(nils_svensson_iid, christina_persdotter_iid, [augusta_nilsdotter_iid],
           "Augusta's Hjärnarp birth, baptism, and household records identify Nils and Christina as her parents.", "@S37@",
           "26 OCT 1850", "Ränneslöv, Halland, Sweden")
add_family(nils_svensson_iid, christina_persdotter_iid, [], source="@S39@")
add_family("", gunnilla_nilsdotter_iid, [nils_svensson_iid],
           "Nils's 1825 baptism names Gunnilla Nilsdotter as his mother and names no father; the father remains blank.", "@S40@")
add_family(nils_johansson_iid, elna_nilsdotter_iid, [gunnilla_nilsdotter_iid],
           "Gunnilla's 1796 baptism names Nils Johansson and Elna Nilsdotter as her parents.", "@S41@")
add_family(pehr_erlandsson_iid, ingier_hansdotter_iid, [christina_persdotter_iid],
           "Christina's 1823 baptism and the Hasslöv household survey identify Pehr and Ingier as her parents.", "@S42@")
add_family(erland_palsson_iid, bengta_pehrsdotter_iid, [pehr_erlandsson_iid],
           "Pehr's 1790 Hishult baptism names Erland Pålsson and Bengta Pehrsdotter as his parents.", "@S44@")
add_family(hans_mansson_iid, maria_hansdotter_iid, [ingier_hansdotter_iid],
           "Ingier's 1794 Hasslöv baptism names Hans Månsson and Maria Hansdotter as her parents.", "@S45@")
add_family("@I176@", mary_alice_iid, [],
           "Washington State Archives documents Henry and Mary Alice's marriage; owner testimony separately confirms both as Chris's biological parents.",
           "@S31@", "16 SEP 1955", "King County, Washington")
add_family("@I176@", mary_alice_iid, [], source="@S28@")
add_unique(individuals["@I176@"], "1 SOUR @S31@")
add_family("@I176@", "", [peter_iid],
           "Peter's indexed obituary names Henry R Vollmer as his father. Peter is owner-confirmed as Chris Vollmer's brother; Peter's mother is not inferred.",
           "@S47@")
add_unique(individuals["@I176@"], "1 SOUR @S47@")

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
    "1 NOTE Jan is Fredric's biological mother; Mary Alice Thoren was born in Port Townsend, was Henry's first wife, and is Chris Vollmer's mother; Jan is Chris's stepmother. William 'Bill' Thoren was remembered as Mary Alice's father. A later 2 Sep statement explicitly identifies Henry as Chris's biological father and Chris as Fredric's paternal half-brother, superseding the earlier unconfirmed status.",
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
source_blocks["@S34@"] = [
    "0 @S34@ SOUR",
    "1 TITL William John Thoren U.S. census, draft, and death-record cluster",
    "1 AUTH U.S. Census Bureau; Selective Service System; state and federal vital-record indexes; Ancestry.com",
    "1 NOTE The 1910 Great Falls census places William, born about 1902 in Montana, as son of Christian and Augusta Thoren; later records establish birth 19 Jul 1901 at Great Falls and death 26 Oct 1991. Records: https://www.ancestry.com/search/collections/7884/records/191842032 ; https://www.ancestry.com/search/collections/6061/records/45709575 ; https://www.ancestry.com/search/collections/6224/records/111918347 ; https://www.ancestry.com/search/collections/2238/records/37117805 ; https://www.ancestry.com/search/collections/5254/records/1097942 ; https://www.ancestry.com/search/collections/3693/records/62441333",
]
source_blocks["@S35@"] = [
    "0 @S35@ SOUR",
    "1 TITL Alice Gallaher Thoren U.S. census, Social Security, death, and burial-record cluster",
    "1 AUTH U.S. Census Bureau; Social Security Administration; Washington State; Find a Grave; Ancestry.com",
    "1 NOTE Records establish birth 27 Apr 1902 in Alaska and death 23 Aug 1978 at Ocean Park, Washington, while the 1929 marriage supplies Gallaher. No parent-naming primary record was found. Records: https://www.ancestry.com/search/collections/6224/records/111918337 ; https://www.ancestry.com/search/collections/3693/records/62440948 ; https://www.ancestry.com/search/collections/6716/records/895426 ; https://www.ancestry.com/search/collections/60541/records/182552983 ; https://www.ancestry.com/search/collections/60901/records/778054457",
]
source_blocks["@S36@"] = [
    "0 @S36@ SOUR",
    "1 TITL Christian Andrew Thoren Swedish birth and household records, U.S. census, and Montana death index",
    "1 AUTH ArkivDigital; U.S. Census Bureau; Montana Department of Public Health and Human Services; Ancestry.com",
    "1 NOTE Swedish records identify Christian Andersson/Thorén, born 27 Jan 1861 at Ignaberga, as son of Anders Troedsson and Kjersti Månsdotter. The Montana death index records 9 May 1921 but incorrectly places wife Augusta Nelson in the mother field. Records: https://www.ancestry.com/search/collections/2262/records/40805501 ; https://www.ancestry.com/search/collections/9731/records/42221130 ; https://www.ancestry.com/search/collections/7602/records/76515976 ; https://www.ancestry.com/search/collections/6061/records/45709573 ; https://www.ancestry.com/search/collections/5437/records/820390",
]
source_blocks["@S37@"] = [
    "0 @S37@ SOUR",
    "1 TITL Augusta Nilsdotter Thoren Swedish birth, baptism, household, U.S. census, and burial records",
    "1 AUTH ArkivDigital; FamilySearch; U.S. Census Bureau; Find a Grave; Ancestry.com",
    "1 NOTE Records identify Augusta, born 30 Nov 1860 at Hjärnarp, as daughter of Nils Svensson and Christina Persdotter; she died 4 Dec 1913 at Great Falls. Name forms include Nilsdotter, Svensson, Nilson, Nelson, and Thoren. Records: https://www.ancestry.com/search/collections/2262/records/41710407 ; https://www.ancestry.com/search/collections/60361/records/255112 ; https://www.ancestry.com/search/collections/9731/records/29521690 ; https://www.ancestry.com/search/collections/7602/records/76515977 ; https://www.ancestry.com/search/collections/60525/records/24177921",
]
source_blocks["@S38@"] = [
    "0 @S38@ SOUR",
    "1 TITL Anders Troedsson and Kjersti Månsdotter Swedish household-survey chain",
    "1 AUTH ArkivDigital; Ancestry.com",
    "1 NOTE The Ignaberga household links Anders (born 2 May 1824) and Kjersti (born 31 Oct 1825) to son Christian; the earlier Norra Sandby household links Anders to parents Trued Andersson (born 25 Apr 1792) and Bortha Nilsdotter (born 1783). Records: https://www.ancestry.com/search/collections/9731/records/8673393 ; https://www.ancestry.com/search/collections/9731/records/8673394 ; https://www.ancestry.com/search/collections/9731/records/73561674 ; https://www.ancestry.com/search/collections/9731/records/73561672 ; https://www.ancestry.com/search/collections/9731/records/73561673",
]
source_blocks["@S39@"] = [
    "0 @S39@ SOUR",
    "1 TITL Nils Svensson and Christina Persdotter household and marriage records",
    "1 AUTH ArkivDigital; FamilySearch; Ancestry.com",
    "1 NOTE The Hjärnarp household records the couple with daughter Augusta and their birthplaces/dates; the marriage index records 26 Oct 1850 at Ränneslöv. Records: https://www.ancestry.com/search/collections/9731/records/29521684 ; https://www.ancestry.com/search/collections/9731/records/29521685 ; https://www.ancestry.com/search/collections/60363/records/338059 ; https://www.ancestry.com/search/collections/60363/records/338058",
]
source_blocks["@S40@"] = [
    "0 @S40@ SOUR",
    "1 TITL Nils Svensson 1825 Ränneslöv baptism",
    "1 AUTH FamilySearch; Ancestry.com",
    "1 DATE 5 MAY 1825",
    "1 NOTE Nils was born 3 May and baptized 5 May 1825 at Ränneslöv. The record names Gunnilla Nilsdotter as mother and names no father, so the paternal link remains blank. https://www.ancestry.com/search/collections/60361/records/13922815",
]
source_blocks["@S41@"] = [
    "0 @S41@ SOUR",
    "1 TITL Gunnilla Nilsdotter 1796 Ränneslöv baptism",
    "1 AUTH FamilySearch; Ancestry.com",
    "1 DATE 25 SEP 1796",
    "1 NOTE Gunla/Gunnilla was born 20 Sep and baptized 25 Sep 1796 at Ränneslöv, daughter of Nils Johansson and Elna Nilsdotter. https://www.ancestry.com/search/collections/60361/records/22162419",
]
source_blocks["@S42@"] = [
    "0 @S42@ SOUR",
    "1 TITL Christina Persdotter 1823 Hasslöv baptism",
    "1 AUTH FamilySearch; Ancestry.com",
    "1 DATE 25 JAN 1823",
    "1 NOTE Stina/Christina was born 24 Jan and baptized 25 Jan 1823 at Hasslöv, daughter of Pehr Erlandsson and Ingier Hansdotter. https://www.ancestry.com/search/collections/60361/records/23764021",
]
source_blocks["@S43@"] = [
    "0 @S43@ SOUR",
    "1 TITL Pehr Erlandsson and Ingier Hansdotter Hasslöv household survey",
    "1 AUTH ArkivDigital; Ancestry.com",
    "1 NOTE The 1814-1823 household records Pehr as head and Ingier as wife. It reports Pehr born 10 Feb 1791 and Ingier 20 Mar 1794; Pehr's baptism supplies the nearer 1790 birth year. Records: https://www.ancestry.com/search/collections/9731/records/91496907 ; https://www.ancestry.com/search/collections/9731/records/91496908",
]
source_blocks["@S44@"] = [
    "0 @S44@ SOUR",
    "1 TITL Pehr Erlandsson 1790 Hishult baptism",
    "1 AUTH FamilySearch; Ancestry.com",
    "1 DATE 14 FEB 1790",
    "1 NOTE Pehr was born 10 Feb and baptized 14 Feb 1790 at Hishult, son of Erland Pålsson and Bengta Pehrsdotter. https://www.ancestry.com/search/collections/60361/records/15528153",
]
source_blocks["@S45@"] = [
    "0 @S45@ SOUR",
    "1 TITL Ingier Hansdotter 1794 Hasslöv baptism",
    "1 AUTH FamilySearch; Ancestry.com",
    "1 DATE 23 MAR 1794",
    "1 NOTE Ingier was born 20 Mar and baptized 23 Mar 1794 at Hasslöv, daughter of Hans Månsson and Maria Hansdotter. https://www.ancestry.com/search/collections/60361/records/11677925",
]
source_blocks["@S46@"] = [
    "0 @S46@ SOUR",
    "1 TITL Vital-date enrichment research ledger",
    "1 AUTH Codex research task in the Family Tree project",
    "1 DATE 2 SEP 2026",
    "1 NOTE Accepted additions, conservative date ranges, rejected candidates, source quality, and conflicts are itemized in Fredric_Vollmer_Complete_Family_Tree_Vital_Dates_Research.csv.",
]
source_blocks["@S47@"] = [
    "0 @S47@ SOUR",
    "1 TITL Owner statements and Ancestry review for Bruce Muller and Peter Vollmer",
    "1 AUTH Fredric Muller Vollmer and Ancestry record review",
    "1 DATE 2 SEP 2026",
    "1 NOTE Bruce died in a Vancouver, Washington hospital and was remembered as age 14. Ancestry's existing-tree hint supplies Bruce Eric Muller's 15 Jun 1958-4 Jun 1972 dates. The sourced Pete Vollmer profile supplies 29 Jun 1959-5 Aug 1975 and identifies Henry R Vollmer as father and Christopher as sibling.",
]
source_blocks["@S48@"] = [
    "0 @S48@ SOUR",
    "1 TITL Occupation and role enrichment research ledger",
    "1 AUTH Codex research task in the Family Tree project",
    "1 DATE 2 SEP 2026",
    "1 NOTE Accepted occupational facts, household roles, military roles, transcription normalizations, rejected candidates, and row-level citations are itemized in Fredric_Vollmer_Complete_Family_Tree_Occupation_Research.csv.",
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


def occupation_event_texts(lines: list[str]) -> list[str]:
    events = []
    for i, line in enumerate(lines):
        if not line.startswith("1 OCCU "):
            continue
        occupation = line[7:]
        date = ""
        place = ""
        work_context = ""
        for subline in lines[i + 1:]:
            if subline.startswith("1 ") or subline.startswith("0 "):
                break
            if subline.startswith("2 DATE "):
                date = subline[7:]
            elif subline.startswith("2 PLAC "):
                place = subline[7:]
            elif subline.startswith("2 NOTE Work context: "):
                work_context = subline[len("2 NOTE Work context: "):]
            elif subline.startswith("2 NOTE Unit: "):
                work_context = subline[len("2 NOTE Unit: "):]
        context = "; ".join(x for x in (date, place, work_context) if x)
        events.append(f"{occupation} ({context})" if context else occupation)
    return events


reverse_local: dict[str, list[str]] = defaultdict(list)
for local_id, iid in local_to_ged.items():
    reverse_local[iid].append(local_id)
reverse_local[mary_alice_iid].append("OWNER-MARY-ALICE")
reverse_local[chris_iid].append("OWNER-CHRIS-VOLLMER")
reverse_local[william_thoren_iid].append("OWNER-WILLIAM-J-THOREN")
reverse_local[alice_gallaher_iid].append("RECORD-ALICE-GALLAHER-THOREN")
reverse_local[peter_iid].append("OWNER-PETER-VOLLMER")
for iid, local_id in thoren_people_local_ids.items():
    reverse_local[iid].append(local_id)

people_rows = []
for iid in sorted(individuals, key=lambda value: int(value.strip("@I"))):
    lines = individuals[iid]
    people_rows.append({
        "individual_id": iid.strip("@"),
        "name": clean_name(first_value(lines, "NAME")),
        "sex": first_value(lines, "SEX") or "U",
        "birth": event_text(lines, "BIRT"),
        "death": event_text(lines, "DEAT"),
        "occupations_and_roles": " | ".join(occupation_event_texts(lines)),
        "local_ids": ";".join(sorted(set(reverse_local.get(iid, [])))),
        "source_refs": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 SOUR ")),
        "notes": " | ".join(line[7:] for line in lines if line.startswith("1 NOTE ")),
        "family_as_child": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 FAMC ")),
        "families_as_spouse": ";".join(line[7:].strip("@") for line in lines if line.startswith("1 FAMS ")),
    })


def has_vital_date(value: str) -> bool:
    lower = value.lower()
    if not value or "date unknown" in lower or "date and place unknown" in lower:
        return False
    return bool(re.search(r"(?<!\d)\d{3,4}(?:/\d{2,4})?(?!\d)", value))


living_by_local = {row["person_id"]: row.get("living_status", "") for row in extended_rows}
explicit_living_iids = {"I001", "I002", "I334", "I335"}
privacy_limited_modern_iids = {
    "I175", "I180", "I181", "I182", "I184", "I185", "I186", "I187", "I188",
    "I189", "I190", "I191", "I192", "I194", "I195", "I196", "I197", "I198",
    "I199", "I200", "I201", "I202", "I203", "I204", "I205", "I269", "I272",
    "I273", "I322", "I323", "I331", "I334", "I335",
}


def missing_status(person: dict[str, str], event: str) -> str:
    value = person[event]
    iid = person["individual_id"]
    local_ids = [local_id for local_id in person["local_ids"].split(";") if local_id]
    if iid in explicit_living_iids or any(living_by_local.get(local_id) == "living" for local_id in local_ids):
        return "withheld—living/private"
    if iid in privacy_limited_modern_iids:
        return "not researched—privacy limited"
    if value:
        return "place or placeholder only—date unresolved"
    return "unresolved—no supported date found"


vital_coverage_rows = []
for person in people_rows:
    birth_status = "recorded" if has_vital_date(person["birth"]) else missing_status(person, "birth")
    death_status = "recorded" if has_vital_date(person["death"]) else missing_status(person, "death")
    if birth_status == death_status == "recorded":
        overall = "complete"
    elif birth_status == "recorded" or death_status == "recorded":
        overall = "partial"
    elif "living/private" in birth_status or "living/private" in death_status:
        overall = "withheld—living/private"
    elif "privacy limited" in birth_status or "privacy limited" in death_status:
        overall = "not researched—privacy limited"
    else:
        overall = "unresolved"
    vital_coverage_rows.append({
        "individual_id": person["individual_id"],
        "name": person["name"],
        "birth": person["birth"],
        "birth_status": birth_status,
        "death": person["death"],
        "death_status": death_status,
        "overall_status": overall,
        "source_refs": person["source_refs"],
    })

coverage_counts = defaultdict(int)
for row in vital_coverage_rows:
    coverage_counts[row["overall_status"]] += 1
birth_date_count = sum(has_vital_date(row["birth"]) for row in people_rows)
death_date_count = sum(has_vital_date(row["death"]) for row in people_rows)

occupation_research_by_iid: dict[str, list[dict[str, str]]] = defaultdict(list)
for row in accepted_occupation_rows:
    occupation_research_by_iid[row["individual_id"]].append(row)


def occupation_status(person: dict[str, str]) -> tuple[str, str]:
    iid = person["individual_id"]
    local_ids = [local_id for local_id in person["local_ids"].split(";") if local_id]
    if person["occupations_and_roles"]:
        return "recorded", "One or more cited occupations or roles are present in the GEDCOM."
    if iid in {"I177", peter_iid.strip("@") }:
        return "not established—minor", "No occupation is assigned; this person died before adulthood."
    if iid in explicit_living_iids or any(living_by_local.get(local_id) == "living" for local_id in local_ids):
        return "withheld—living/private", "No living person's occupation was researched or exposed."
    if iid in privacy_limited_modern_iids:
        return "not researched—privacy limited", "Modern collateral occupation research was intentionally limited for privacy."
    return "unresolved—no supported occupation found", "No occupation is inferred from name, sex, residence, spouse, or family role."


occupation_coverage_rows = []
occupation_coverage_counts = defaultdict(int)
for person in people_rows:
    research = occupation_research_by_iid.get(person["individual_id"], [])
    status, coverage_note = occupation_status(person)
    occupation_coverage_counts[status] += 1
    occupation_coverage_rows.append({
        "individual_id": person["individual_id"],
        "name": person["name"],
        "occupations_and_roles": person["occupations_and_roles"],
        "event_count": len(research),
        "status": status,
        "categories": ";".join(sorted({row["category"] for row in research})),
        "source_refs": person["source_refs"],
        "research_ids": ";".join(row["research_id"] for row in research),
        "coverage_note": coverage_note,
    })
occupation_people_count = occupation_coverage_counts["recorded"]
occupation_event_count = len(accepted_occupation_rows)

with OUT_PEOPLE.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=people_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(people_rows)
with OUT_FAMILIES.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=family_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(family_rows)
with OUT_VITAL_COVERAGE.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=vital_coverage_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(vital_coverage_rows)
with OUT_OCCUPATION_COVERAGE.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=occupation_coverage_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(occupation_coverage_rows)


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
    "This ledger aggregates the recovered maternal canonical package, the later Vollmer-Marsh direct-ancestor research, the extended-family research, the Mary Alice Thoren ancestry investigation, owner corrections, the vital-date enrichment pass, and the occupation/role enrichment pass. The GEDCOM uses S1-S48; the detailed local ledgers below retain their original identifiers.\n\n"
    "## Cross-chat provenance\n\n"
    "- **Build Family Tree** — recovered canonical 169-person maternal direct tree, corrected maternal collateral households, GEDCOM, workbook, report, chart, source key, and validation package.\n"
    "- **Continue Vollmer Family Tree** — established the paternal research scope and Charles Frederic Vollmer / Doris Marsh anchors; superseded where later records proved more detail.\n"
    "- **Research Vollmer-Marsh ancestry** and **Continue Vollmer-Marsh research** — records-first paternal direct ancestry, preserved originals, conflicts, and rejected candidates.\n"
    "- **Extend paternal family tree** — three collateral rings on both sides, owner relationship corrections, record audits, and rejected same-name candidates.\n\n"
    "- **Trace Mary Alice Thoren ancestry** — Ancestry.com census, vital, Swedish church, and household-survey records extending the proven Thoren line into eighteenth-century Sweden.\n\n"
    "- **Vital-date enrichment** — audited every canonical person, restored dropped project facts, added supported dates or conservative ranges, and classified every remaining gap as unresolved or privacy-limited.\n"
    "- **Occupation and role enrichment** — reviewed Ancestry records in the signed-in browser, reconciled results to canonical people, preserved dated occupational changes, and classified every person without a supported fact.\n\n"
    "## GEDCOM source catalog\n\n" +
    "\n".join(f"### {s['source_id']} — {s['title']}\n\n{s['notes'] or 'See recovered canonical report/source key.'}" for s in source_catalog) +
    "\n\n---\n\n## Vollmer-Marsh direct-ancestor ledger\n\n" + DIRECT_SOURCES.read_text(encoding="utf-8") +
    "\n\n---\n\n## Extended-family ledger\n\n" + EXTENDED_SOURCES.read_text(encoding="utf-8") +
    "\n\n---\n\n## Mary Alice Thoren ancestry research ledger\n\n" + THOREN_SOURCES.read_text(encoding="utf-8") +
    "\n\n---\n\n## Vital-date enrichment ledger\n\n"
    "The complete, row-level research ledger is `Fredric_Vollmer_Complete_Family_Tree_Vital_Dates_Research.csv`. Accepted rows alter GEDCOM events; rejected rows document tempting but unproved candidates.\n\n" +
    "\n\n".join(
        f"### {row['research_id']} — {row['name']} ({row['decision']})\n\n"
        f"- Birth addition: {row['birth'] or 'none'}\n"
        f"- Death addition: {row['death'] or 'none'}\n"
        f"- Confidence: {row['confidence']}\n"
        f"- Source: {row['source_title']} — <{row['source_url']}>\n"
        f"- Evidence: {row['evidence_note']}\n"
        f"- Conflict/control: {row['conflict_note'] or 'none'}"
        for row in vital_rows
    ) +
    "\n\n---\n\n## Occupation and role enrichment ledger\n\n"
    "The complete, row-level research ledger is `Fredric_Vollmer_Complete_Family_Tree_Occupation_Research.csv`. Accepted rows create GEDCOM OCCU events; rejected rows remain evidence controls and never alter a person.\n\n" +
    "\n\n".join(
        f"### {row['research_id']} — {row['name']} ({row['decision']})\n\n"
        f"- Occupation or role: {row['occupation_or_role'] or 'none'}\n"
        f"- Date or period: {row['occupation_date_or_period'] or 'unresolved'}\n"
        f"- Place or employer: {row['place_or_employer'] or 'unresolved'}\n"
        f"- Category: {row['category']}\n"
        f"- Confidence: {row['confidence']}\n"
        f"- Source: {row['source_title']} — <{row['source_url']}>\n"
        f"- Evidence: {row['evidence_note']}\n"
        f"- Conflict/control: {row['conflict_note'] or 'none'}"
        for row in occupation_rows
    ) + "\n",
    encoding="utf-8",
)

canonical_data = {
    "metadata": {
        "title": "Complete Family Tree of Fredric Muller Vollmer",
        "format": "consolidated canonical genealogy dataset",
        "gedcom_version": "5.5.1",
        "updated": "2026-09-02",
        "scope": "Recovered maternal direct tree plus later paternal direct and bounded collateral research, including Mary Alice Thoren's documented Thoren ancestry through eighteenth-century Sweden.",
        "privacy": "Living dates, addresses, contact information, and speculative modern links are omitted.",
        "vital_date_coverage": {
            "people": len(people_rows),
            "birth_dates_recorded": birth_date_count,
            "death_dates_recorded": death_date_count,
            "complete": coverage_counts["complete"],
            "partial": coverage_counts["partial"],
            "unresolved": coverage_counts["unresolved"],
            "privacy_limited": coverage_counts["not researched—privacy limited"],
            "living_private": coverage_counts["withheld—living/private"],
        },
        "occupation_coverage": {
            "people": len(people_rows),
            "people_with_recorded_occupations_or_roles": occupation_people_count,
            "accepted_occupation_events": occupation_event_count,
            "unresolved": occupation_coverage_counts["unresolved—no supported occupation found"],
            "privacy_limited": occupation_coverage_counts["not researched—privacy limited"],
            "living_private": occupation_coverage_counts["withheld—living/private"],
            "minor_without_occupation": occupation_coverage_counts["not established—minor"],
        },
    },
    "people": people_rows,
    "families": family_rows,
    "sources": source_catalog,
    "corrections": canonical_json.get("corrections", []) + [
        {"topic": "Jan relationship", "corrected": "Jan is Fredric's biological mother and Chris Vollmer's stepmother."},
        {"topic": "Chris parentage", "corrected": "Owner-confirmed: Henry Richard Vollmer and Mary Alice Thoren are Chris Vollmer's biological parents; Chris is Fredric's paternal half-brother. This supersedes the earlier unconfirmed-father status."},
        {"topic": "Mary Alice identity and birthplace", "corrected": "Owner-confirmed as Mary Alice Thoren, born in Port Townsend, Washington."},
        {"topic": "Mary Alice parents", "corrected": "The 1950 census identifies William J. Thoren and Alice Gallaher Thoren as Mary Alice's parents."},
        {"topic": "William Thoren ancestry", "corrected": "A record chain identifies William John Thoren's parents as Christian Andrew Thoren and Augusta Nilsdotter, then extends their Swedish direct ancestry through named eighteenth-century ancestors."},
        {"topic": "Alice Gallaher ancestry", "corrected": "Alice Gallaher's parents remain unproved. The unsourced James M. Gallaher and Agnes Cope member-tree hint is retained only as a rejected/unverified lead."},
        {"topic": "Nils Svensson father", "corrected": "Nils's 1825 baptism names only his mother, Gunnilla Nilsdotter; no father is inferred from the Svensson patronymic."},
        {"topic": "Henry first marriage", "corrected": "Henry R. Vollmer married Mary A. Thoren in King County on 16 Sep 1955, before Jan Muller Vollmer."},
        {"topic": "Mary Gene spouse", "corrected": "Historical records identify Elmer James Chaffee Jr; the family chart's James form is retained as a shorter usage."},
        {"topic": "Eloise vital dates", "corrected": "Official California index supports 25 Aug 1903-10 Feb 1994; earlier compiled dates remain conflicting secondary evidence."},
        {"topic": "Charles Vollmer middle name", "corrected": "Owner-confirmed spelling is Charles Frederic Vollmer; Frederick is retained only as a record/index variant."},
        {"topic": "Bathsheba Robie Lane death", "corrected": "Town-history and monument evidence support 13 Apr 1765; the copied 1785 member-tree date is rejected."},
        {"topic": "Gabriel Whelden death", "corrected": "Will and probate evidence establish a death between 11 Feb 1653/54 and 4 Apr 1654; 4 Apr 1655 is rejected."},
        {"topic": "Bruce Eric Muller vital dates", "corrected": "Ancestry's existing-tree hint supplies 15 Jun 1958-4 Jun 1972; owner testimony places the death at a Vancouver hospital and remembers age 14. The calculated-age discrepancy is retained."},
        {"topic": "Peter Vollmer identity and dates", "corrected": "Duplicate Peter/Pete profiles were consolidated as Peter Vollmer, 29 Jun 1959-5 Aug 1975. The obituary index names Henry R Vollmer as father and Christopher as sibling; Peter's mother remains unconfirmed."},
    ],
    "provenance": [
        {"thread_title": "Build Family Tree", "role": "canonical maternal baseline and maternal collateral family evidence"},
        {"thread_title": "Continue Vollmer Family Tree", "role": "paternal scope and family anchors"},
        {"thread_title": "Research Vollmer-Marsh ancestry", "role": "records-first paternal direct research"},
        {"thread_title": "Continue Vollmer-Marsh research", "role": "deep paternal continuation and preserved originals"},
        {"thread_title": "Extend paternal family tree", "role": "both-side collateral expansion and owner corrections"},
        {"thread_title": "Trace Mary Alice Thoren ancestry", "role": "owner-confirmed identity and birthplace; U.S. and Swedish records extending the proven Thoren line while preserving Gallaher and same-name uncertainties"},
        {"thread_title": "Vital-date enrichment", "role": "complete birth/death coverage audit, Ancestry review, and owner-confirmed Bruce/Peter corrections"},
        {"thread_title": "Occupation enrichment", "role": "Ancestry-centered occupation and role research with one-row-per-person coverage outcomes"},
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
    f"- Preserved record files inventoried: {len(record_inventory)}\n"
    f"- People with a recorded birth date: {birth_date_count}\n"
    f"- People with a recorded death date: {death_date_count}\n"
    f"- People with both dates recorded: {coverage_counts['complete']}\n"
    f"- Partial vital-date coverage: {coverage_counts['partial']}\n"
    f"- Unresolved vital-date coverage: {coverage_counts['unresolved']}\n"
    f"- Privacy-limited modern people: {coverage_counts['not researched—privacy limited']}\n"
    f"- Living/private people with dates withheld: {coverage_counts['withheld—living/private']}\n"
    f"- Accepted occupation/role research events: {occupation_event_count}\n"
    f"- People with a recorded occupation or role: {occupation_people_count}\n"
    f"- Unresolved occupation coverage: {occupation_coverage_counts['unresolved—no supported occupation found']}\n"
    f"- Privacy-limited occupation coverage: {occupation_coverage_counts['not researched—privacy limited']}\n"
    f"- Living/private occupation coverage: {occupation_coverage_counts['withheld—living/private']}\n"
    f"- Minors without an established occupation: {occupation_coverage_counts['not established—minor']}\n\n"
    "## Controlling corrections\n\n"
    "- Jan Muller Vollmer is Fredric's biological mother.\n"
    "- Henry Richard Vollmer and Mary Alice Thoren are Chris Vollmer's biological parents; Mary Alice was Henry's first wife.\n"
    "- William J. Thoren and Alice Gallaher Thoren are Mary Alice's census-documented parents.\n"
    "- William John Thoren's parents are Christian Andrew Thoren and Augusta Nilsdotter; their proven direct Swedish lines are added through the earliest parent-naming records located.\n"
    "- Alice Gallaher's parents remain unresolved; the unsourced James M. Gallaher and Agnes Cope hint is not imported.\n"
    "- Nils Svensson's father remains blank because his baptism names only his mother, Gunnilla Nilsdotter.\n"
    "- Jan is Chris Vollmer's stepmother.\n"
    "- Chris is Fredric's paternal half-brother.\n"
    "- The superseded Chaffee mistranscription is removed.\n"
    "- Elmer James Chaffee Jr is Mary Gene's historically documented husband; James remains a family-chart short form.\n"
    "- Eloise's official California dates replace the conflicting compiled dates as the primary GEDCOM events.\n\n"
    "- Bruce Eric Muller is recorded as 15 Jun 1958-4 Jun 1972, with Vancouver as the owner-confirmed death place and the age-14 recollection retained as a conflict.\n"
    "- Duplicate Peter/Pete Vollmer profiles are consolidated as Peter Vollmer, 29 Jun 1959-5 Aug 1975; Henry is the obituary-supported father and Christopher the named sibling, while Peter's mother remains uninferred.\n\n"
    "## Merge policy\n\n"
    "The recovered GEDCOM remains the structural base. Stable direct identities were reused. Newer record-based findings supersede earlier drafts when they directly conflict. Parent links require a parent-naming record or independently corroborated household chain; Ancestry member-tree hints and same-name suggestions are not imported without that proof. Family testimony is retained for living collateral relationships with an explicit evidence grade; public people-search sites were not used.\n",
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
    "William John Thoren present": "1 NAME William John /Thoren/" in out_text,
    "Alice Gallaher present": "1 NAME Alice /Gallaher/" in out_text,
    "Henry and Mary 1955 marriage present": "2 DATE 16 SEP 1955" in out_text,
    "William and Alice 1929 marriage present": "2 DATE 16 NOV 1929" in out_text,
    "Christian and Augusta parent link to William present": any(row["husband_id"] == christian_thoren_iid.strip("@") and row["wife_id"] == augusta_nilsdotter_iid.strip("@") and william_thoren_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Swedish Thoren grandparents link present": any(row["husband_id"] == anders_troedsson_iid.strip("@") and row["wife_id"] == kjersti_mansdotter_iid.strip("@") and christian_thoren_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Nils Svensson father remains blank": any(not row["husband_id"] and row["wife_id"] == gunnilla_nilsdotter_iid.strip("@") and nils_svensson_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Alice Gallaher parents remain blank": not any(alice_gallaher_iid.strip("@") in row["children_ids"].split(";") for row in family_rows),
    "Chris Vollmer present": "1 NAME Chris /Vollmer/" in out_text,
    "Chris parent link to Henry and Mary present": any(row["husband_id"] == "I176" and row["wife_id"] == mary_alice_iid.strip("@") and chris_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Bruce Eric Muller dates present": "1 NAME Bruce Eric /Muller/" in out_text and "2 DATE 15 JUN 1958" in individuals["@I177@"] and "2 DATE 4 JUN 1972" in individuals["@I177@"],
    "Peter Vollmer present": "1 NAME Peter /Vollmer/" in out_text,
    "Peter and Chris brother association present": f"1 ASSO {chris_iid}" in individuals[peter_iid] and f"1 ASSO {peter_iid}" in individuals[chris_iid],
    "Peter father link to Henry present": any(row["husband_id"] == "I176" and not row["wife_id"] and peter_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Peter mother intentionally absent": not any(row["wife_id"] and peter_iid.strip("@") in row["children_ids"] for row in family_rows),
    "Elmer James Chaffee corrected": "Elmer James /Chaffee/ Jr" in out_text,
    "people CSV rows": len(people_rows),
    "families CSV rows": len(family_rows),
    "source inventory rows": len(source_catalog) + len(record_inventory),
    "vital-date research rows": len(vital_rows),
    "accepted vital-date research rows": len(accepted_vital_rows),
    "vital-date coverage rows": len(vital_coverage_rows),
    "people with recorded birth dates": birth_date_count,
    "people with recorded death dates": death_date_count,
    "people with complete vital dates": coverage_counts["complete"],
    "occupation research rows": len(occupation_rows),
    "accepted occupation research rows": len(accepted_occupation_rows),
    "occupation coverage rows": len(occupation_coverage_rows),
    "people with recorded occupations or roles": occupation_people_count,
    "GEDCOM occupation events": len(re.findall(r"^1 OCCU ", out_text, re.M)),
    "rejected Marion teacher absent": not any("1 OCCU Teacher" in line for line in individuals["@I284@"]),
}
OUT_VALIDATION.write_text("\n".join(f"{key}: {value}" for key, value in validation.items()) + "\n" +
                          ("Reference errors:\n" + "\n".join(errors) + "\n" if errors else ""), encoding="utf-8")

OUT_README.write_text(
    "# Complete Family Tree of Fredric Muller Vollmer\n\n"
    "This is the canonical local package aggregating every Family Tree project chat through 2 September 2026. The GEDCOM is the standardized tree source of truth; the JSON and workbook are synchronized review formats.\n\n"
    "## Canonical files\n\n"
    f"- `{OUT_GED.name}` — GEDCOM 5.5.1 source-of-truth tree.\n"
    f"- `{OUT_JSON.name}` — complete machine-readable people, families, sources, corrections, and cross-chat provenance.\n"
    "- `Fredric_Vollmer_Complete_Family_Tree_Index.xlsx` — synchronized review workbook; its eight recovered tabs are retained for provenance and six consolidated tabs reflect the current tree.\n"
    f"- `{OUT_PEOPLE.name}` and `{OUT_FAMILIES.name}` — flat audit tables.\n"
    f"- `{OUT_SOURCES.name}` — all recovered and later source ledgers in one file.\n"
    f"- `{OUT_SOURCE_INVENTORY.name}` — source and preserved-record inventory with SHA-256 hashes.\n"
    f"- `{OUT_VITAL_COVERAGE.name}` — one-row-per-person birth/death coverage and explicit unresolved/privacy outcomes.\n"
    f"- `{VITAL_RESEARCH.name}` — accepted additions, rejected candidates, source quality, and conflicts from the vital-date pass.\n"
    f"- `{OUT_OCCUPATION_COVERAGE.name}` — one-row-per-person occupation/role coverage with explicit unresolved and privacy outcomes.\n"
    f"- `{OCCUPATION_RESEARCH.name}` — accepted occupational facts, rejected candidates, dates, categories, transcription controls, and row-level citations.\n"
    f"- `{OUT_AUDIT.name}` and `{OUT_VALIDATION.name}` — merge and integrity checks.\n"
    "- `records/` — preserved source images and certificates copied from the later records-first tasks.\n"
    "- The recovered records-first maternal package remains alongside these files for provenance.\n\n"
    "## Privacy and relationship controls\n\n"
    "Living details are minimized. Jan is recorded as Fredric's biological mother and Chris Vollmer's stepmother. Henry Richard Vollmer and Mary Alice Thoren are Chris's biological parents; Chris is Fredric's paternal half-brother. Peter Vollmer is recorded as Chris's owner-confirmed brother and Henry's obituary-supported son without inferring Peter's mother. The 1950 census identifies William John Thoren and Alice Gallaher Thoren as Mary Alice's parents. U.S. and Swedish records extend William's ancestry through Christian Andrew Thoren and Augusta Nilsdotter into eighteenth-century Sweden. Alice Gallaher's parents remain unresolved and no member-tree hint was imported as fact.\n",
    encoding="utf-8",
)

print(json.dumps(validation, indent=2))
