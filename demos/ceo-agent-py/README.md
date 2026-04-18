# CEO Agent (Python core)

Synthetic CEO cockpit for any company. Deterministic — same company name always
returns the same numbers so the demo is reproducible.

## Install & run

```
pip install -r requirements.txt
python cli.py all --company "NewCo Inc" --lang en
python cli.py brief --company "NewCo Inc" --brief-idx 1 --lang zh
```

## What it returns

`CEOAgent.morning_brief / metrics / decisions / mood_heatmap / competitor_feed / action_queue`
— all JSON-serializable, all bilingual (en/zh). API handlers at `api/ceo_*.py`
wrap each method.
