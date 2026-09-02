#!/usr/bin/env python3
"""Resolve family-tree places locally against a GeoNames cities500 dump.

Usage:
    python geocode_places_offline.py /path/to/cities500.txt /path/to/country-dumps

No family-derived label is transmitted anywhere.  Coordinates are copied from
GeoNames locality records, or (for broad regions) calculated as an unweighted
centroid of GeoNames localities in that region.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE / "places-to-geocode.json"
OUTPUT = HERE / "geocoded-locations.json"

US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "California": "CA", "Connecticut": "CT", "Kentucky": "KY",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "New Hampshire": "NH",
    "Montana": "MT", "New Jersey": "NJ", "New York": "NY", "North Carolina": "NC", "Ohio": "OH",
    "Oregon": "OR", "South Carolina": "SC", "Texas": "TX", "Virginia": "VA",
    "Washington": "WA",
}

COUNTRY_HINTS = {
    "England": "GB", "France": "FR", "Germany": "DE", "Bavaria": "DE",
    "Canada": "CA", "Newfoundland": "CA", "United States": "US",
}

LOCALITY_OVERRIDES = {
    "Alsace, France": "Strasbourg",
    "Bavaria": "Munich",
    "Bullitt County, Kentucky": "Shepherdsville",
    "Buckingham County, Virginia": "Buckingham",
    "Brunswick County, Virginia": "Lawrenceville",
    "Camden District, South Carolina": "Camden",
    "Change Islands, Newfoundland": "Change Islands",
    "Fairfield District, South Carolina": "Winnsboro",
    "Hampshire, England": "Winchester",
    "Hursley, Hampshire, England": "Hursley",
    "Jefferson County, Kentucky": "Louisville",
    "Kershaw District, South Carolina": "Camden",
    "Los Angeles County, California": "Los Angeles",
    "Moscow (now Leicester), Livingston, New York (compiled genealogy)": "Leicester",
    "Newfoundland": "Gander",
    "Oakland County, Michigan": "Pontiac",
    "Oxfordshire, England": "Oxford",
    "Perdue Hill, Monroe County, Alabama": "Perdue Hill",
    "Plymouth Colony": "Plymouth",
    "Plymouth or Eastham, Massachusetts (scholarly reconstruction)": "Eastham",
    "Prince George County, Virginia": "Prince George",
    "Simsbury, Hartford, Connecticut": "Simsbury Center",
    "Sparks, Maryland": "Sparks",
    "Stratham, New Hampshire": "Stratham",
    "Stratham, New Hampshire (compiled genealogy)": "Stratham",
    "Surry County, Virginia": "Surry",
    "Wayne County, Michigan": "Detroit",
    "York, Livingston, New York": "York Hamlet",
    "probably Fingringhoe, Essex, England": "Fingringhoe",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("saint ", "st ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def read_gazetteer(path: Path):
    rows = []
    by_name = defaultdict(list)
    by_region = defaultdict(list)
    by_country = defaultdict(list)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 19:
                continue
            row = {
                "geonameid": int(fields[0]),
                "name": fields[1],
                "asciiname": fields[2],
                "alternatenames": fields[3].split(",") if fields[3] else [],
                "latitude": float(fields[4]),
                "longitude": float(fields[5]),
                "countrycode": fields[8],
                "admin1code": fields[10],
                "admin2code": fields[11],
                "population": int(fields[14] or 0),
            }
            rows.append(row)
            names = {row["name"], row["asciiname"], *row["alternatenames"]}
            for name in names:
                if name:
                    by_name[norm(name)].append(row)
            by_region[(row["countrycode"], row["admin1code"])].append(row)
            by_country[row["countrycode"]].append(row)
    return rows, by_name, by_region, by_country


def target_for_place(place: str) -> str:
    target = LOCALITY_OVERRIDES.get(place)
    if target:
        return target
    target = re.sub(r"^(probably|near)\s+", "", place, flags=re.I).split(",", 1)[0]
    target = re.sub(r"\s*\([^)]*\)\s*", "", target).strip()
    return re.sub(r"\s+County$", "", target, flags=re.I)


def add_exact_country_matches(country_dir: Path, targets: set[str], by_name) -> None:
    """Scan full GeoNames country dumps without retaining unrelated records."""
    for path in sorted(country_dir.glob("??.txt")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 19 or fields[6] != "P":
                    continue
                names = {fields[1], fields[2], *(fields[3].split(",") if fields[3] else [])}
                matched = {norm(name) for name in names if norm(name) in targets}
                if not matched:
                    continue
                row = {
                    "geonameid": int(fields[0]), "name": fields[1], "asciiname": fields[2],
                    "alternatenames": fields[3].split(",") if fields[3] else [],
                    "latitude": float(fields[4]), "longitude": float(fields[5]),
                    "countrycode": fields[8], "admin1code": fields[10],
                    "admin2code": fields[11], "population": int(fields[14] or 0),
                }
                for name in matched:
                    by_name[name].append(row)


def infer_country(place: str, query: str) -> str:
    combined = f"{place}, {query}"
    for hint, code in COUNTRY_HINTS.items():
        if hint.lower() in combined.lower():
            return code
    if any(state.lower() in combined.lower() for state in US_STATES):
        return "US"
    return "US"


def infer_admin1(place: str, query: str, country: str) -> str | None:
    if country == "US":
        combined = f"{place}, {query}"
        for state, code in US_STATES.items():
            if re.search(rf"\b{re.escape(state)}\b", combined, re.I):
                return code
    return None


def centroid(rows: list[dict]) -> tuple[float, float] | None:
    if not rows:
        return None
    return (
        round(sum(row["latitude"] for row in rows) / len(rows), 6),
        round(sum(row["longitude"] for row in rows) / len(rows), 6),
    )


def candidate_score(row: dict, target: str) -> tuple:
    names = [row["name"], row["asciiname"], *row["alternatenames"]]
    exact = any(norm(name) == norm(target) for name in names)
    similarity = max((difflib.SequenceMatcher(None, norm(target), norm(name)).ratio() for name in names if name), default=0)
    return (1 if exact else 0, similarity, row["population"])


def resolve(item: dict, by_name, by_region, by_country) -> dict:
    place = item["place"]
    query = item["query"]
    country = infer_country(place, query)
    admin1 = infer_admin1(place, query, country)

    broad_place = re.sub(r"\s*\([^)]*\)\s*", "", place).strip()
    if broad_place in US_STATES:
        rows = by_region[("US", US_STATES[broad_place])]
        latlon = centroid(rows)
        return make_centroid(place, query, latlon, f"GeoNames locality centroid for {broad_place}, US", len(rows))
    if place in {"England", "Germany", "Canada"}:
        country_code = {"England": "GB", "Germany": "DE", "Canada": "CA"}[place]
        rows = by_country[country_code]
        latlon = centroid(rows)
        return make_centroid(place, query, latlon, f"GeoNames locality centroid for {place}", len(rows))

    target = target_for_place(place)

    candidates = list(by_name.get(norm(target), []))
    candidates = [row for row in candidates if row["countrycode"] == country]
    if admin1:
        regional = [row for row in candidates if row["admin1code"] == admin1]
        candidates = regional

    if not candidates:
        pool = by_region.get((country, admin1), []) if admin1 else by_country.get(country, [])
        scored = [(candidate_score(row, target), row) for row in pool]
        scored = [pair for pair in scored if pair[0][1] >= 0.84]
        candidates = [max(scored, key=lambda pair: pair[0])[1]] if scored else []

    if not candidates:
        return {
            "status": "unresolved",
            "latitude": None,
            "longitude": None,
            "display_name": None,
            "geocoder": "GeoNames offline gazetteer",
            "query": query,
            "match_method": "no-local-match",
        }

    best = max(candidates, key=lambda row: candidate_score(row, target))
    return {
        "status": "resolved",
        "latitude": round(best["latitude"], 6),
        "longitude": round(best["longitude"], 6),
        "display_name": f"{best['name']} ({best['countrycode']}-{best['admin1code']})",
        "geocoder": "GeoNames offline gazetteer",
        "geonameid": best["geonameid"],
        "query": query,
        "match_method": "override-locality" if place in LOCALITY_OVERRIDES else "locality-name",
        "matched_name": best["name"],
        "matched_country": best["countrycode"],
        "matched_admin1": best["admin1code"],
    }


def make_centroid(place: str, query: str, latlon, display: str, count: int) -> dict:
    if not latlon:
        return {
            "status": "unresolved", "latitude": None, "longitude": None,
            "display_name": None, "geocoder": "GeoNames offline gazetteer",
            "query": query, "match_method": "no-region-match",
        }
    return {
        "status": "resolved",
        "latitude": latlon[0],
        "longitude": latlon[1],
        "display_name": display,
        "geocoder": "GeoNames offline gazetteer",
        "query": query,
        "match_method": "derived-region-centroid",
        "centroid_locality_count": count,
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Pass GeoNames cities500.txt and a directory of extracted country dumps")
    gazetteer_path = Path(sys.argv[1]).resolve()
    country_dir = Path(sys.argv[2]).resolve()
    places = json.loads(INPUT.read_text(encoding="utf-8"))
    _, by_name, by_region, by_country = read_gazetteer(gazetteer_path)
    targets = {norm(target_for_place(item["place"])) for item in places}
    add_exact_country_matches(country_dir, targets, by_name)
    results = {item["place"]: resolve(item, by_name, by_region, by_country) for item in places}
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    unresolved = [place for place, value in results.items() if value["status"] != "resolved"]
    print(json.dumps({"resolved": len(results) - len(unresolved), "unresolved": unresolved}, indent=2))


if __name__ == "__main__":
    main()
