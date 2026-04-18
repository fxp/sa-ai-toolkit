# SA Toolkit (Python core)

Three modules for the full sales-agent workflow.

- `Gen`: `search_company` + `generate_package` (reuses enterprise-gen scorer).
- `Customize`: `replace_terms`, `deepen_demo`, `switch_audience`.
- `Present`: `rehearse` (play-by-play) and `export_email` (Jinja2 template).

## Install & run

```
pip install -r requirements.txt
python cli.py gen --company Tencent
python cli.py customize --package-json p.json --replace "Tencent:Acme"
python cli.py present --package-json p.json --mode email
```
