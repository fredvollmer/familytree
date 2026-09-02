# Lineage — The Vollmer Family Archive

An interactive, searchable family-history app built from the canonical Vollmer/Muller genealogy package.

> **Canonical repository:** This repository is the project source of truth. The authoritative tree is `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree.ged`; the deployed site and `public/` data are derived views.

## What the site includes

- A pannable and zoomable 308-person family tree
- Person details, relationships, research notes, confidence ratings, and citations
- Highlighted direct ancestors and descendants for the selected person
- Preserved source-record images and PDFs
- A privacy-aware migration map with timeline, maternal/paternal filters, and inferred endpoint connections

## Source of truth and precedence

The repository's authority order is:

1. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree.ged` — authoritative tree structure
2. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json` — synchronized machine-readable mirror
3. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Index.xlsx` — synchronized review workbook
4. `original-data/final-family-tree/Fredric_Vollmer_Complete_Family_Tree_Sources.md`, the source inventory, and preserved records — evidence and provenance

The approved migration bundle is under `original-data/family-migration-map/`. The complete packaged archive is `original-data/Fredric_Vollmer_Complete_Family_Tree_Package.zip`.

The `public/data/` files are deployment copies derived from those originals and are never independently authoritative. Living-person details remain minimized, and inferred migration connections are analytical endpoints rather than documented travel routes. See `AGENTS.md` for the rules future maintainers and automated agents must follow.

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
