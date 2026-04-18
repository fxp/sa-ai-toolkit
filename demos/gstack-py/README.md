# gstack-py

Python backend for the gstack terminal demo.

Pure-Python: no external services. `core.run_command(command, user_input)` returns a
list of `{delay_ms, text, class}` script items that the frontend replays as a
typewriter animation.

## Commands
- `office-hours` — six YC-style forcing questions (uses `--input`)
- `autoplan` — CEO + design + eng review (three phases)
- `qa` — 47 tests, 3 fail, 3 atomic fixes, all green
- `ship` — sync main, tests, push, PR

## Usage
```bash
python cli.py run --command office-hours --input "my startup idea"
pytest tests/
```
