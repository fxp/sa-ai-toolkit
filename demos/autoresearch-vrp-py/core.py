"""
AutoResearch for VRP — autonomous algorithm-discovery loop applied to a
Capacitated Vehicle Routing Problem (CVRP).

Same pattern as the scheduling demo:
    - Fixed instance + fixed distance evaluator = frozen benchmark harness.
    - 10 solver variants mirror what an autoresearch agent would propose over
      a night of iteration (Random → NN → Sweep → Clarke-Wright → +2-opt →
      +Or-opt → +relocate → +full neighborhood → +SA).
    - Each iteration runs real Python, gets a real total-distance metric,
      and is kept or reverted against the running best.
"""
from __future__ import annotations

import inspect
import math
import random
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Instance & evaluator  (frozen benchmark harness)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Customer:
    id: int        # 0 = depot, 1..N = customers
    x: float
    y: float
    demand: int    # depot: 0


@dataclass(frozen=True)
class Instance:
    customers: tuple[Customer, ...]
    capacity: int
    num_vehicles: int

    @property
    def depot(self) -> Customer:
        return self.customers[0]


def build_benchmark(seed: int = 11) -> Instance:
    """25 customers around a central depot, 4 vehicles × capacity 60.
    Demand sums ~= 230 → needs all 4 vehicles (~58/60 utilisation)."""
    rng = random.Random(seed)
    depot = Customer(id=0, x=50.0, y=50.0, demand=0)
    customers = [depot]
    # Cluster customers in 3 zones plus some scatter so routing structure matters.
    zone_centers = [(20, 25), (75, 30), (65, 75), (30, 80)]
    for i in range(1, 26):
        cx, cy = zone_centers[(i - 1) % len(zone_centers)]
        x = max(2, min(98, cx + rng.gauss(0, 12)))
        y = max(2, min(98, cy + rng.gauss(0, 12)))
        demand = rng.randint(4, 14)
        customers.append(Customer(id=i, x=round(x, 1), y=round(y, 1), demand=demand))
    return Instance(customers=tuple(customers), capacity=60, num_vehicles=4)


def dist(a: Customer, b: Customer) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def route_length(inst: Instance, route: list[int]) -> float:
    """A route is a list of customer ids, implicitly starting & ending at depot."""
    if not route:
        return 0.0
    nodes = [inst.customers[i] for i in [0] + route + [0]]
    return sum(dist(a, b) for a, b in zip(nodes, nodes[1:]))


def route_load(inst: Instance, route: list[int]) -> int:
    return sum(inst.customers[i].demand for i in route)


def evaluate(inst: Instance, routes: list[list[int]]) -> dict:
    total_dist = sum(route_length(inst, r) for r in routes)
    over_cap = sum(max(0, route_load(inst, r) - inst.capacity) for r in routes)
    covered = sorted(c for r in routes for c in r)
    expected = list(range(1, len(inst.customers)))
    missing = len(set(expected) - set(covered))
    return {
        "total_distance": round(total_dist, 2),
        "num_routes": sum(1 for r in routes if r),
        "over_capacity": over_cap,
        "missing_customers": missing,
        "longest_route": round(max((route_length(inst, r) for r in routes if r), default=0), 2),
    }


# ---------------------------------------------------------------------------
# Solver variants  (10 rungs up the ladder)
# ---------------------------------------------------------------------------

def solver_random(inst: Instance) -> list[list[int]]:
    """v0 — baseline: shuffle customers, round-robin into vehicles.
    Ignores capacity and geography. Just a reference."""
    rng = random.Random(0)
    custs = list(range(1, len(inst.customers)))
    rng.shuffle(custs)
    routes = [[] for _ in range(inst.num_vehicles)]
    for i, c in enumerate(custs):
        routes[i % inst.num_vehicles].append(c)
    return routes


def solver_nn_single(inst: Instance) -> list[list[int]]:
    """v1 — one greedy nearest-neighbor tour, ignores capacity & vehicles.
    Dumps every customer into vehicle 0. Capacity will overflow."""
    remaining = set(range(1, len(inst.customers)))
    tour: list[int] = []
    cur = 0
    while remaining:
        nxt = min(remaining, key=lambda c: dist(inst.customers[cur], inst.customers[c]))
        tour.append(nxt)
        remaining.remove(nxt)
        cur = nxt
    routes = [tour] + [[] for _ in range(inst.num_vehicles - 1)]
    return routes


def solver_nn_capacity(inst: Instance) -> list[list[int]]:
    """v2 — nearest-neighbor that closes the current route when capacity would
    overflow, then starts the next route from depot."""
    remaining = set(range(1, len(inst.customers)))
    routes: list[list[int]] = []
    while remaining and len(routes) < inst.num_vehicles:
        route: list[int] = []
        load = 0
        cur = 0
        while remaining:
            candidates = [c for c in remaining if load + inst.customers[c].demand <= inst.capacity]
            if not candidates:
                break
            nxt = min(candidates, key=lambda c: dist(inst.customers[cur], inst.customers[c]))
            route.append(nxt)
            load += inst.customers[nxt].demand
            remaining.remove(nxt)
            cur = nxt
        routes.append(route)
    while len(routes) < inst.num_vehicles:
        routes.append([])
    # Leftover: dump into the vehicle with most slack
    for c in list(remaining):
        routes.sort(key=lambda r: route_load(inst, r))
        routes[0].append(c)
        remaining.remove(c)
    return routes


def solver_sweep(inst: Instance) -> list[list[int]]:
    """v3 — sweep algorithm: sort customers by polar angle around depot,
    then cut into routes that respect capacity."""
    depot = inst.depot
    custs = list(range(1, len(inst.customers)))
    custs.sort(key=lambda c: math.atan2(inst.customers[c].y - depot.y, inst.customers[c].x - depot.x))
    routes: list[list[int]] = []
    cur: list[int] = []
    load = 0
    for c in custs:
        d = inst.customers[c].demand
        if load + d > inst.capacity:
            routes.append(cur)
            cur, load = [c], d
        else:
            cur.append(c)
            load += d
    if cur:
        routes.append(cur)
    while len(routes) < inst.num_vehicles:
        routes.append([])
    return routes[:inst.num_vehicles] if len(routes) > inst.num_vehicles else routes


def solver_clarke_wright(inst: Instance) -> list[list[int]]:
    """v4 — Clarke-Wright savings. Start with one route per customer, then
    greedily merge routes by descending savings = d(0,i)+d(0,j)−d(i,j)."""
    n = len(inst.customers)
    routes: list[list[int]] = [[c] for c in range(1, n)]

    def route_of(c: int) -> list[int] | None:
        for r in routes:
            if c in r:
                return r
        return None

    savings: list[tuple[float, int, int]] = []
    for i in range(1, n):
        for j in range(i + 1, n):
            s = (dist(inst.customers[0], inst.customers[i])
                 + dist(inst.customers[0], inst.customers[j])
                 - dist(inst.customers[i], inst.customers[j]))
            savings.append((s, i, j))
    savings.sort(reverse=True)

    for s, i, j in savings:
        if s <= 0:
            break
        ri, rj = route_of(i), route_of(j)
        if ri is None or rj is None or ri is rj:
            continue
        if (i == ri[0] or i == ri[-1]) and (j == rj[0] or j == rj[-1]):
            if route_load(inst, ri) + route_load(inst, rj) > inst.capacity:
                continue
            if i == ri[-1] and j == rj[0]:
                merged = ri + rj
            elif i == ri[0] and j == rj[-1]:
                merged = rj + ri
            elif i == ri[-1] and j == rj[-1]:
                merged = ri + rj[::-1]
            else:  # i == ri[0] and j == rj[0]
                merged = ri[::-1] + rj
            routes.remove(ri); routes.remove(rj); routes.append(merged)

    # Trim to available vehicles by merging smallest pairs if too many
    while len(routes) > inst.num_vehicles:
        routes.sort(key=lambda r: route_length(inst, r))
        a = routes.pop(0); b = routes.pop(0)
        merged = a + b  # capacity may break but missing=0 still holds
        routes.append(merged)
    while len(routes) < inst.num_vehicles:
        routes.append([])
    return routes


def _two_opt_route(inst: Instance, route: list[int]) -> list[int]:
    """Standard 2-opt on a single route until no improving swap."""
    if len(route) < 3:
        return route[:]
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                trial = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if route_length(inst, trial) < route_length(inst, best) - 1e-9:
                    best = trial
                    improved = True
                    break
            if improved:
                break
    return best


def solver_cw_2opt(inst: Instance) -> list[list[int]]:
    """v5 — Clarke-Wright + 2-opt on each route (intra-route only)."""
    routes = solver_clarke_wright(inst)
    return [_two_opt_route(inst, r) for r in routes]


def _or_opt_route(inst: Instance, route: list[int], seg_len: int = 2) -> list[int]:
    """Or-opt: move a contiguous segment of length `seg_len` to its best position."""
    best = route[:]
    improved = True
    while improved:
        improved = False
        n = len(best)
        if n < seg_len + 1:
            break
        for i in range(n - seg_len + 1):
            seg = best[i:i + seg_len]
            rest = best[:i] + best[i + seg_len:]
            for k in range(len(rest) + 1):
                if k == i:
                    continue
                trial = rest[:k] + seg + rest[k:]
                if route_length(inst, trial) < route_length(inst, best) - 1e-9:
                    best = trial
                    improved = True
                    break
            if improved:
                break
    return best


def solver_cw_or_opt(inst: Instance) -> list[list[int]]:
    """v6 — CW + 2-opt + Or-opt (segments of length 1 and 2)."""
    routes = [_two_opt_route(inst, r) for r in solver_clarke_wright(inst)]
    routes = [_or_opt_route(inst, r, 1) for r in routes]
    routes = [_or_opt_route(inst, r, 2) for r in routes]
    return routes


def _relocate_interroute(inst: Instance, routes: list[list[int]]) -> list[list[int]]:
    """Move a single customer from one route to another if it strictly improves."""
    best = [r[:] for r in routes]
    improved = True
    while improved:
        improved = False
        base = sum(route_length(inst, r) for r in best)
        for ri in range(len(best)):
            if not best[ri]:
                continue
            for ci_pos in range(len(best[ri])):
                c = best[ri][ci_pos]
                for rj in range(len(best)):
                    if rj == ri:
                        continue
                    if route_load(inst, best[rj]) + inst.customers[c].demand > inst.capacity:
                        continue
                    for k in range(len(best[rj]) + 1):
                        new_ri = best[ri][:ci_pos] + best[ri][ci_pos + 1:]
                        new_rj = best[rj][:k] + [c] + best[rj][k:]
                        new_total = base - route_length(inst, best[ri]) - route_length(inst, best[rj]) \
                                    + route_length(inst, new_ri) + route_length(inst, new_rj)
                        if new_total < base - 1e-9:
                            best[ri], best[rj] = new_ri, new_rj
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
    return best


def solver_cw_relocate(inst: Instance) -> list[list[int]]:
    """v7 — CW + inter-route customer relocation."""
    routes = solver_clarke_wright(inst)
    routes = _relocate_interroute(inst, routes)
    return [_two_opt_route(inst, r) for r in routes]


def solver_cw_full_local(inst: Instance) -> list[list[int]]:
    """v8 — CW + 2-opt + Or-opt + relocate, iterated until no improvement."""
    routes = solver_clarke_wright(inst)
    prev_total = float('inf')
    for _ in range(6):
        routes = [_two_opt_route(inst, r) for r in routes]
        routes = [_or_opt_route(inst, r, 1) for r in routes]
        routes = [_or_opt_route(inst, r, 2) for r in routes]
        routes = _relocate_interroute(inst, routes)
        total = sum(route_length(inst, r) for r in routes)
        if total >= prev_total - 1e-6:
            break
        prev_total = total
    return routes


def _cheapest_insertion(inst: Instance, routes: list[list[int]], customer: int) -> list[list[int]]:
    """Insert `customer` into the best (feasible, min-delta) position across all routes."""
    cust = inst.customers[customer]
    best_delta = float("inf")
    best_ri, best_pos = -1, -1
    for ri, r in enumerate(routes):
        if route_load(inst, r) + cust.demand > inst.capacity:
            continue
        base = route_length(inst, r)
        for pos in range(len(r) + 1):
            trial = r[:pos] + [customer] + r[pos:]
            delta = route_length(inst, trial) - base
            if delta < best_delta:
                best_delta = delta
                best_ri, best_pos = ri, pos
    if best_ri < 0:
        # Fallback: dump into vehicle with most slack
        best_ri = min(range(len(routes)), key=lambda i: route_load(inst, routes[i]))
        best_pos = len(routes[best_ri])
    new_routes = [r[:] for r in routes]
    new_routes[best_ri] = new_routes[best_ri][:best_pos] + [customer] + new_routes[best_ri][best_pos:]
    return new_routes


def solver_cw_lns(inst: Instance, iters: int = 80, remove_frac: float = 0.25) -> list[list[int]]:
    """v9 — CW + Large Neighborhood Search (destroy + repair).
    Each iteration: remove `remove_frac` customers (random + costly), reinsert
    with cheapest-insertion, polish with 2-opt, accept if better.
    """
    routes = solver_cw_full_local(inst)

    def total(rs: list[list[int]]) -> float:
        return sum(route_length(inst, r) for r in rs)

    best = [r[:] for r in routes]
    best_t = total(best)
    n_cust = len(inst.customers) - 1
    n_remove = max(2, int(remove_frac * n_cust))
    rng = random.Random(42)
    for _ in range(iters):
        # Destroy: pick customers to remove (50% random, 50% most costly — Shaw-like)
        flat = [(ri, pos, c) for ri, r in enumerate(routes) for pos, c in enumerate(r)]
        costs = []
        for ri, pos, c in flat:
            r = routes[ri]
            prev = inst.customers[r[pos - 1]] if pos > 0 else inst.customers[0]
            nxt = inst.customers[r[pos + 1]] if pos + 1 < len(r) else inst.customers[0]
            cost = dist(prev, inst.customers[c]) + dist(inst.customers[c], nxt) - dist(prev, nxt)
            costs.append((cost, c))
        costs.sort(reverse=True)
        costly = [c for _, c in costs[:n_remove // 2]]
        pool = [c for c in range(1, len(inst.customers)) if c not in costly]
        rng.shuffle(pool)
        random_removed = pool[:n_remove - len(costly)]
        removed = set(costly + random_removed)
        # Remove them
        trial = [[c for c in r if c not in removed] for r in routes]
        # Repair: cheapest insertion in random order
        order = list(removed)
        rng.shuffle(order)
        for c in order:
            trial = _cheapest_insertion(inst, trial, c)
        # Reject if any route over capacity (cheapest_insertion fallback may overflow)
        if any(route_load(inst, r) > inst.capacity for r in trial):
            continue
        # Intensify
        trial = [_two_opt_route(inst, r) for r in trial]
        trial = [_or_opt_route(inst, r, 2) for r in trial]
        new_t = total(trial)
        # Accept only if improving (greedy LNS)
        if new_t < best_t - 1e-6:
            routes = trial
            best = [r[:] for r in trial]
            best_t = new_t
    return best




# ---------------------------------------------------------------------------
# Variant catalog
# ---------------------------------------------------------------------------

VARIANTS: list[dict] = [
    {"idx": 0, "name": "Random", "name_zh": "随机分派", "fn": solver_random,
     "hypothesis": "Round-robin shuffle. Reference line — ignores distance and capacity.",
     "hypothesis_zh": "打散后轮询分配给4辆车，不考虑距离和容量，仅作参考。"},
    {"idx": 1, "name": "NN single tour", "name_zh": "单路径最近邻", "fn": solver_nn_single,
     "hypothesis": "One greedy nearest-neighbor tour. Breaks capacity — expected worse.",
     "hypothesis_zh": "所有客户并入一辆车做贪心最近邻，必然超载，预期变差。"},
    {"idx": 2, "name": "NN + capacity", "name_zh": "最近邻+容量", "fn": solver_nn_capacity,
     "hypothesis": "Nearest-neighbor but close route when capacity would overflow.",
     "hypothesis_zh": "每次临近满载就返仓开新路径，容量受约束的贪心NN。"},
    {"idx": 3, "name": "Sweep", "name_zh": "扇形扫描", "fn": solver_sweep,
     "hypothesis": "Sort by polar angle around depot, cut by capacity — classic Gillett-Miller.",
     "hypothesis_zh": "按极角绕仓库扫描，按容量切段——经典Gillett-Miller扫描法。"},
    {"idx": 4, "name": "Clarke-Wright", "name_zh": "Clarke-Wright 节约", "fn": solver_clarke_wright,
     "hypothesis": "Merge route pairs by descending savings (d0i+d0j-dij).",
     "hypothesis_zh": "按节约值 d(0,i)+d(0,j)-d(i,j) 降序合并路径。VRP 的黄金基线。"},
    {"idx": 5, "name": "CW + 2-opt", "name_zh": "CW + 2-opt", "fn": solver_cw_2opt,
     "hypothesis": "CW routes + 2-opt reversal on each route (intra-route only).",
     "hypothesis_zh": "在CW基础上，对每条路径内部做2-opt反转。"},
    {"idx": 6, "name": "CW + Or-opt", "name_zh": "CW + Or-opt", "fn": solver_cw_or_opt,
     "hypothesis": "CW + 2-opt + Or-opt: move segments of length 1-2 to better positions.",
     "hypothesis_zh": "在CW+2-opt基础上加入Or-opt，移动长度1-2的片段到更优位置。"},
    {"idx": 7, "name": "CW + relocate", "name_zh": "CW + 路径间迁移", "fn": solver_cw_relocate,
     "hypothesis": "CW + inter-route relocation: move a customer across routes.",
     "hypothesis_zh": "在CW之上允许客户跨路径迁移，打破局部最优的结构。"},
    {"idx": 8, "name": "CW + full local", "name_zh": "CW + 全局局部搜索", "fn": solver_cw_full_local,
     "hypothesis": "CW + 2-opt + Or-opt + relocate, iterated until no improvement.",
     "hypothesis_zh": "把2-opt / Or-opt / 跨路径迁移打包成VND，反复迭代至收敛。"},
    {"idx": 9, "name": "CW + LNS", "name_zh": "CW + 大邻域搜索", "fn": solver_cw_lns,
     "hypothesis": "Large Neighborhood Search — destroy 25% of the solution and repair via cheapest insertion.",
     "hypothesis_zh": "大邻域搜索：每轮摧毁 25% 客户再用最廉价插入重建，突破局部搜索的天花板。"},
]

NUM_ITERATIONS = len(VARIANTS)


def _commentary(idx: int, metric: dict, prev_best: float | None, kept: bool, lang: str = "en") -> str:
    d = metric["total_distance"]
    over = metric["over_capacity"]
    if lang == "zh":
        if idx == 0:
            return f"基线总里程={d:.1f}，超容量={over}。作为后续对比参照。"
        delta = d - prev_best if prev_best is not None else 0
        over_note = f"（超容量{over}）" if over else ""
        if kept:
            return f"总里程={d:.1f}{over_note}，较最优 ↓{-delta:.1f}（{-delta / max(prev_best, 1):.0%}）— 保留。"
        return f"总里程={d:.1f}{over_note}，较最优 ↑{delta:.1f}（{delta / max(prev_best, 1):.0%}）— 回滚。"
    if idx == 0:
        return f"Baseline distance={d:.1f}, over-cap={over}. Reference line."
    delta = d - prev_best if prev_best is not None else 0
    over_note = f" (over-cap {over})" if over else ""
    if kept:
        return f"Distance={d:.1f}{over_note}, down {-delta:.1f} ({-delta / max(prev_best, 1):.0%}) vs best — kept."
    return f"Distance={d:.1f}{over_note}, up {delta:.1f} ({delta / max(prev_best, 1):.0%}) vs best — reverted."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_instance_payload(seed: int = 11) -> dict:
    inst = build_benchmark(seed)
    return {
        "depot": {"id": inst.depot.id, "x": inst.depot.x, "y": inst.depot.y},
        "customers": [
            {"id": c.id, "x": c.x, "y": c.y, "demand": c.demand}
            for c in inst.customers[1:]
        ],
        "num_customers": len(inst.customers) - 1,
        "num_vehicles": inst.num_vehicles,
        "capacity": inst.capacity,
        "total_demand": sum(c.demand for c in inst.customers),
    }


def get_program_md(lang: str = "en") -> str:
    inst = build_benchmark()
    n = len(inst.customers) - 1
    total_demand = sum(c.demand for c in inst.customers)
    if lang == "zh":
        return (
            "# program.md\n\n"
            f"**目标**: 在固定基准上最小化总行驶距离 Σ d(route_k)，"
            f"全部 {n} 个客户必须访问且不超车辆容量。\n\n"
            f"**基准**: {n} 客户 + 1 仓库，{inst.num_vehicles} 辆车 × 容量 {inst.capacity}，"
            f"总需求 {total_demand}（≈ {total_demand / (inst.num_vehicles * inst.capacity):.0%} 容量利用率）。\n\n"
            "**评估器**: `evaluate(inst, routes)` — 不可修改。\n\n"
            "**可编辑文件**: `solver.py` — 自由重写 `solve(inst) -> routes`。\n\n"
            "**硬约束**: `missing_customers == 0`，`over_capacity == 0`。\n\n"
            f"**停止**: 总距离连续 3 轮无改善，或 {NUM_ITERATIONS} 轮上限。"
        )
    return (
        "# program.md\n\n"
        f"**Goal**: minimize total travel distance Σ d(route_k). Every customer "
        f"must be visited and no route may exceed vehicle capacity.\n\n"
        f"**Benchmark**: {n} customers + 1 depot, {inst.num_vehicles} vehicles × "
        f"capacity {inst.capacity}, total demand {total_demand} "
        f"(~{total_demand / (inst.num_vehicles * inst.capacity):.0%} capacity utilisation).\n\n"
        "**Evaluator**: `evaluate(inst, routes)` — frozen.\n\n"
        "**Editable file**: `solver.py` — rewrite `solve(inst) -> routes` freely.\n\n"
        "**Hard constraints**: `missing_customers == 0`, `over_capacity == 0`.\n\n"
        f"**Stop**: distance flat for 3 iterations, or {NUM_ITERATIONS}-iteration cap reached."
    )


def _serialize_routes(inst: Instance, routes: list[list[int]]) -> list[dict]:
    out = []
    for v, r in enumerate(routes):
        out.append({
            "vehicle": v,
            "customers": r,
            "path": [0] + r + [0],
            "distance": round(route_length(inst, r), 2),
            "load": route_load(inst, r),
            "over_capacity": max(0, route_load(inst, r) - inst.capacity),
        })
    return out


def run_iteration(iter_idx: int, seed: int = 11, lang: str = "en") -> dict:
    if iter_idx < 0 or iter_idx >= NUM_ITERATIONS:
        raise IndexError(f"iter_idx {iter_idx} out of range [0, {NUM_ITERATIONS - 1}]")
    inst = build_benchmark(seed)
    # prev_best for commentary — re-run prior variants (cheap: O(seconds))
    prev_best = None
    for j in range(iter_idx):
        try:
            m = evaluate(inst, VARIANTS[j]["fn"](inst))
            # Only count feasible solutions for "best"
            if m["over_capacity"] == 0 and m["missing_customers"] == 0:
                if prev_best is None or m["total_distance"] < prev_best:
                    prev_best = m["total_distance"]
        except Exception:
            continue
    v = VARIANTS[iter_idx]
    routes = v["fn"](inst)
    metric = evaluate(inst, routes)
    d = metric["total_distance"]
    feasible = metric["over_capacity"] == 0 and metric["missing_customers"] == 0
    kept = feasible and (prev_best is None or d < prev_best)
    best_so_far = d if kept else (prev_best if prev_best is not None else d)
    return {
        "iter": iter_idx,
        "name": v["name"],
        "name_zh": v["name_zh"],
        "hypothesis": v["hypothesis"],
        "hypothesis_zh": v["hypothesis_zh"],
        "code": inspect.getsource(v["fn"]),
        "metric": metric,
        "routes": _serialize_routes(inst, routes),
        "feasible": feasible,
        "kept": kept,
        "prev_best": prev_best,
        "best_so_far": best_so_far,
        "commentary": _commentary(iter_idx, metric, prev_best, kept, lang),
        "num_iterations": NUM_ITERATIONS,
    }


def run_full(seed: int = 11, lang: str = "en") -> dict:
    inst = build_benchmark(seed)
    results = []
    prev_best = None
    for i, v in enumerate(VARIANTS):
        routes = v["fn"](inst)
        m = evaluate(inst, routes)
        feasible = m["over_capacity"] == 0 and m["missing_customers"] == 0
        kept = feasible and (prev_best is None or m["total_distance"] < prev_best)
        results.append({
            "iter": i, "name": v["name"], "name_zh": v["name_zh"],
            "metric": m, "kept": kept, "feasible": feasible, "prev_best": prev_best,
            "commentary": _commentary(i, m, prev_best, kept, lang),
        })
        if kept:
            prev_best = m["total_distance"]
    return {
        "num_iterations": NUM_ITERATIONS,
        "results": results,
        "best_distance": prev_best,
        "instance": get_instance_payload(seed),
    }


def build_trajectory_md(lang: str = "en") -> str:
    full = run_full(lang=lang)
    if lang == "zh":
        lines = [
            "# AutoResearch 演进轨迹 — VRP 配送路径",
            "",
            f"**基准**: {full['instance']['num_customers']} 客户 × "
            f"{full['instance']['num_vehicles']} 车辆（容量 {full['instance']['capacity']}）",
            f"**最优总里程**: **{full['best_distance']}**",
            "",
            "| 轮次 | 方案 | 总里程 | 超容 | 保留 |",
            "|:---:|:---|--:|--:|:---:|",
        ]
    else:
        lines = [
            "# AutoResearch trajectory — VRP",
            "",
            f"**Benchmark**: {full['instance']['num_customers']} customers × "
            f"{full['instance']['num_vehicles']} vehicles (capacity {full['instance']['capacity']})",
            f"**Best distance**: **{full['best_distance']}**",
            "",
            "| iter | variant | distance | over-cap | kept |",
            "|:---:|:---|--:|--:|:---:|",
        ]
    for r in full["results"]:
        m = r["metric"]
        name = r["name_zh"] if lang == "zh" else r["name"]
        flag = "✓" if r["kept"] else "✗"
        lines.append(f"| v{r['iter']} | {name} | {m['total_distance']} | {m['over_capacity']} | {flag} |")
    return "\n".join(lines)
