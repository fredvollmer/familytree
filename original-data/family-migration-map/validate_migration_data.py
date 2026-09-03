#!/usr/bin/env python3
"""Integrity checks for the derived migration bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main() -> None:
    data = json.loads((HERE / "migration-data.json").read_text(encoding="utf-8"))
    geojson = json.loads((HERE / "migration-events.geojson").read_text(encoding="utf-8"))
    locations = {item["location_id"]: item for item in data["locations"]}
    events = {item["event_id"]: item for item in data["events"]}

    assert len(events) == data["metadata"]["counts"]["events"]
    assert len(locations) == data["metadata"]["counts"]["locations"]
    assert len(data["movements"]) == data["metadata"]["counts"]["movements"]
    assert sum(event["year_min"] is not None for event in events.values()) == data["metadata"]["counts"]["dated_events"]
    assert sum(location["latitude"] is not None for location in locations.values()) == data["metadata"]["counts"]["resolved_locations"]

    for event in events.values():
        assert event["location_id"] in locations
        assert event["side"] in {"Maternal", "Paternal", "Other"}
        assert event["line"] in {"Muller", "Vollmer", "Fischer", "VanHoose"}
    for movement in data["movements"]:
        assert movement["from_event_id"] in events
        assert movement["to_event_id"] in events
        assert locations[movement["from_location_id"]]["latitude"] is not None
        assert locations[movement["to_location_id"]]["latitude"] is not None
        assert movement["line"] in {"Muller", "Vollmer", "Fischer", "VanHoose"}

    resolved_event_count = sum(locations[event["location_id"]]["latitude"] is not None for event in events.values())
    assert len(geojson["features"]) == resolved_event_count
    assert all(feature["geometry"]["type"] == "Point" for feature in geojson["features"])

    # Current living/potentially living records must never leak into the bundle.
    excluded_ids = {"I001", "I002", "I269", "I272", "I273", "I322", "I323", "I331", "I334"}
    assert not excluded_ids.intersection(event["person_id"] for event in events.values())

    html = (HERE / "family-migration-map.html").read_text(encoding="utf-8")
    assert len(html.encode("utf-8")) < 1_000_000
    assert "__MIGRATION_DATA__" not in html and "__WORLD_TOPOLOGY__" not in html
    assert not re.search(r"<!doctype|<html|<head|<body", html, re.I)
    print("Migration data validation passed")


if __name__ == "__main__":
    main()
