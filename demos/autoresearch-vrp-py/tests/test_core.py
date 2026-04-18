"""Tests for AutoResearch-for-VRP core logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (  # noqa: E402
    VARIANTS, NUM_ITERATIONS,
    build_benchmark, evaluate, run_iteration, run_full,
    get_program_md, get_instance_payload,
)


def test_benchmark_deterministic():
    a = build_benchmark()
    b = build_benchmark()
    assert [(c.x, c.y, c.demand) for c in a.customers] == [(c.x, c.y, c.demand) for c in b.customers]


def test_benchmark_shape():
    inst = build_benchmark()
    assert inst.num_vehicles == 4
    assert inst.capacity == 60
    assert len(inst.customers) == 26  # 1 depot + 25 customers
    assert inst.depot.id == 0
    assert inst.depot.demand == 0
    # total demand fits within fleet
    total = sum(c.demand for c in inst.customers)
    assert total <= inst.num_vehicles * inst.capacity


def test_variant_count_and_metadata():
    assert NUM_ITERATIONS == 10
    assert len(VARIANTS) == 10
    for v in VARIANTS:
        assert callable(v["fn"])
        assert v["name"] and v["name_zh"]
        assert v["hypothesis"] and v["hypothesis_zh"]


def test_every_variant_visits_every_customer():
    inst = build_benchmark()
    all_custs = set(range(1, len(inst.customers)))
    for v in VARIANTS:
        routes = v["fn"](inst)
        covered = set(c for r in routes for c in r)
        assert covered == all_custs, f"{v['name']} missed customers: {all_custs - covered}"


def test_feasibility_of_key_variants():
    """Every variant from v2 onward should produce capacity-feasible routes."""
    inst = build_benchmark()
    for i in (2, 3, 4, 5, 6, 7, 8, 9):
        routes = VARIANTS[i]["fn"](inst)
        m = evaluate(inst, routes)
        assert m["over_capacity"] == 0, f"v{i} {VARIANTS[i]['name']} overloads: {m}"
        assert m["missing_customers"] == 0


def test_clarke_wright_beats_nn():
    inst = build_benchmark()
    nn_d = evaluate(inst, VARIANTS[2]["fn"](inst))["total_distance"]
    cw_d = evaluate(inst, VARIANTS[4]["fn"](inst))["total_distance"]
    assert cw_d < nn_d, f"Clarke-Wright ({cw_d}) should beat NN+cap ({nn_d})"


def test_lns_at_least_matches_cw():
    """LNS should never be worse than the CW it starts from."""
    inst = build_benchmark()
    cw_d = evaluate(inst, VARIANTS[4]["fn"](inst))["total_distance"]
    lns_d = evaluate(inst, VARIANTS[9]["fn"](inst))["total_distance"]
    assert lns_d <= cw_d + 0.5


def test_trajectory_shows_major_improvement():
    full = run_full()
    first = full["results"][0]["metric"]["total_distance"]
    assert full["best_distance"] <= first * 0.6, f"only improved {first} → {full['best_distance']}"


def test_at_least_two_reverts():
    full = run_full()
    reverted = sum(1 for r in full["results"] if not r["kept"])
    assert reverted >= 2


def test_run_iteration_contract():
    res = run_iteration(4, lang="en")
    required = {"iter", "name", "name_zh", "hypothesis", "hypothesis_zh",
                "code", "metric", "routes", "feasible", "kept",
                "prev_best", "best_so_far", "commentary", "num_iterations"}
    assert required.issubset(res.keys())
    assert res["iter"] == 4
    assert "def " in res["code"]
    assert all({"vehicle", "customers", "path", "distance", "load"} <= set(r) for r in res["routes"])


def test_program_md_reflects_instance():
    md_en = get_program_md("en")
    assert "25 customers" in md_en
    md_zh = get_program_md("zh")
    assert "25" in md_zh


def test_instance_payload_shape():
    p = get_instance_payload()
    assert p["num_customers"] == 25
    assert p["num_vehicles"] == 4
    assert p["capacity"] == 60
    assert "depot" in p
    assert len(p["customers"]) == 25
