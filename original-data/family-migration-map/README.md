# Family migration map

This directory contains a derived, privacy-aware migration view of the canonical Vollmer family tree. The canonical GEDCOM and JSON under `../final-family-tree/` remain unchanged.

## Deliverables

- `family-migration-map.html` — embeddable interactive map fragment with the current data and world geometry inlined.
- `migration-data.json` — complete application-facing dataset: metadata, normalized locations, birth/death events, and inferred movements.
- `migration-events.geojson` — event points for GIS or mapping libraries.
- `geocoded-locations.json` — auditable coordinate cache, including GeoNames IDs, matching method, original query, and regional-centroid derivations.
- `places-to-geocode.json` — normalized place queue retained for review.
- `world-countries-110m.topojson` — low-resolution map background embedded in the visualization.
- `build_migration_data.py` and `build_map_visualization.py` — reproducible builders.
- `geocode_places_offline.py` — local-only gazetteer matcher. It does not send family place labels to an online service.

## Data model

`migration-data.json` has four top-level members:

- `metadata`: source, privacy rule, date extent, interpretation warnings, and counts.
- `locations`: stable location ID, original canonical wording, normalized geocode query, coordinates, precision, status, and gazetteer provenance.
- `events`: stable event ID, canonical person ID and name, birth/death type, original date/place text, parsed year range, maternal/paternal side, branch, confidence, and canonical source references.
- `movements`: endpoint connections for either `intergenerational` birth-place shifts or `lifetime` birth-to-death displacement. These are analytical inferences, not documented travel routes.

The GeoJSON contains the same resolved event points and their event properties. Ambiguous/unresolved labels remain in `migration-data.json` rather than being assigned guessed coordinates.

## Privacy and interpretation

- People explicitly marked living, or potentially living because they have no death record and a birth within the last 100 years, are excluded. The current build excludes eight people.
- Living dates omitted by the canonical tree are not reconstructed.
- The current data contains 234 place-bearing events, including 220 dated events. Fourteen undated events remain available in the JSON but are not placed on the timeline.
- `Kentucky or Virginia` and `exact death unproved` remain unresolved and unplotted.
- Route lines connect recorded endpoints; they do not assert a path, travel date, residence sequence, or causation.

## Embedding

The map file is an HTML fragment rather than a full document. It can be inserted into an existing application surface. It currently loads pinned D3 and TopoJSON client builds from jsDelivr and includes the family data and boundary geometry inline, so it does not fetch family information at runtime.

For a production web app, use `migration-data.json` as the source of truth for the feature and keep `family-migration-map.html` as the reference implementation. The UI supports timeline playback, maternal/paternal filtering, intergenerational versus lifetime endpoint views, pointer details, and keyboard-focusable location links.

## Coordinate provenance

Coordinates were resolved locally from the 1 September 2026 GeoNames `cities500` and country dumps for the United States, United Kingdom, Canada, Germany, and France. Broad state/country labels use an unweighted centroid of relevant `cities500` localities; historic districts and county-level labels use documented overrides to a matching locality or county seat, recorded in the coordinate cache. GeoNames data is licensed under CC BY 4.0: <https://www.geonames.org/>.

The world background is `world-atlas@2` countries-110m data derived from Natural Earth: <https://github.com/topojson/world-atlas>.
