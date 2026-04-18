"""GStack command simulator — pure functions that emit scripted terminal output.

Each command returns a list of script items:
    {"delay_ms": int, "text": str, "class": str}

`class` is one of: "prompt" | "output" | "highlight" | "warn" | "err" | "ok" | "dim".
The frontend is responsible for rendering; this module produces only data.
"""
from __future__ import annotations

from typing import List, Dict, Optional


ScriptItem = Dict[str, object]


def _item(text: str, cls: str = "output", delay_ms: int = 80) -> ScriptItem:
    return {"delay_ms": int(delay_ms), "text": str(text), "class": str(cls)}


def _office_hours(user_input: Optional[str]) -> List[ScriptItem]:
    idea = (user_input or "(no idea provided)").strip()
    questions = [
        "1. Who, specifically, are your first 10 users? (Names, not personas.)",
        "2. What does the status quo cost them today — in dollars or hours?",
        "3. What is the narrowest wedge you can ship in 4 weeks?",
        "4. Why you, why now? What unfair advantage do you have?",
        "5. What observation from the real world sparked this idea?",
        "6. In 3 years, what does the future look like if you succeed?",
    ]
    script: List[ScriptItem] = []
    script.append(_item("YC Office Hours — 6 forcing questions", "prompt", 200))
    script.append(_item("──────────────────────────────────────", "dim", 100))
    script.append(_item(f"Idea: {idea}", "highlight", 400))
    for q in questions:
        script.append(_item(q, "output", 800))
    script.append(_item("── Reframe Summary ───────────────────", "prompt", 600))
    script.append(_item("→ Biggest gap: desperate specificity on the first 10 users.", "warn", 400))
    script.append(_item("→ Next action: 3 concrete user names by Friday.", "ok", 400))
    return script


def _autoplan() -> List[ScriptItem]:
    script: List[ScriptItem] = []
    script.append(_item("/autoplan — three-phase plan review", "prompt", 200))
    script.append(_item("──────────────────────────────────────", "dim", 100))

    # Phase 1 CEO
    script.append(_item("Phase 1: CEO review (scope & 10-star product)", "highlight", 400))
    script.append(_item("  • Exploring scope expansions…", "dim", 600))
    script.append(_item("  • Rethink premise: should we expand to multi-tenant?", "dim", 500))
    script.append(_item("  • Decision: HOLD SCOPE — ship v1, expand in v2.", "ok", 500))

    # Phase 2 Design
    script.append(_item("Phase 2: Design review (UX & taste)", "highlight", 500))
    script.append(_item("  • Scoring visual hierarchy…", "dim", 600))
    script.append(_item("  • Density 7/10 — tighten card padding.", "dim", 400))
    script.append(_item("  • Motion 6/10 — add 200ms transitions.", "dim", 400))
    script.append(_item("  • Decision: polish before ship.", "ok", 500))

    # Phase 3 Eng
    script.append(_item("Phase 3: Eng review (architecture)", "highlight", 500))
    script.append(_item("  • Tracing data flow & edge cases…", "dim", 600))
    script.append(_item("  • Edge case: empty state not handled — add fallback.", "warn", 400))
    script.append(_item("  • Test coverage: 68% → target 80%.", "dim", 400))
    script.append(_item("  • Decision: LGTM with 2 followups.", "ok", 400))

    script.append(_item("✓ Plan locked. 3 taste decisions at approval gate.", "ok", 500))
    return script


def _qa() -> List[ScriptItem]:
    script: List[ScriptItem] = []
    script.append(_item("/qa — systematic test + fix loop", "prompt", 200))
    script.append(_item("──────────────────────────────────────", "dim", 100))
    script.append(_item("Running 47 tests…", "highlight", 300))
    fails = {12, 23, 38}
    for i in range(1, 48):
        tag = "✗" if i in fails else "✓"
        cls = "err" if i in fails else "ok"
        script.append(_item(f"{tag} test_{i:03d}", cls, 40))
    script.append(_item("3 failures detected:", "err", 400))
    script.append(_item("  ✗ test_012  empty_state_renders_fallback", "err", 200))
    script.append(_item("  ✗ test_023  lang_toggle_persists_to_localStorage", "err", 200))
    script.append(_item("  ✗ test_038  kb_lint_flags_unsourced_claims", "err", 200))
    script.append(_item("Applying atomic fixes…", "highlight", 500))
    for label, sha in [
        ("fix 1/3: add empty state fallback", "a3f2e1"),
        ("fix 2/3: persist lang to localStorage", "b8c0d5"),
        ("fix 3/3: flag unsourced claims in lint", "d7e9a4"),
    ]:
        script.append(_item(f"  ⠿ {label}", "dim", 900))
        script.append(_item(f"    committed: {sha}", "dim", 300))
    script.append(_item("Re-running 47 tests…", "highlight", 500))
    script.append(_item("✓ All 47 tests passing. 3 commits on branch qa-fixes.", "ok", 800))
    return script


def _ship() -> List[ScriptItem]:
    script: List[ScriptItem] = []
    script.append(_item("/ship — land & deploy", "prompt", 200))
    script.append(_item("──────────────────────────────────────", "dim", 100))
    script.append(_item("⠿ git sync main", "dim", 900))
    script.append(_item("  3 commits ahead, 0 behind.", "dim", 300))
    script.append(_item("⠿ running tests (47)", "dim", 1200))
    script.append(_item("  all green.", "ok", 300))
    script.append(_item("⠿ bump VERSION 1.4.2 → 1.4.3", "dim", 600))
    script.append(_item("⠿ update CHANGELOG", "dim", 500))
    script.append(_item("⠿ git push origin feature/interactive-demos", "dim", 900))
    script.append(_item("⠿ gh pr create", "dim", 1000))
    script.append(_item("✓ PR #247 opened: \"Add interactive demo pages\"", "ok", 500))
    script.append(_item("  https://github.com/your-org/repo/pull/247", "prompt", 200))
    script.append(_item("Next: run /land-and-deploy to merge & verify prod.", "dim", 400))
    return script


COMMANDS = {
    "office-hours": _office_hours,
    "autoplan": lambda _inp=None: _autoplan(),
    "qa": lambda _inp=None: _qa(),
    "ship": lambda _inp=None: _ship(),
}


def run_command(command: str, user_input: Optional[str] = None) -> List[ScriptItem]:
    """Return the scripted output for a gstack command (full, one-shot).

    command: one of "office-hours", "autoplan", "qa", "ship".
    user_input: optional free-form user text (currently only used by office-hours).
    """
    cmd = (command or "").strip().lstrip("/")
    if cmd not in COMMANDS:
        raise ValueError(
            f"Unknown command: {command!r}. Valid: {sorted(COMMANDS)}"
        )
    if cmd == "office-hours":
        return _office_hours(user_input)
    return COMMANDS[cmd]()


# ──────────────────────────────────────────────────────────────
# Multi-turn chat protocol
# ──────────────────────────────────────────────────────────────
# Client tracks {command, turn, history}. Each POST/GET to the
# backend replays one segment. Turn numbering:
#
#   office-hours: turn 0 opens the session (show idea + Q1),
#                 turns 1..5 echo user's last answer + ask Qk+1,
#                 turn 6 shows the Reframe Summary and ends.
#   autoplan   : single turn (full plan output).
#   qa         : single turn (full test run).
#   ship       : single turn (full pipeline output).
#
# Shape returned by run_turn():
#   {"script": [ScriptItem, ...],
#    "prompt": <str|None>,      # next prompt to show inline (e.g. the current question)
#    "done": <bool>,            # True = session ended, client should reset state
#    "turn": <int>}             # echo back the turn just played

_OFFICE_QUESTIONS = [
    "Who, specifically, are your first 10 users? (Names, not personas.)",
    "What does the status quo cost them today — in dollars or hours?",
    "What is the narrowest wedge you can ship in 4 weeks?",
    "Why you, why now? What unfair advantage do you have?",
    "What observation from the real world sparked this idea?",
    "In 3 years, what does the future look like if you succeed?",
]


def _office_hours_turn(turn: int, user_input: Optional[str],
                       history: Optional[List[Dict]] = None) -> Dict:
    """Play one turn of the office-hours dialogue."""
    total = len(_OFFICE_QUESTIONS)
    script: List[ScriptItem] = []

    if turn == 0:
        idea = (user_input or "(no idea provided)").strip()
        script.append(_item("YC Office Hours — 6 forcing questions", "prompt", 150))
        script.append(_item("──────────────────────────────────────", "dim", 60))
        script.append(_item(f"Idea: {idea}", "highlight", 200))
        script.append(_item(f"Q1/{total}. {_OFFICE_QUESTIONS[0]}", "output", 400))
        return {"script": script, "prompt": _OFFICE_QUESTIONS[0],
                "done": False, "turn": turn, "total_turns": total + 1}

    if 1 <= turn <= total - 1:
        ans = (user_input or "").strip() or "(no answer)"
        script.append(_item(f"› {ans}", "dim", 60))
        script.append(_item(f"Q{turn + 1}/{total}. {_OFFICE_QUESTIONS[turn]}", "output", 300))
        return {"script": script, "prompt": _OFFICE_QUESTIONS[turn],
                "done": False, "turn": turn, "total_turns": total + 1}

    # turn == total (6) → collect last answer, print summary, end
    ans = (user_input or "").strip() or "(no answer)"
    script.append(_item(f"› {ans}", "dim", 60))
    script.append(_item("── Reframe Summary ───────────────────", "prompt", 400))
    # Roll up history into a deterministic "reframe"
    if history:
        first_user_idea = next((h.get("text") for h in history
                                if h.get("role") == "user"), "(no idea)")
        script.append(_item(f"Original idea: {first_user_idea[:80]}", "dim", 100))
    script.append(_item("→ Biggest gap: desperate specificity on the first 10 users.", "warn", 300))
    script.append(_item("→ Next action: 3 concrete user names by Friday.", "ok", 300))
    script.append(_item("── Session ended ────────────────────", "dim", 100))
    return {"script": script, "prompt": None, "done": True,
            "turn": turn, "total_turns": total + 1}


def run_turn(command: str, turn: int = 0,
             user_input: Optional[str] = None,
             history: Optional[List[Dict]] = None) -> Dict:
    """Multi-turn version of run_command. Interactive for office-hours,
    one-shot for others (returns full script with done=True on turn 0)."""
    cmd = (command or "").strip().lstrip("/")
    if cmd not in COMMANDS:
        raise ValueError(f"Unknown command: {command!r}. Valid: {sorted(COMMANDS)}")

    if cmd == "office-hours":
        return _office_hours_turn(turn=int(turn), user_input=user_input, history=history)

    # Non-interactive commands: return full script in one turn.
    if turn > 0:
        return {"script": [], "prompt": None, "done": True, "turn": turn,
                "total_turns": 1}
    return {"script": COMMANDS[cmd](), "prompt": None, "done": True,
            "turn": 0, "total_turns": 1}
