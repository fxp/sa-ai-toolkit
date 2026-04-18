"""Tests for AutoResearch-for-Scheduling core logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (  # noqa: E402
    VARIANTS, NUM_ITERATIONS,
    build_benchmark, evaluate, run_iteration, run_full, get_program_md,
    get_instance_payload,
)


def test_benchmark_is_deterministic():
    a = build_benchmark()
    b = build_benchmark()
    assert [o.proc_time for o in a.orders] == [o.proc_time for o in b.orders]
    assert a.num_machines == b.num_machines == 3


def test_benchmark_shape():
    inst = build_benchmark()
    assert len(inst.orders) == 28
    assert inst.num_machines == 3
    assert sum(o.proc_time for o in inst.orders) > 150  # substantial workload


def test_variant_count():
    assert NUM_ITERATIONS == 10
    assert len(VARIANTS) == 10
    # every variant has a callable solver + both-language metadata
    for v in VARIANTS:
        assert callable(v["fn"])
        assert v["name"] and v["name_zh"]
        assert v["hypothesis"] and v["hypothesis_zh"]


def test_each_variant_produces_complete_schedule():
    inst = build_benchmark()
    for v in VARIANTS:
        sched = v["fn"](inst)
        assert len(sched) == len(inst.orders), f"{v['name']} missed orders"
        # every order scheduled exactly once
        assert sorted(s["order_id"] for s in sched) == sorted(o.id for o in inst.orders)
        # no machine overlap
        for m in range(inst.num_machines):
            seq = sorted((s for s in sched if s["machine"] == m), key=lambda s: s["start"])
            for a, b in zip(seq, seq[1:]):
                assert a["end"] <= b["start"], f"{v['name']} overlap on M{m}"


def test_trajectory_reaches_strong_improvement():
    """Baseline WT should drop by at least 50% through the trajectory."""
    full = run_full()
    wts = [r["metric"]["weighted_tardiness"] for r in full["results"]]
    assert full["best_wt"] <= wts[0] * 0.5, f"only improved {wts[0]} → {full['best_wt']}"


def test_at_least_one_reverted_hypothesis():
    """Demo authenticity: some variants should be rejected."""
    full = run_full()
    reverted = sum(1 for r in full["results"] if not r["kept"])
    assert reverted >= 2, "trajectory should show some dead-end hypotheses"


def test_run_iteration_contract():
    res = run_iteration(3, lang="en")
    required = {"iter", "name", "name_zh", "hypothesis", "hypothesis_zh",
                "code", "metric", "schedule", "kept", "prev_best",
                "best_so_far", "commentary", "num_iterations"}
    assert required.issubset(res.keys())
    assert res["iter"] == 3
    assert "def " in res["code"]  # real Python source
    assert res["num_iterations"] == NUM_ITERATIONS


def test_run_iteration_out_of_range():
    import pytest
    with pytest.raises(IndexError):
        run_iteration(99)


def test_evaluate_matches_schedule():
    inst = build_benchmark()
    sched = VARIANTS[0]["fn"](inst)
    m = evaluate(inst, sched)
    # manual recomputation
    expected_wt = sum(s["weight"] * max(0, s["end"] - s["due_date"]) for s in sched)
    assert m["weighted_tardiness"] == expected_wt
    assert m["makespan"] == max(s["end"] for s in sched)


def test_program_md_reflects_instance():
    md_en = get_program_md("en")
    assert "28-order" in md_en
    assert "seed=77" in md_en
    md_zh = get_program_md("zh")
    assert "28" in md_zh
    assert "seed=77" in md_zh


def test_instance_payload_shape():
    p = get_instance_payload()
    assert p["num_orders"] == 28
    assert p["num_machines"] == 3
    assert len(p["orders"]) == 28
    assert all({"id", "proc_time", "due_date", "weight"} <= set(o) for o in p["orders"])
