# Lineage — The Vollmer Family Archive

An interactive, searchable family-history app built from the canonical Vollmer/Muller genealogy package.

## What the site includes

- A pannable and zoomable 308-person family tree
- Person details, relationships, research notes, confidence ratings, and citations
- Highlighted direct ancestors and descendants for the selected person
- Preserved source-record images and PDFs
- A privacy-aware migration map with timeline, maternal/paternal filters, and inferred endpoint connections

## Source of truth

The authoritative tree is preserved under `original-data/final-family-tree/`, led by:

- `Fredric_Vollmer_Complete_Family_Tree.ged`
- `Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json`
- `Fredric_Vollmer_Complete_Family_Tree_Index.xlsx`
- `Fredric_Vollmer_Complete_Family_Tree_Sources.md`

The approved migration bundle is under `original-data/family-migration-map/`. The complete packaged archive is `original-data/Fredric_Vollmer_Complete_Family_Tree_Package.zip`.

The `public/data/` files are deployment copies derived from those originals. Living-person details remain minimized, and inferred migration connections are analytical endpoints rather than documented travel routes.

## Local development

Requires Node.js 22.13 or newer.

```sh
npm install
npm run dev:github
```

## Production build

```sh
npm run build:github
```

GitHub Actions deploys the `main` branch to GitHub Pages.
