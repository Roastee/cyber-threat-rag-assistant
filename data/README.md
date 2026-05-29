# Data Directory

> This directory contains threat intelligence data used by the RAG pipeline.
>
> **⚠️ Do NOT commit sensitive or proprietary data to version control.**
> The contents of `raw/` and `processed/` are gitignored.

## Structure

```
data/
├── raw/                # Original unprocessed documents
│   ├── feeds/          # Threat intelligence feeds (STIX, CSV, JSON)
│   └── reports/        # Threat reports (PDF, DOCX, TXT)
└── processed/          # Chunked and cleaned documents ready for embedding
```

## Adding Data

1. Place raw documents in the appropriate subdirectory under `data/raw/`
2. Run the ingestion pipeline (Sprint 2) to process and index them
3. Processed chunks will be saved to `data/processed/`
