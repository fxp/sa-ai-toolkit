# PPT Gen (Python core)

Generate real PPTX files via python-pptx with 5 templates (cover, agenda, data,
split, summary) and 4 themes (blue-orange, red-gold, green-mint, purple-pink).

## Install & run

```
pip install -r requirements.txt
python cli.py gen --config config.json --output deck.pptx
```

Programmatic:

```python
from core import generate_pptx
pptx_bytes = generate_pptx("Title", "Sub", [{"template": "cover", "fields": {...}}], theme="blue-orange")
```
