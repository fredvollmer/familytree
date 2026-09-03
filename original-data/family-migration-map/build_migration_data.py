#!/usr/bin/env python3
"""Build privacy-aware migration datasets from the canonical family tree.

The canonical GEDCOM/JSON files are inputs only.  This script writes derived
JSON/GeoJSON files beside itself so a future web app can consume the data
without scraping the visualization.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from datetime import date
from pathlib import Path


HERE = Path(__file__).resolve().parent
CANONICAL = HERE.parent / "final-family-tree" / "Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json"
GEOCODE_CACHE = HERE / "geocoded-locations.json"

US_STATES = {
    "Alabama", "Alaska", "California", "Connecticut", "Kentucky", "Maryland",
    "Massachusetts", "Michigan", "New Hampshire", "New Jersey", "New York",
    "Montana", "North Carolina", "Ohio", "Oregon", "South Carolina", "Texas", "Virginia",
    "Washington",
}

QUERY_OVERRIDES = {
    "Bavaria": "Bavaria, Germany",
    "Plymouth Colony": "Plymouth, Massachusetts, United States",
    "Moscow (now Leicester), Livingston, New York (compiled genealogy)": "Leicester, Livingston County, New York, United States",
    "Plymouth or Eastham, Massachusetts (scholarly reconstruction)": "Eastham, Massachusetts, United States",
    "Kentucky or Virginia": None,
    "exact death unproved": None,
    "date unknown": None,
    "Harsefeld, Province of Hanover, Germany": "Harsefeld, Germany",
    "Lintig, Lehe, Province of Hanover, Germany": "Lintig, Geestland, Germany",
    "Kershaw District, South Carolina": "Kershaw County, South Carolina, United States",
    "Camden District, South Carolina": "Kershaw County, South Carolina, United States",
    "Fairfield District, South Carolina": "Fairfield County, South Carolina, United States",
    "Change Islands, Newfoundland": "Change Islands, Newfoundland and Labrador, Canada",
}


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:10]}"


def confidence_from_notes(notes: str) -> str:
    match = re.search(r"Confidence\s+([ABC])", notes or "")
    if match:
        return match.group(1)
    if re.search(r"Confidence:\s*high", notes or "", re.I):
        return "A"
    if re.search(r"Confidence:\s*moderate", notes or "", re.I):
        return "B"
    if re.search(r"Confidence:\s*(low|provisional)", notes or "", re.I):
        return "C"
    return "unknown"


def branch_from_notes(notes: str) -> str:
    match = re.search(r"Branch:\s*([^.|]+)", notes or "")
    return match.group(1).strip() if match else "Unspecified"


def parse_years(value: str) -> tuple[int | None, int | None, bool]:
    years = [int(y) for y in re.findall(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)", value)]
    if not years:
        return None, None, False
    approximate = bool(re.search(r"\b(ABOUT|ABT|BEF|BEFORE|BY|AFTER|AFT|BETWEEN|probably|secondary|compiled|reconstruction)\b", value, re.I))
    return min(years), max(years), approximate


def looks_like_place_only(value: str) -> bool:
    if re.search(r"\d", value):
        return False
    cleaned = re.sub(r"^As reported:\s*", "", value, flags=re.I).strip()
    if not cleaned or cleaned.lower() in {"date unknown", "unknown"}:
        return False
    return "," in cleaned or cleaned in {
        "Alabama", "Bavaria", "Brunswick County, Virginia", "England", "Germany",
        "Kentucky", "Massachusetts", "Michigan", "New Hampshire", "New Jersey",
        "New York", "Ohio", "South Carolina", "Texas", "Virginia",
        "near Lyon, France",
    }


def split_event_value(value: str) -> tuple[str, str | None]:
    """Return (date text, place text), preserving unusual source wording."""
    value = (value or "").strip()
    if not value:
        return "", None
    if ";" in value:
        left, right = [part.strip() for part in value.split(";", 1)]
        if right.lower() == "date unknown" and left.lower().startswith("as reported:"):
            return right, re.sub(r"^As reported:\s*", "", left, flags=re.I).strip()
        return left, right or None
    if looks_like_place_only(value):
        return "date unknown", re.sub(r"^As reported:\s*", "", value, flags=re.I).strip()
    return value, None


def precision_for_place(place: str) -> str:
    lower = place.lower()
    if any(token in lower for token in ["probably", " or ", "near ", "colony", "secondary", "compiled", "reconstruction"]):
        return "approximate"
    if "county" in lower or "district" in lower:
        return "county"
    if place in US_STATES or place in {"England", "Germany", "Canada", "Bavaria", "Alsace, France"}:
        return "region"
    return "locality"


def normalize_query(place: str) -> str | None:
    if place in QUERY_OVERRIDES:
        return QUERY_OVERRIDES[place]
    query = re.sub(r"\s*\((compiled genealogy|derivative lineage record|secondary|scholarly reconstruction|strongly supported identification[^)]*)\)\s*", "", place, flags=re.I)
    query = re.sub(r"^(probably|near)\s+", "", query, flags=re.I).strip()
    if query in US_STATES:
        return f"{query}, United States"
    if any(re.search(rf"(?:,|^)\s*{re.escape(state)}$", query) for state in US_STATES):
        return f"{query}, United States"
    return query


def main() -> None:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    geocodes = json.loads(GEOCODE_CACHE.read_text(encoding="utf-8")) if GEOCODE_CACHE.exists() else {}

    # Remove the two parent families and the Fredric/Arianna couple family so
    # each named family line can be mapped without crossing through a spouse.
    graph: dict[str, set[str]] = defaultdict(set)
    for family in canonical["families"]:
        members = [value for value in [family.get("husband_id"), family.get("wife_id")] if value]
        members += [value for value in family.get("children_ids", "").split(";") if value]
        member_set = set(members)
        if (
            {"I001", "I002", "I176"}.issubset(member_set)
            or {"I001", "I356"}.issubset(member_set)
            or {"I356", "I357", "I358"}.issubset(member_set)
        ):
            continue
        for left in members:
            for right in members:
                if left != right:
                    graph[left].add(right)

    def component(anchor: str) -> set[str]:
        seen = {anchor}
        queue = deque([anchor])
        while queue:
            current = queue.popleft()
            for neighbor in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return seen

    line_components = {
        "Muller": component("I002"),
        "Vollmer": component("I176"),
        "Fischer": component("I357"),
        "VanHoose": component("I358"),
    }

    def line_for_person(person_id: str) -> str:
        matches = [name for name, people in line_components.items() if person_id in people]
        return matches[0] if len(matches) == 1 else "Other"

    places: dict[str, dict] = {}
    events: list[dict] = []
    person_events: dict[str, dict[str, dict]] = {}
    privacy_excluded_people = 0
    scope_excluded_people = 0

    for person in canonical["people"]:
        person_line = line_for_person(person["individual_id"])
        if person_line == "Other":
            # Root couples and unrelated supporting people remain in the tree,
            # but are not assigned to a family line without a unique component.
            scope_excluded_people += 1
            continue
        person_side = {
            "Muller": "Maternal",
            "Vollmer": "Paternal",
        }.get(person_line, "Other")
        birth_year_min, birth_year_max, _ = parse_years(person.get("birth", ""))
        possibly_living = (
            not person.get("death")
            and birth_year_max is not None
            and birth_year_max >= date.today().year - 100
        )
        explicitly_living = bool(re.search(r"\b(?:Living person|Potentially living)\b", person.get("notes") or "", re.I))
        if possibly_living or explicitly_living:
            privacy_excluded_people += 1
            continue
        for event_type in ("birth", "death"):
            raw = person.get(event_type, "")
            date_text, place = split_event_value(raw)
            if not place:
                continue
            year_min, year_max, approximate_date = parse_years(date_text)
            place_id = stable_id("loc", place)
            query = normalize_query(place)
            cached = geocodes.get(place, {})
            places.setdefault(place_id, {
                "location_id": place_id,
                "label": place,
                "geocode_query": query,
                "latitude": cached.get("latitude"),
                "longitude": cached.get("longitude"),
                "precision": precision_for_place(place),
                "geocode_status": cached.get("status", "unresolved" if query else "excluded-ambiguous"),
                "geocoder": cached.get("geocoder"),
                "geocoder_display_name": cached.get("display_name"),
            })
            event_id = f"evt-{person['individual_id'].lower()}-{event_type}"
            event = {
                "event_id": event_id,
                "person_id": person["individual_id"],
                "person_name": person["name"],
                "event_type": event_type,
                "date_text": date_text,
                "year_min": year_min,
                "year_max": year_max,
                "date_is_approximate": approximate_date,
                "place_original": place,
                "location_id": place_id,
                "side": person_side,
                "line": person_line,
                "branch": branch_from_notes(person.get("notes", "")),
                "confidence": confidence_from_notes(person.get("notes", "")),
                "source_refs": [s for s in person.get("source_refs", "").split(";") if s],
            }
            events.append(event)
            person_events.setdefault(person["individual_id"], {})[event_type] = event

    movements: list[dict] = []

    def add_movement(kind: str, person_id: str, from_event: dict, to_event: dict, relationship: str | None = None) -> None:
        if from_event["location_id"] == to_event["location_id"]:
            return
        if places[from_event["location_id"]]["latitude"] is None or places[to_event["location_id"]]["latitude"] is None:
            return
        movement_key = f"{kind}|{person_id}|{from_event['event_id']}|{to_event['event_id']}|{relationship or ''}"
        movements.append({
            "movement_id": stable_id("move", movement_key),
            "movement_type": kind,
            "person_id": person_id,
            "person_name": to_event["person_name"] if kind == "intergenerational" else from_event["person_name"],
            "relationship": relationship,
            "from_event_id": from_event["event_id"],
            "to_event_id": to_event["event_id"],
            "from_location_id": from_event["location_id"],
            "to_location_id": to_event["location_id"],
            "year_min": to_event["year_min"],
            "year_max": to_event["year_max"],
            "branch": to_event["branch"],
            "side": to_event["side"],
            "line": to_event["line"],
            "confidence": to_event["confidence"],
            "interpretation": "inferred endpoint displacement; not a documented travel route",
        })

    for person_id, by_type in person_events.items():
        if "birth" in by_type and "death" in by_type:
            add_movement("lifetime", person_id, by_type["birth"], by_type["death"])

    people_by_id = {person["individual_id"]: person for person in canonical["people"]}
    for family in canonical["families"]:
        child_ids = [value for value in family.get("children_ids", "").split(";") if value]
        for role, parent_id in (("father", family.get("husband_id")), ("mother", family.get("wife_id"))):
            parent_birth = person_events.get(parent_id or "", {}).get("birth")
            if not parent_birth:
                continue
            for child_id in child_ids:
                child_birth = person_events.get(child_id, {}).get("birth")
                if child_birth and child_id in people_by_id:
                    add_movement("intergenerational", child_id, parent_birth, child_birth, role)

    locations = sorted(places.values(), key=lambda item: item["label"])
    events.sort(key=lambda item: (item["year_min"] is None, item["year_min"] or 9999, item["person_name"], item["event_type"]))
    movements.sort(key=lambda item: (item["year_min"] is None, item["year_min"] or 9999, item["person_name"]))

    dated_years = [event["year_min"] for event in events if event["year_min"] is not None]
    payload = {
        "metadata": {
            "title": "Four-family migration data",
            "generated": date.today().isoformat(),
            "canonical_source": str(CANONICAL.relative_to(HERE.parent.parent)),
            "canonical_updated": canonical.get("metadata", {}).get("updated"),
            "privacy": canonical.get("metadata", {}).get("privacy"),
            "scope_note": "Derived from recorded birth and death places in the Muller, Vollmer, Fischer, and VanHoose family components. Root couples and unrelated supporting people remain in the canonical tree but are not assigned to a map line. People explicitly marked living or potentially living under a 100-year rule are also excluded.",
            "privacy_excluded_people": privacy_excluded_people,
            "scope_excluded_people": scope_excluded_people,
            "movement_note": "Routes connect recorded endpoints and are analytical inferences, not documented travel paths.",
            "year_extent": [min(dated_years), max(dated_years)] if dated_years else [None, None],
            "counts": {
                "locations": len(locations),
                "resolved_locations": sum(item["latitude"] is not None for item in locations),
                "events": len(events),
                "dated_events": sum(item["year_min"] is not None for item in events),
                "movements": len(movements),
                "people_represented": len({event["person_id"] for event in events}),
            },
        },
        "locations": locations,
        "events": events,
        "movements": movements,
    }

    (HERE / "migration-data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "places-to-geocode.json").write_text(
        json.dumps([
            {"place": item["label"], "query": item["geocode_query"], "precision": item["precision"]}
            for item in locations if item["geocode_query"]
        ], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    features = []
    for event in events:
        location = places[event["location_id"]]
        if location["latitude"] is None:
            continue
        features.append({
            "type": "Feature",
            "id": event["event_id"],
            "geometry": {"type": "Point", "coordinates": [location["longitude"], location["latitude"]]},
            "properties": {key: value for key, value in event.items() if key not in {"location_id"}},
        })
    geojson = {"type": "FeatureCollection", "features": features}
    (HERE / "migration-events.geojson").write_text(json.dumps(geojson, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    branch_counts = Counter(event["branch"] for event in events if event["year_min"] is not None)
    line_counts = Counter(event["line"] for event in events if event["year_min"] is not None)
    print(json.dumps({"counts": payload["metadata"]["counts"], "lines": line_counts, "branches": branch_counts}, indent=2))


if __name__ == "__main__":
    main()
