# Performance Notes

This repo includes a lightweight benchmark script for the MVP data scale targets.

## Run

```bash
python scripts/perf_bench.py
```

Optional flags:

```bash
python scripts/perf_bench.py --books 100 --concepts 500 --notes 1000
```

The script prints query timings for representative lookups (books list, depth filter,
concepts by book, and FTS5 note search). Use this as a quick sanity check while
developing CLI commands.
