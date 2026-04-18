# Org-Uplift — METR-style productivity game

Python port of the METR Org-Uplift dice engine. Each "task" gets a
success-rate lookup based on estimated human hours, a dice roll, and a
bottleneck classifier.

## Usage

    python cli.py execute --task "调研AI客服竞品" --player Alice --scenario newco
    python cli.py stats   --tasks-json tasks.json
    python cli.py scenarios

## Tests

    pytest tests/
