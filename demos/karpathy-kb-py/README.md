# karpathy-kb-py

Python backend for the Karpathy knowledge-base demo.

- `extract_concepts(text, n=5)` — pulls top-N single-word keywords using
  [`yake`](https://github.com/LIAAD/yake) (pure Python) and cross-links them via
  co-occurring sentences. Falls back to a frequency heuristic when `yake` is
  unavailable.
- `lint_kb(concepts)` — surfaces `orphaned`, `short_summaries`, `duplicates`.

## Usage
```bash
python cli.py extract --text "Sierra is winning customer service ..." --n 5
python cli.py lint --concepts-json concepts.json
pytest tests/
```
