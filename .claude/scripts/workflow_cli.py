#!/usr/bin/env python3
"""Workflow CLI — structured read/write for plan, phase, and state JSON files.

Usage:
  workflow-cli plan show [--plan-dir DIR]
  workflow-cli plan get [FIELD] [--plan-dir DIR]
  workflow-cli plan phases [--plan-dir DIR]
  workflow-cli plan set-status STATUS [--plan-dir DIR]

  workflow-cli phase show N [--plan-dir DIR]
  workflow-cli phase tasks N [--plan-dir DIR]
  workflow-cli phase task N TASK_ID [--plan-dir DIR]

  workflow-cli state show [--plan-dir DIR]
  workflow-cli state current [--plan-dir DIR]
  workflow-cli state get [FIELD] [--plan-dir DIR]
  workflow-cli state start-execution COMMIT [--plan-dir DIR]
  workflow-cli state start-phase N [--plan-dir DIR]
  workflow-cli state set-active N TASK_ID [--plan-dir DIR]
  workflow-cli state complete-task N TASK_ID [--plan-dir DIR]
  workflow-cli state fail-task N TASK_ID REASON [--plan-dir DIR]
  workflow-cli state skip-task N TASK_ID REASON [--plan-dir DIR]
  workflow-cli state substep N TASK_ID STEP done|next [--plan-dir DIR]
  workflow-cli state complete-phase N [--plan-dir DIR]
  workflow-cli state complete [--plan-dir DIR]
  workflow-cli state pause [--plan-dir DIR]
  workflow-cli state log MESSAGE [--plan-dir DIR]
  workflow-cli state set FIELD VALUE [--plan-dir DIR]

  workflow-cli find-active
  workflow-cli init PLAN_DIR
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


WORKFLOW_DIR = ".workflow/plans"


def find_project_root() -> Path:
    """Find project root by looking for .workflow/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".workflow").is_dir():
            return parent
    return cwd


def find_active_plan() -> Path | None:
    """Find the plan directory with status executing or paused."""
    root = find_project_root()
    plans_dir = root / WORKFLOW_DIR
    if not plans_dir.exists():
        return None

    for plan_dir in sorted(plans_dir.iterdir(), reverse=True):
        state_file = plan_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("status") in ("executing", "paused"):
                return plan_dir

    return None


def find_latest_plan() -> Path | None:
    """Find the most recent plan directory."""
    root = find_project_root()
    plans_dir = root / WORKFLOW_DIR
    if not plans_dir.exists():
        return None

    dirs = sorted(
        [d for d in plans_dir.iterdir() if d.is_dir() and (d / "plan.json").exists()],
        reverse=True,
    )
    return dirs[0] if dirs else None


def resolve_plan_dir(explicit: str | None = None) -> Path:
    """Resolve plan directory: explicit > active > latest.

    Accepts:
      - Absolute path: used as-is
      - Relative path with .workflow/plans/: resolved from project root
      - Short name (e.g., '260326-game-bridge'): looked up in .workflow/plans/
    """
    if explicit:
        p = Path(explicit)
        if p.is_absolute():
            return p

        root = find_project_root()

        # If it's already a relative path that exists from root, use it
        candidate = root / explicit
        if candidate.is_dir() and (candidate / "plan.json").exists():
            return candidate

        # Try as a short name inside .workflow/plans/
        candidate_in_plans = root / WORKFLOW_DIR / explicit
        if candidate_in_plans.is_dir() and (candidate_in_plans / "plan.json").exists():
            return candidate_in_plans

        # Fall back to relative from root (original behavior — will error with clear message)
        return candidate

    active = find_active_plan()
    if active:
        return active

    latest = find_latest_plan()
    if latest:
        return latest

    print("Error: No plan directory found.", file=sys.stderr)
    sys.exit(1)


def read_json(path: Path) -> dict:
    """Read a JSON file."""
    if not path.exists():
        print(f"Error: {path} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict):
    """Write a JSON file with pretty formatting."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def now_iso() -> str:
    """Current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ─── Plan Commands ───────────────────────────────────────────────────────────

def cmd_plan_get(plan_dir: Path, field: str | None):
    """Get plan data — full JSON or specific field."""
    plan = read_json(plan_dir / "plan.json")
    if field:
        if field in plan:
            val = plan[field]
            print(json.dumps(val) if isinstance(val, (dict, list)) else str(val))
        else:
            print(f"Error: field '{field}' not found in plan.json", file=sys.stderr)
            sys.exit(1)
    else:
        print(json.dumps(plan, indent=2))


def cmd_plan_show(plan_dir: Path):
    """Readable plan summary."""
    plan = read_json(plan_dir / "plan.json")
    print(f"# {plan.get('name', 'Unnamed Plan')}")
    print(f"Status: {plan.get('status', 'unknown')} | Phases: {plan.get('total_phases', '?')} | Tasks: {plan.get('total_tasks', '?')}")
    print(f"Created: {plan.get('created', '?')}")
    print()
    if plan.get("summary"):
        print(f"## Summary\n{plan['summary']}")
        print()
    if plan.get("phases"):
        print("## Phases")
        print(f"{'#':<4} {'Phase':<30} {'Tasks':<7} {'Deps':<15} {'Group'}")
        print("-" * 70)
        for p in plan["phases"]:
            deps = ", ".join(str(d) for d in p.get("dependencies", [])) or "none"
            print(f"{p['phase']:<4} {p['name']:<30} {p.get('tasks', '?'):<7} {deps:<15} {p.get('group', '?')}")


def cmd_plan_set_status(plan_dir: Path, status: str):
    """Update plan status."""
    valid = ("draft", "reviewed", "approved", "executing", "completed")
    if status not in valid:
        print(f"Error: status must be one of {valid}", file=sys.stderr)
        sys.exit(1)
    plan = read_json(plan_dir / "plan.json")
    plan["status"] = status
    write_json(plan_dir / "plan.json", plan)
    print(json.dumps({"status": status}))


def cmd_plan_phases(plan_dir: Path):
    """List phases with status from state."""
    plan = read_json(plan_dir / "plan.json")
    state_path = plan_dir / "state.json"
    state_phases = {}
    if state_path.exists():
        state = read_json(state_path)
        for sp in state.get("phases", []):
            state_phases[sp["phase"]] = sp.get("status", "unknown")

    for p in plan.get("phases", []):
        status = state_phases.get(p["phase"], "pending")
        print(json.dumps({"phase": p["phase"], "name": p["name"], "group": p.get("group"), "status": status}))


# ─── Phase Commands ──────────────────────────────────────────────────────────

def cmd_phase_show(plan_dir: Path, phase_num: int):
    """Readable phase render."""
    phase = read_json(plan_dir / f"phase-{phase_num}.json")
    print(f"# Phase {phase['phase']}: {phase['name']}")
    print(f"Status: {phase.get('status', 'pending')} | Group: {phase.get('group', '?')}")
    deps = phase.get("depends_on", [])
    print(f"Dependencies: {', '.join(str(d) for d in deps) if deps else 'none'}")
    print()
    if phase.get("goal"):
        print(f"## Goal\n{phase['goal']}")
        print()
    if phase.get("tasks"):
        print("## Tasks")
        for t in phase["tasks"]:
            print(f"\n### {t['id']}: {t['name']}")
            if t.get("description"):
                print(f"  {t['description']}")
            if t.get("files"):
                print(f"  Files: {', '.join(t['files'])}")
            if t.get("acceptance_criteria"):
                print("  Acceptance Criteria:")
                for c in t["acceptance_criteria"]:
                    print(f"    - {c}")
            if t.get("test_requirements"):
                print("  Tests:")
                for tr in t["test_requirements"]:
                    print(f"    - {tr}")


def cmd_phase_tasks(plan_dir: Path, phase_num: int):
    """Get just the tasks for a phase — compact."""
    phase = read_json(plan_dir / f"phase-{phase_num}.json")
    print(json.dumps(phase.get("tasks", []), indent=2))


def cmd_phase_task(plan_dir: Path, phase_num: int, task_id: str):
    """Get a single task."""
    phase = read_json(plan_dir / f"phase-{phase_num}.json")
    for t in phase.get("tasks", []):
        if t["id"] == task_id:
            print(json.dumps(t, indent=2))
            return
    print(f"Error: task '{task_id}' not found in phase {phase_num}", file=sys.stderr)
    sys.exit(1)


# ─── State Commands ──────────────────────────────────────────────────────────

def cmd_state_get(plan_dir: Path, field: str | None):
    """Get state data — full JSON or specific field."""
    state = read_json(plan_dir / "state.json")
    if field:
        if field in state:
            val = state[field]
            print(json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val))
        else:
            print(f"Error: field '{field}' not found in state.json", file=sys.stderr)
            sys.exit(1)
    else:
        print(json.dumps(state, indent=2))


def cmd_state_current(plan_dir: Path):
    """Compact current state — just what's needed for resume."""
    state = read_json(plan_dir / "state.json")
    current = {
        "plan": state.get("plan"),
        "status": state.get("status"),
        "current_phase": state.get("current_phase"),
        "current_task": state.get("current_task"),
        "execution_start_commit": state.get("execution_start_commit"),
    }

    # Find active task substeps if any
    phase_num = state.get("current_phase")
    task_id = state.get("current_task")
    if phase_num and task_id:
        for p in state.get("phases", []):
            if p["phase"] == phase_num:
                for t in p.get("tasks", []):
                    if t["id"] == task_id and t.get("substeps"):
                        current["substeps"] = t["substeps"]
                break

    print(json.dumps(current, indent=2))


def cmd_state_show(plan_dir: Path):
    """Readable progress view."""
    state = read_json(plan_dir / "state.json")
    print(f"# Execution: {state.get('plan', 'Unknown')}")
    print(f"Status: {state.get('status', '?')} | Started: {state.get('started', '?')}")
    print(f"Last updated: {state.get('last_updated', '?')}")
    if state.get("execution_start_commit"):
        print(f"Start commit: {state['execution_start_commit']}")
    print()

    status_icons = {
        "completed": "[x]",
        "in_progress": "[>]",
        "pending": "[ ]",
        "failed": "[!]",
        "skipped": "[S]",
    }

    for p in state.get("phases", []):
        icon = status_icons.get(p.get("status", "pending"), "?")
        print(f"  {icon} Phase {p['phase']}: {p['name']} [{p.get('status', 'pending')}]")
        for t in p.get("tasks", []):
            t_icon = status_icons.get(t.get("status", "pending"), "?")
            print(f"    {t_icon} {t['id']}: {t['name']}")
            if t.get("substeps"):
                for s in t["substeps"]:
                    s_icon = "[x]" if s["status"] == "done" else "[ ]"
                    print(f"      {s_icon} {s['step']}")
            if t.get("error"):
                print(f"      Error: {t['error']}")
            if t.get("skip_reason"):
                print(f"      Skipped: {t['skip_reason']}")

        if p.get("review"):
            print(f"    Review: {p['review']}")
        print()

    if state.get("session_log"):
        print("## Session Log")
        for entry in state["session_log"]:
            print(f"  {entry.get('timestamp', '?')} — {entry.get('message', '')}")


def _get_state_and_phase(plan_dir: Path, phase_num: int) -> tuple[dict, dict]:
    """Helper: load state and find the phase entry."""
    state = read_json(plan_dir / "state.json")
    for p in state.get("phases", []):
        if p["phase"] == phase_num:
            return state, p
    print(f"Error: phase {phase_num} not found in state", file=sys.stderr)
    sys.exit(1)


def _get_task(phase_data: dict, task_id: str) -> dict:
    """Helper: find a task in a phase."""
    for t in phase_data.get("tasks", []):
        if t["id"] == task_id:
            return t
    print(f"Error: task '{task_id}' not found", file=sys.stderr)
    sys.exit(1)


def _save_state(plan_dir: Path, state: dict):
    """Helper: save state with updated timestamp."""
    state["last_updated"] = now_iso()
    write_json(plan_dir / "state.json", state)


def cmd_state_start_execution(plan_dir: Path, commit: str):
    """Mark execution started, record start commit."""
    state = read_json(plan_dir / "state.json")
    state["status"] = "executing"
    state["execution_start_commit"] = commit
    state["started"] = now_iso()
    _save_state(plan_dir, state)
    print(json.dumps({"status": "executing", "execution_start_commit": commit}))


def cmd_state_start_phase(plan_dir: Path, phase_num: int):
    """Mark phase as in_progress."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    phase["status"] = "in_progress"
    state["current_phase"] = phase_num
    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "status": "in_progress"}))


def cmd_state_set_active(plan_dir: Path, phase_num: int, task_id: str):
    """Set current active task."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    task = _get_task(phase, task_id)
    task["status"] = "in_progress"
    state["current_phase"] = phase_num
    state["current_task"] = task_id
    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "task": task_id, "status": "in_progress"}))


def cmd_state_complete_task(plan_dir: Path, phase_num: int, task_id: str):
    """Mark task as completed."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    task = _get_task(phase, task_id)
    task["status"] = "completed"
    task.pop("substeps", None)
    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "task": task_id, "status": "completed"}))


def cmd_state_fail_task(plan_dir: Path, phase_num: int, task_id: str, reason: str):
    """Mark task as failed with reason."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    task = _get_task(phase, task_id)
    task["status"] = "failed"
    task["error"] = reason
    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "task": task_id, "status": "failed", "error": reason}))


def cmd_state_skip_task(plan_dir: Path, phase_num: int, task_id: str, reason: str):
    """Mark task as skipped with reason."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    task = _get_task(phase, task_id)
    task["status"] = "skipped"
    task["skip_reason"] = reason
    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "task": task_id, "status": "skipped"}))


def cmd_state_substep(plan_dir: Path, phase_num: int, task_id: str, step: str, status: str):
    """Update a substep status (done or next)."""
    if status not in ("done", "next"):
        print("Error: substep status must be 'done' or 'next'", file=sys.stderr)
        sys.exit(1)

    state, phase = _get_state_and_phase(plan_dir, phase_num)
    task = _get_task(phase, task_id)

    if "substeps" not in task:
        task["substeps"] = []

    # Check if substep exists
    found = False
    for s in task["substeps"]:
        if s["step"] == step:
            s["status"] = status
            found = True
            break

    if not found:
        task["substeps"].append({"step": step, "status": status})

    _save_state(plan_dir, state)
    print(json.dumps({"phase": phase_num, "task": task_id, "substep": step, "status": status}))


def cmd_state_complete_phase(plan_dir: Path, phase_num: int):
    """Mark phase as completed."""
    state, phase = _get_state_and_phase(plan_dir, phase_num)
    phase["status"] = "completed"
    _save_state(plan_dir, state)
    cmd_state_log(plan_dir, f"Phase {phase_num}: {phase.get('name', '')} completed")
    print(json.dumps({"phase": phase_num, "status": "completed"}))


def cmd_state_complete(plan_dir: Path):
    """Mark execution as completed."""
    state = read_json(plan_dir / "state.json")
    state["status"] = "completed"
    _save_state(plan_dir, state)
    print(json.dumps({"status": "completed"}))


def cmd_state_pause(plan_dir: Path):
    """Mark execution as paused."""
    state = read_json(plan_dir / "state.json")
    state["status"] = "paused"
    _save_state(plan_dir, state)
    print(json.dumps({"status": "paused"}))


def cmd_state_log(plan_dir: Path, message: str):
    """Add a session log entry."""
    state = read_json(plan_dir / "state.json")
    if "session_log" not in state:
        state["session_log"] = []
    state["session_log"].append({"timestamp": now_iso(), "message": message})
    _save_state(plan_dir, state)


def cmd_state_set(plan_dir: Path, field: str, value: str):
    """Set a top-level field in state."""
    state = read_json(plan_dir / "state.json")
    # Try to parse as JSON (for numbers, bools, etc.)
    try:
        state[field] = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        state[field] = value
    _save_state(plan_dir, state)
    print(json.dumps({field: state[field]}))


# ─── Init & Find ─────────────────────────────────────────────────────────────

def cmd_find_active():
    """Find plan directory with active execution."""
    active = find_active_plan()
    if active:
        print(str(active))
    else:
        print("No active execution found.", file=sys.stderr)
        sys.exit(1)


def cmd_init(plan_dir_str: str):
    """Create state.json from plan.json + phase files."""
    plan_dir = Path(plan_dir_str)
    if not plan_dir.is_absolute():
        plan_dir = find_project_root() / plan_dir_str

    plan = read_json(plan_dir / "plan.json")

    phases = []
    for p_info in plan.get("phases", []):
        phase_file = plan_dir / f"phase-{p_info['phase']}.json"
        if phase_file.exists():
            phase_data = read_json(phase_file)
            tasks = [
                {"id": t["id"], "name": t["name"], "status": "pending"}
                for t in phase_data.get("tasks", [])
            ]
        else:
            tasks = []

        phases.append({
            "phase": p_info["phase"],
            "name": p_info["name"],
            "status": "pending",
            "tasks": tasks,
        })

    state = {
        "plan": plan.get("name", ""),
        "status": "approved",
        "current_phase": None,
        "current_task": None,
        "execution_start_commit": None,
        "last_updated": now_iso(),
        "started": None,
        "phases": phases,
        "session_log": [],
    }

    write_json(plan_dir / "state.json", state)
    print(json.dumps({"created": str(plan_dir / "state.json"), "phases": len(phases)}))


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # Extract --plan-dir if present
    plan_dir_arg = None
    if "--plan-dir" in args:
        idx = args.index("--plan-dir")
        if idx + 1 < len(args):
            plan_dir_arg = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --plan-dir requires a value", file=sys.stderr)
            sys.exit(1)

    cmd = args[0] if args else ""
    sub = args[1] if len(args) > 1 else ""

    # Routing
    if cmd == "find-active":
        cmd_find_active()
        return

    if cmd == "init" and len(args) >= 2:
        cmd_init(args[1])
        return

    if cmd == "plan":
        plan_dir = resolve_plan_dir(plan_dir_arg)
        if sub == "show":
            cmd_plan_show(plan_dir)
        elif sub == "get":
            cmd_plan_get(plan_dir, args[2] if len(args) > 2 else None)
        elif sub == "phases":
            cmd_plan_phases(plan_dir)
        elif sub == "set-status" and len(args) > 2:
            cmd_plan_set_status(plan_dir, args[2])
        else:
            print(f"Unknown plan command: {sub}", file=sys.stderr)
            sys.exit(1)
        return

    if cmd == "phase":
        plan_dir = resolve_plan_dir(plan_dir_arg)
        if len(args) < 3:
            print("Error: phase commands require a phase number", file=sys.stderr)
            sys.exit(1)
        phase_num = int(args[2])
        if sub == "show":
            cmd_phase_show(plan_dir, phase_num)
        elif sub == "tasks":
            cmd_phase_tasks(plan_dir, phase_num)
        elif sub == "task" and len(args) >= 4:
            cmd_phase_task(plan_dir, phase_num, args[3])
        else:
            print(f"Unknown phase command: {sub}", file=sys.stderr)
            sys.exit(1)
        return

    if cmd == "state":
        plan_dir = resolve_plan_dir(plan_dir_arg)
        if sub == "show":
            cmd_state_show(plan_dir)
        elif sub == "current":
            cmd_state_current(plan_dir)
        elif sub == "get":
            cmd_state_get(plan_dir, args[2] if len(args) > 2 else None)
        elif sub == "start-execution" and len(args) >= 3:
            cmd_state_start_execution(plan_dir, args[2])
        elif sub == "start-phase" and len(args) >= 3:
            cmd_state_start_phase(plan_dir, int(args[2]))
        elif sub == "set-active" and len(args) >= 4:
            cmd_state_set_active(plan_dir, int(args[2]), args[3])
        elif sub == "complete-task" and len(args) >= 4:
            cmd_state_complete_task(plan_dir, int(args[2]), args[3])
        elif sub == "fail-task" and len(args) >= 5:
            cmd_state_fail_task(plan_dir, int(args[2]), args[3], " ".join(args[4:]))
        elif sub == "skip-task" and len(args) >= 5:
            cmd_state_skip_task(plan_dir, int(args[2]), args[3], " ".join(args[4:]))
        elif sub == "substep" and len(args) >= 6:
            cmd_state_substep(plan_dir, int(args[2]), args[3], args[4], args[5])
        elif sub == "complete-phase" and len(args) >= 3:
            cmd_state_complete_phase(plan_dir, int(args[2]))
        elif sub == "complete":
            cmd_state_complete(plan_dir)
        elif sub == "pause":
            cmd_state_pause(plan_dir)
        elif sub == "log" and len(args) >= 3:
            cmd_state_log(plan_dir, " ".join(args[2:]))
        elif sub == "set" and len(args) >= 4:
            cmd_state_set(plan_dir, args[2], " ".join(args[3:]))
        else:
            print(f"Unknown state command: {sub}", file=sys.stderr)
            sys.exit(1)
        return

    print(f"Unknown command: {cmd}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
