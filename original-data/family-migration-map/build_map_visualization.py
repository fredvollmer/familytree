#!/usr/bin/env python3
"""Inline migration data and map geometry into the embeddable map fragment."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "migration-map.template.html"
OUTPUT = HERE / "family-migration-map.html"
INLINE_OUTPUT = Path("/Users/russell.jowell/.codex/visualizations/2026/09/01/01a05e3c-401f-7fe2-a178-702caea2a955/family-migration-map.html")


def compact_json(path: Path) -> str:
    return json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    rendered = template.replace("__MIGRATION_DATA__", compact_json(HERE / "migration-data.json"))
    rendered = rendered.replace("__WORLD_TOPOLOGY__", compact_json(HERE / "world-countries-110m.topojson"))
    if "__MIGRATION_DATA__" in rendered or "__WORLD_TOPOLOGY__" in rendered:
        raise RuntimeError("Visualization placeholders were not replaced")
    OUTPUT.write_text(rendered, encoding="utf-8")
    INLINE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    INLINE_OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"Wrote {INLINE_OUTPUT} ({INLINE_OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
