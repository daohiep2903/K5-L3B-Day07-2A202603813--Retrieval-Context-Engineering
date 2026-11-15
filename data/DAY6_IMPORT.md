# Day 6 corpus imported for Day 7

Actual corpus: IETF RFC 6749 sections 2-7, strategy B, 116 chunks from 41 non-overlapping source units. `page` means a sequential source unit, not an original RFC page. Data provenance and model settings are recorded in `day6_import.json`.

`chunks.json` follows the Day 7 contract: `id`, `source_id`, `source`, `page`, `text`, `metadata`. IDs, source paths, source-unit positions, text and metadata are preserved from Day 6. No answer or gold label is added to chunks.

The compatible embedding model is `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 dimensions; the previous Qdrant collection is `day6_B`. Connection is a later step: this import does not itself query or copy vectors.

From the Day 7 root, reproduce with:

```powershell
python scripts/import_day6.py --day6 "<absolute-path-to-Day6-project>"
```

All IDs must be unique. Each chunk must equal its exact source substring, stay inside its source unit and have the correct actual section. The import refuses to overwrite differing existing corpus files.

Keep `RFC6749_NOTICES.txt`, `RIGHTS_REVIEW.md` and original source attribution with redistributed corpus and derived excerpts. No Day 6 benchmark was copied: prepare Day 7 dev/test and no-evidence cases before retrieval experiments. No real agent or retrieval benchmark has run in this step.
