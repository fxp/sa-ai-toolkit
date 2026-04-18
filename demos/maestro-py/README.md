# maestro-py

Python backend for the Maestro mobile test-simulator demo.

- `parse_yaml(text)` — parses Maestro flows via `PyYAML` (with a regex
  fallback). Returns `{"appId", "name", "steps": [{"cmd", "arg"}]}`.
- `simulate_execution(parsed)` — returns an execution trace with screen
  transitions for the SmartPet demo.

## Usage
```bash
python cli.py parse --yaml-file flow.yaml
python cli.py simulate --yaml-file flow.yaml
pytest tests/
```
