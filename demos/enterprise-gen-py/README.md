# Enterprise Gen (Python core)

Scores 14 AI demo templates against a company profile and generates a full
runbook package (profile, scoring matrix, schedule, markdown runbook).

## Install & run

```
pip install -r requirements.txt
python cli.py score --company Acme --industry banking --pain comp,risk --minutes 90
python cli.py generate --company Acme --industry tech --pain km,collab --minutes 60
```

Scoring formula: `score = 0.4 × pain_match + 0.4 × industry_fit + 0.2 × impact`
