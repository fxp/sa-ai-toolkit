"""
AutoResearch for Scheduling — autonomous algorithm-discovery loop applied to
weighted-tardiness minimization on a fixed 20-order / 3-machine benchmark.

Mirrors the karpathy/autoresearch pattern:
    - Fixed instance + fixed evaluator = the "benchmark harness" (ground truth).
    - A sequence of solver variants = the agent's edits to solver.py over time.
    - Each iteration runs real Python, gets a real metric, and is kept or reverted.

No LLM is called during the demo. The 10 solver variants below are hand-authored
to mirror what an autoresearch agent would propose (simple heuristics → local
search → metaheuristics), including two deliberate dead-ends that get reverted.
"""
from __future__ import annotations

import inspect
import math
import random
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Instance & evaluator  (the "benchmark harness" — never edited by the agent)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Order:
    id: int
    proc_time: int    # processing hours
    due_date: int     # hours from t=0
    weight: int       # 1 (low) — 5 (critical)


@dataclass(frozen=True)
class Instance:
    orders: tuple[Order, ...]
    num_machines: int


def build_benchmark(seed: int = 77) -> Instance:
    """Deterministic 28-order / 3-machine instance.
    Tight due dates (15-55h) versus ~208h of total work → guaranteed tardiness;
    ATC + local search + SA beats every single-pass dispatch rule.
    """
    rng = random.Random(seed)
    orders = []
    for i in range(28):
        p = rng.randint(3, 11)
        d = rng.randint(15, 55)
        w = rng.choices([1, 2, 3, 4, 5], weights=[3, 3, 3, 2, 1])[0]
        orders.append(Order(id=i, proc_time=p, due_date=d, weight=w))
    return Instance(orders=tuple(orders), num_machines=3)


def _assemble_schedule(inst: Instance, order_sequence: list[Order]) -> list[dict]:
    """List-schedule: each order goes to the earliest-available machine."""
    avail = [0] * inst.num_machines
    sched: list[dict] = []
    for o in order_sequence:
        m = min(range(inst.num_machines), key=lambda k: avail[k])
        start = avail[m]
        end = start + o.proc_time
        avail[m] = end
        sched.append({
            "order_id": o.id, "machine": m,
            "start": start, "end": end,
            "weight": o.weight, "due_date": o.due_date, "proc_time": o.proc_time,
            "tardy": max(0, end - o.due_date),
        })
    return sched


def evaluate(inst: Instance, schedule: list[dict]) -> dict:
    wt = sum(s["weight"] * s["tardy"] for s in schedule)
    makespan = max(s["end"] for s in schedule) if schedule else 0
    num_tardy = sum(1 for s in schedule if s["tardy"] > 0)
    return {
        "weighted_tardiness": wt,
        "makespan": makespan,
        "num_tardy": num_tardy,
        "num_orders": len(schedule),
    }


# ---------------------------------------------------------------------------
# Solver variants  (the file "solver.py" — agent edits this across iterations)
# ---------------------------------------------------------------------------

def solver_random(inst: Instance) -> list[dict]:
    """v0 — baseline: shuffle orders, list-schedule."""
    rng = random.Random(0)
    seq = list(inst.orders)
    rng.shuffle(seq)
    return _assemble_schedule(inst, seq)


def solver_fifo(inst: Instance) -> list[dict]:
    """v1 — order by order-id (arrival order)."""
    return _assemble_schedule(inst, sorted(inst.orders, key=lambda o: o.id))


def solver_lpt(inst: Instance) -> list[dict]:
    """v2 — longest processing time first.
    Hypothesis: do big jobs early so they don't block finishing.
    (Usually worse for weighted tardiness — we expect to revert.)
    """
    return _assemble_schedule(inst, sorted(inst.orders, key=lambda o: -o.proc_time))


def solver_edd(inst: Instance) -> list[dict]:
    """v3 — earliest due date first."""
    return _assemble_schedule(inst, sorted(inst.orders, key=lambda o: o.due_date))


def solver_spt(inst: Instance) -> list[dict]:
    """v4 — shortest processing time first.
    Hypothesis: finish more jobs early, lower avg tardiness.
    (Ignores due dates — usually worse than EDD.)
    """
    return _assemble_schedule(inst, sorted(inst.orders, key=lambda o: o.proc_time))


def solver_wspt(inst: Instance) -> list[dict]:
    """v5 — weighted shortest processing time: priority = proc_time / weight."""
    return _assemble_schedule(inst, sorted(inst.orders, key=lambda o: o.proc_time / o.weight))


def solver_atc(inst: Instance, K: float = 2.0) -> list[dict]:
    """v6 — Apparent Tardiness Cost (Vepsalainen & Morton, 1987).
    Dynamic priority that blends weight/proc_time with remaining slack.
    """
    pbar = sum(o.proc_time for o in inst.orders) / len(inst.orders)
    remaining = list(inst.orders)
    avail = [0] * inst.num_machines
    sched: list[dict] = []
    while remaining:
        m = min(range(inst.num_machines), key=lambda k: avail[k])
        t = avail[m]
        def priority(o: Order) -> float:
            slack = max(o.due_date - o.proc_time - t, 0)
            return -(o.weight / o.proc_time) * math.exp(-slack / (K * pbar))
        pick = min(remaining, key=priority)
        start, end = t, t + pick.proc_time
        avail[m] = end
        sched.append({
            "order_id": pick.id, "machine": m,
            "start": start, "end": end,
            "weight": pick.weight, "due_date": pick.due_date, "proc_time": pick.proc_time,
            "tardy": max(0, end - pick.due_date),
        })
        remaining.remove(pick)
    return sched


def _reflow_machine(sched: list[dict], m: int, new_order: list[dict]) -> list[dict]:
    """Rebuild schedule with `new_order` on machine m, other machines untouched."""
    out = [s for s in sched if s["machine"] != m]
    t = 0
    for s in new_order:
        ns = dict(s)
        ns["start"] = t
        ns["end"] = t + s["proc_time"]
        ns["tardy"] = max(0, ns["end"] - s["due_date"])
        t = ns["end"]
        out.append(ns)
    return out


def solver_atc_swap(inst: Instance) -> list[dict]:
    """v7 — ATC + adjacent-pair swap on each machine until no improvement."""
    sched = solver_atc(inst)
    best_wt = evaluate(inst, sched)["weighted_tardiness"]
    improved = True
    while improved:
        improved = False
        for m in range(inst.num_machines):
            seq = sorted([s for s in sched if s["machine"] == m], key=lambda s: s["start"])
            for i in range(len(seq) - 1):
                trial = seq[:i] + [seq[i + 1], seq[i]] + seq[i + 2:]
                new_sched = _reflow_machine(sched, m, trial)
                new_wt = sum(s["weight"] * s["tardy"] for s in new_sched)
                if new_wt < best_wt:
                    sched = new_sched
                    best_wt = new_wt
                    improved = True
                    break
            if improved:
                break
    return sched


def solver_atc_2opt(inst: Instance, trials: int = 120) -> list[dict]:
    """v8 — ATC + random 2-opt: sample non-adjacent swaps on same machine."""
    sched = solver_atc_swap(inst)
    best_wt = evaluate(inst, sched)["weighted_tardiness"]
    rng = random.Random(1)
    for _ in range(trials):
        m = rng.randrange(inst.num_machines)
        seq = sorted([s for s in sched if s["machine"] == m], key=lambda s: s["start"])
        if len(seq) < 3:
            continue
        i, j = sorted(rng.sample(range(len(seq)), 2))
        trial = seq[:i] + seq[i:j + 1][::-1] + seq[j + 1:]
        new_sched = _reflow_machine(sched, m, trial)
        new_wt = sum(s["weight"] * s["tardy"] for s in new_sched)
        if new_wt < best_wt:
            sched, best_wt = new_sched, new_wt
    return sched


def solver_atc_sa(inst: Instance, iters: int = 400) -> list[dict]:
    """v9 — ATC + simulated annealing: accept worse moves with prob exp(-ΔWT / T)."""
    sched = solver_atc_2opt(inst)
    best_wt = cur_wt = evaluate(inst, sched)["weighted_tardiness"]
    best_sched = sched
    rng = random.Random(2)
    T0, Tmin = 8.0, 0.15
    for k in range(iters):
        T = T0 * (Tmin / T0) ** (k / max(1, iters - 1))
        m = rng.randrange(inst.num_machines)
        seq = sorted([s for s in sched if s["machine"] == m], key=lambda s: s["start"])
        if len(seq) < 2:
            continue
        i = rng.randrange(len(seq) - 1)
        trial = seq[:i] + [seq[i + 1], seq[i]] + seq[i + 2:]
        new_sched = _reflow_machine(sched, m, trial)
        new_wt = sum(s["weight"] * s["tardy"] for s in new_sched)
        delta = new_wt - cur_wt
        if delta < 0 or rng.random() < math.exp(-delta / max(T, 1e-6)):
            sched, cur_wt = new_sched, new_wt
            if new_wt < best_wt:
                best_wt, best_sched = new_wt, new_sched
    return best_sched


# ---------------------------------------------------------------------------
# Variant catalog  (the agent's research trajectory)
# ---------------------------------------------------------------------------

VARIANTS: list[dict] = [
    {
        "idx": 0, "name": "Random",
        "name_zh": "随机基线",
        "fn": solver_random,
        "hypothesis": "Baseline — no ordering logic. Establishes a reference WT.",
        "hypothesis_zh": "基线方案：无任何排序逻辑，只为建立参考值。",
    },
    {
        "idx": 1, "name": "FIFO",
        "name_zh": "FIFO 先进先出",
        "fn": solver_fifo,
        "hypothesis": "Order-id arrival sequence. Typical human/ERP default.",
        "hypothesis_zh": "按订单ID先后顺序排程。是人工和普通ERP的默认做法。",
    },
    {
        "idx": 2, "name": "LPT",
        "name_zh": "LPT 最长优先",
        "fn": solver_lpt,
        "hypothesis": "Big jobs first so they don't block late in the horizon.",
        "hypothesis_zh": "先做大订单，防止它们拖到后期变延误。",
    },
    {
        "idx": 3, "name": "EDD",
        "name_zh": "EDD 交期优先",
        "fn": solver_edd,
        "hypothesis": "Sort by due date — classic single-machine tardiness heuristic.",
        "hypothesis_zh": "按交期排序——经典的单机延误启发式。",
    },
    {
        "idx": 4, "name": "SPT",
        "name_zh": "SPT 短单优先",
        "fn": solver_spt,
        "hypothesis": "Finish more jobs early to reduce average tardiness.",
        "hypothesis_zh": "先做短单，让更多订单早完成以降低平均延误。",
    },
    {
        "idx": 5, "name": "WSPT",
        "name_zh": "WSPT 加权短单",
        "fn": solver_wspt,
        "hypothesis": "Weighted SPT: priority = proc_time / weight.",
        "hypothesis_zh": "加权SPT：优先级 = 处理时长 / 权重。",
    },
    {
        "idx": 6, "name": "ATC",
        "name_zh": "ATC 动态紧迫度",
        "fn": solver_atc,
        "hypothesis": "Apparent Tardiness Cost — blends WSPT with remaining slack.",
        "hypothesis_zh": "ATC动态规则：加权短单 × 剩余松弛度的指数衰减。",
    },
    {
        "idx": 7, "name": "ATC + pair swap",
        "name_zh": "ATC + 邻位交换",
        "fn": solver_atc_swap,
        "hypothesis": "Greedy 1-opt local search on top of ATC ordering.",
        "hypothesis_zh": "在ATC之上贪心做相邻两单交换的1-opt局部搜索。",
    },
    {
        "idx": 8, "name": "ATC + 2-opt",
        "name_zh": "ATC + 2-opt",
        "fn": solver_atc_2opt,
        "hypothesis": "Random non-adjacent segment reversals, 120 trials.",
        "hypothesis_zh": "在ATC基础上随机采样2-opt区段反转，120次试探。",
    },
    {
        "idx": 9, "name": "ATC + SA",
        "name_zh": "ATC + 模拟退火",
        "fn": solver_atc_sa,
        "hypothesis": "Simulated annealing — accept worse moves to escape local optima.",
        "hypothesis_zh": "模拟退火：按温度概率接受变差的解，跳出局部最优。",
    },
]

NUM_ITERATIONS = len(VARIANTS)


# ---------------------------------------------------------------------------
# Agent narration  (short "commit messages" per iteration, like results.tsv)
# ---------------------------------------------------------------------------

def _commentary(idx: int, metric: dict, prev_best: float | None, kept: bool, lang: str = "en") -> str:
    v = VARIANTS[idx]
    wt = metric["weighted_tardiness"]
    if lang == "zh":
        if idx == 0:
            return f"基线WT={wt:.0f}，作为后续对比参照。"
        delta = wt - prev_best if prev_best is not None else 0
        if kept:
            return f"WT={wt:.0f}，相比已知最优 ↓{-delta:.0f}（{-delta / max(prev_best, 1):.0%}）— 保留为新基线。"
        return f"WT={wt:.0f}，比已知最优差 ↑{delta:.0f}（{delta / max(prev_best, 1):.0%}）— 回滚。假设不成立。"
    if idx == 0:
        return f"Baseline WT={wt:.0f}. Everything later is measured against this."
    delta = wt - prev_best if prev_best is not None else 0
    if kept:
        return f"WT={wt:.0f}, down {-delta:.0f} ({-delta / max(prev_best, 1):.0%}) vs best — kept."
    return f"WT={wt:.0f}, up {delta:.0f} ({delta / max(prev_best, 1):.0%}) vs best — reverted. Hypothesis rejected."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_instance_payload(seed: int = 77) -> dict:
    inst = build_benchmark(seed)
    return {
        "num_machines": inst.num_machines,
        "num_orders": len(inst.orders),
        "orders": [
            {"id": o.id, "proc_time": o.proc_time, "due_date": o.due_date, "weight": o.weight}
            for o in inst.orders
        ],
        "total_work": sum(o.proc_time for o in inst.orders),
        "mean_due": sum(o.due_date for o in inst.orders) / len(inst.orders),
    }


def get_program_md(lang: str = "en") -> str:
    inst = build_benchmark()
    n_orders = len(inst.orders)
    n_machines = inst.num_machines
    total_work = sum(o.proc_time for o in inst.orders)
    if lang == "zh":
        return (
            "# program.md\n\n"
            f"**目标**: 在 {n_orders} 订单 × {n_machines} 机器的固定基准上，"
            "最小化加权延误 WT = Σ wᵢ · max(0, Cᵢ - dᵢ)。\n\n"
            f"**基准**: `build_benchmark(seed=77)` — 不可修改（总工时 {total_work}h，交期普遍偏紧）。\n\n"
            "**评估器**: `evaluate(inst, schedule)` — 不可修改。\n\n"
            "**可编辑文件**: `solver.py` — 任意重写 `solve(inst) -> schedule`。\n\n"
            f"**预算**: 每次运行 < 50ms。保留则更新基线，变差则回滚。\n\n"
            f"**停止条件**: WT 连续 3 轮无改善，或已达 {NUM_ITERATIONS} 轮上限。"
        )
    return (
        "# program.md\n\n"
        f"**Goal**: minimize weighted tardiness "
        f"WT = Σ wᵢ · max(0, Cᵢ - dᵢ) on a fixed {n_orders}-order / {n_machines}-machine benchmark.\n\n"
        f"**Benchmark**: `build_benchmark(seed=77)` — frozen "
        f"(total work {total_work}h, due dates tight).\n\n"
        "**Evaluator**: `evaluate(inst, schedule)` — frozen.\n\n"
        "**Editable file**: `solver.py` — rewrite `solve(inst) -> schedule` freely.\n\n"
        "**Budget**: < 50 ms per run. Keep if WT improves, else revert.\n\n"
        f"**Stop**: WT flat for 3 iterations, or {NUM_ITERATIONS}-iteration cap reached."
    )


def run_iteration(iter_idx: int, seed: int = 77, lang: str = "en") -> dict:
    if iter_idx < 0 or iter_idx >= NUM_ITERATIONS:
        raise IndexError(f"iter_idx {iter_idx} out of range [0, {NUM_ITERATIONS - 1}]")
    inst = build_benchmark(seed)
    # Re-run prior variants to establish prev_best (cheap — <50ms each).
    prev_best = None
    kept_sequence: list[int] = []
    for j in range(iter_idx):
        wt_j = evaluate(inst, VARIANTS[j]["fn"](inst))["weighted_tardiness"]
        if prev_best is None or wt_j < prev_best:
            prev_best = wt_j
            kept_sequence.append(j)
    v = VARIANTS[iter_idx]
    schedule = v["fn"](inst)
    metric = evaluate(inst, schedule)
    wt = metric["weighted_tardiness"]
    kept = prev_best is None or wt < prev_best
    best_so_far = wt if kept else prev_best
    source = inspect.getsource(v["fn"])
    return {
        "iter": iter_idx,
        "name": v["name"],
        "name_zh": v["name_zh"],
        "hypothesis": v["hypothesis"],
        "hypothesis_zh": v["hypothesis_zh"],
        "code": source,
        "metric": metric,
        "schedule": schedule,
        "kept": kept,
        "prev_best": prev_best,
        "best_so_far": best_so_far,
        "commentary": _commentary(iter_idx, metric, prev_best, kept, lang),
        "num_iterations": NUM_ITERATIONS,
    }


def run_full(seed: int = 77, lang: str = "en") -> dict:
    inst = build_benchmark(seed)
    results = []
    prev_best = None
    for i, v in enumerate(VARIANTS):
        sched = v["fn"](inst)
        metric = evaluate(inst, sched)
        wt = metric["weighted_tardiness"]
        kept = prev_best is None or wt < prev_best
        results.append({
            "iter": i, "name": v["name"], "name_zh": v["name_zh"],
            "metric": metric, "kept": kept, "prev_best": prev_best,
            "commentary": _commentary(i, metric, prev_best, kept, lang),
        })
        if kept:
            prev_best = wt
    return {
        "num_iterations": NUM_ITERATIONS,
        "results": results,
        "best_wt": prev_best,
        "instance": get_instance_payload(seed),
    }


# ---------------------------------------------------------------------------
# Back-compat shims (older callers imported run_stage / build_report / NUM_STAGES)
# ---------------------------------------------------------------------------

NUM_STAGES = NUM_ITERATIONS  # keep old name alive for anything still referencing it


def run_stage(topic: str, stage_idx: int, prev_results=None) -> dict:
    """Deprecated: maps to run_iteration. `topic` is ignored."""
    res = run_iteration(stage_idx)
    res["stage_idx"] = stage_idx
    return res


def build_report(topic: str, all_results: list[dict], lang: str = "en") -> str:
    """Legacy report builder — renders trajectory summary as markdown."""
    # Re-run full to get the authoritative trajectory, ignore `all_results`.
    full = run_full(lang=lang)
    lines_en = [
        f"# AutoResearch trajectory — scheduling",
        "",
        f"**Instance**: 20 orders × 3 machines  ",
        f"**Objective**: minimize Σ wᵢ · max(0, Cᵢ - dᵢ)  ",
        f"**Iterations**: {full['num_iterations']}  ",
        f"**Best WT**: **{full['best_wt']}**",
        "",
        "| iter | variant | WT | makespan | #tardy | kept |",
        "|------|---------|----|---------:|-------:|:----:|",
    ]
    lines_zh = [
        f"# AutoResearch 演进轨迹 — 排产",
        "",
        f"**基准**: 20 订单 × 3 机器  ",
        f"**目标**: 最小化 Σ wᵢ · max(0, Cᵢ - dᵢ)  ",
        f"**迭代数**: {full['num_iterations']}  ",
        f"**最优 WT**: **{full['best_wt']}**",
        "",
        "| 轮次 | 方案 | WT | 总跨度 | 延误数 | 保留 |",
        "|------|------|----|------:|-----:|:---:|",
    ]
    lines = lines_zh if lang == "zh" else lines_en
    for r in full["results"]:
        m = r["metric"]
        name = r["name_zh"] if lang == "zh" else r["name"]
        flag = "✓" if r["kept"] else "✗"
        lines.append(f"| {r['iter']} | {name} | {m['weighted_tardiness']} | {m['makespan']} | {m['num_tardy']} | {flag} |")
    return "\n".join(lines)
