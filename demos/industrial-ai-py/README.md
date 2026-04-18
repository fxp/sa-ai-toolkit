# Industrial AI — 4-layer pipeline

Thin wrapper around `api/_pipeline.py`: perception (SAM3 + SAM-Audio) →
prediction (TimesFM) → ontology trace → LLM diagnosis.

## Usage

    python cli.py detect
    python cli.py predict
    python cli.py diagnose
    python cli.py run --output report.json

## Tests

    pytest tests/
