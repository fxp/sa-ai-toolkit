# AutoResearch — 23-stage research pipeline

Chat an idea, get a research report. Four of the 23 stages hit DuckDuckGo
for real web sources; the rest are simulated reasoning work. Final stage
emits a Markdown report via Jinja2 template.

## Usage

    pip install -r requirements.txt
    python cli.py list
    python cli.py stage --topic "Agentic AI in 2026" --idx 2
    python cli.py full  --topic "Agentic AI in 2026" --lang en -o report.md

## Tests

    pytest tests/
