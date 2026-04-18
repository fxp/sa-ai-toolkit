# AutoResearch for Scheduling

Autonomous algorithm-discovery loop applied to weighted-tardiness minimization
on a fixed 28-order / 3-machine benchmark. Inspired by
[karpathy/autoresearch](https://github.com/karpathy/autoresearch): instead of
letting an agent mutate `train.py` to improve an LLM, we let it mutate
`solver.py` to improve a scheduling heuristic.

- **Benchmark harness** — `build_benchmark(seed=77)` + `evaluate(inst, schedule)` (frozen).
- **Editable file** — `solver.py` equivalent: 10 solver variants mirror what an
  autoresearch agent would propose over a night of iteration
  (Random → FIFO → LPT → EDD → SPT → WSPT → ATC → ATC+swap → ATC+2-opt → ATC+SA).
- **Loop** — run variant, compute real WT, keep-or-revert against the running best.

Trajectory on the bundled instance: `974 → 944 → (1219 reverted) → 359 → (665 reverted) →
(454 reverted) → 243 → 219 → (219 reverted) → 187` — an 81% drop, with four dead-end
hypotheses rejected.

## Usage

    pip install -r requirements.txt
    python cli.py list
    python cli.py iterate --idx 6
    python cli.py full --lang en -o trajectory.md

## Tests

    pytest tests/
