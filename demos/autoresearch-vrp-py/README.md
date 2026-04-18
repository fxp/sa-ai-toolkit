# AutoResearch for VRP

Same autonomous algorithm-discovery loop as the scheduling demo, applied to a
capacitated vehicle-routing problem (CVRP). 25 customers around a central depot,
4 vehicles × capacity 60, minimize total travel distance with no capacity
overflow.

- **Benchmark harness** — `build_benchmark(seed=11)` + `evaluate(inst, routes)`.
- **Solver variants (10)** — Random → NN single-tour → NN+capacity → Sweep →
  Clarke-Wright → CW+2-opt → CW+Or-opt → CW+relocate → CW+VND → CW+LNS.
- **Loop** — run variant, score against frozen benchmark, keep-or-revert.

Trajectory on the bundled instance:
`1178 → (467 infeasible, reverted) → 691 → (711 reverted) → 566 (CW) → … → 558 (LNS)`
— about 52% total improvement, four hypotheses rejected along the way.

## Usage

    pip install -r requirements.txt
    python cli.py list
    python cli.py iterate --idx 4
    python cli.py full --lang en -o trajectory.md

## Tests

    pytest tests/
