# Canonical family-tree source of truth

This GitHub repository is the canonical project repository. Do not treat chat history, the deployed GitHub Pages site, an online Ancestry tree, or files copied elsewhere as authoritative.

## Authority order

1. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree.ged` is the authoritative family-tree structure.
2. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json` is its synchronized machine-readable mirror.
3. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Index.xlsx` is the synchronized human-review workbook.
4. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Sources.md`, the source inventory, and `records/` preserve evidence and provenance.
5. `public/data/` and `public/records/` contain deployment copies only. They are derived outputs, never independent sources of truth.

If any derived file conflicts with the canonical GEDCOM, use the GEDCOM and repair the derived file. Preserve documented conflicts and uncertainty rather than silently resolving them.

## Change discipline

- Treat preserved source records as read-only evidence.
- Never infer an unknown relationship.
- Preserve citations, confidence, conflicts, provenance, and living-person privacy.
- Incorporate approved research results into the GEDCOM, canonical JSON, workbook, source ledger, inventory, and validation set together.
- Rebuild and validate the migration bundle after any approved change to people, families, dates, places, privacy status, or source references.
- Keep collateral extension bounded through the grandparents' generation while retaining direct ancestry already present.

## Controlling corrections

- Jan Muller Vollmer is Fredric's biological mother.
- Mary Alice Thoren and Henry Richard Vollmer are Chris Vollmer's biological parents; Mary Alice was Henry's first wife, before Jan.
- William J. “Bill” Thoren and Alice Gallaher Thoren are Mary Alice's parents, documented in the 1950 census.
- Jan is Chris's stepmother.
- Chris is Fredric's paternal half-brother.
- Charles Vollmer's middle name is Frederic.
- Janet Chaffee was an error; the child is James Chaffee.
- Mary Gene's husband is Elmer James Chaffee Jr.

These corrections override older chat claims, copied trees, and conflicting derivative displays unless new evidence is explicitly reviewed and approved.
