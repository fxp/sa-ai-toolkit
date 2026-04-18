# hypothesis-py

Python backend for the Hypothesis annotator demo.

Stdlib-only (`re`) heuristics classify each sentence into one of four tags:

| Tag | Color | Trigger |
| --- | --- | --- |
| `data` | red | numbers, `%`, `$`, years |
| `contrarian` | yellow | but / however / contrary / 虽然 / 但是 |
| `strategy` | green | should / must / strategy / 应该 / 策略 |
| `critique` | blue | fallback — first undecided sentence |

## Usage
```bash
python cli.py annotate --text "Revenue hit $12B in 2025. However, profits fell."
python cli.py annotate --file article.txt
pytest tests/
```
