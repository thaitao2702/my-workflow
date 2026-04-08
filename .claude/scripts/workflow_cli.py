#!/usr/bin/env python3
"""Workflow CLI — structured read/write for plan, phase, and state JSON files.

Usage:
  workflow-cli plan show [--plan-dir DIR]
  workflow-cli plan get [FIELD] [--plan-dir DIR]
  workflow-cli plan phases [--plan-dir DIR]
  workflow-cli plan set-status STATUS [--plan-dir DIR]
  workflow-cli plan review-dump [--plan-dir DIR]

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
  workflow-cli state add-discovery PHASE_N COMPONENT WHAT WHY RISK TEST CATEGORY [--plan-dir DIR]
  workflow-cli state add-decision PHASE_N COMPONENT DECISION REASONING [ALTERNATIVES] [--plan-dir DIR]
  workflow-cli state get-discoveries [--plan-dir DIR]
  workflow-cli state get-decisions [--plan-dir DIR]

  workflow-cli analysis check COMPONENT [--recursive]
  workflow-cli analysis read COMPONENT [--level 0|1|2]
  workflow-cli analysis list DIR

  workflow-cli read FILE [FILE ...]
  workflow-cli grep [--path P] [--type T] [--context N] PATTERN
  workflow-cli batch --commands 'JSON_ARRAY'

  workflow-cli find-active
  workflow-cli init PLAN_DIR
  workflow-cli hash FILE [FILE...]

  workflow-cli config get [FIELD]
"""

import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path


WORKFLOW_DIR = ".workflow/plans"


class CLIError(Exception):
    """Raised by command functions to signal user-facing errors."""
    pass


def find_project_root() -> Path:
    """Find project root by looking for .workflow/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".workflow").is_dir():
            return parent
    return cwd


def find_active_plans() -> list[Path]:
    """Find all plan directories with status executing or paused."""
    root = find_project_root()
    plans_dir = root / WORKFLOW_DIR
    if not plans_dir.exists():
        return []

    results = []
    for plan_dir in sorted(plans_dir.iterdir(), reverse=True):
        state_file = plan_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("status") in ("executing", "paused"):
                results.append(plan_dir)
    return results


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

    active = find_active_plans()
    if active:
        return active[0]

    latest = find_latest_plan()
    if latest:
        return latest

    raise CLIError("No plan directory found.")


def read_json(path: Path) -> dict:
    """Read a JSON file."""
    if not path.exists():
        raise CLIError(f"{path} not found.")
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
            raise CLIError(f"field '{field}' not found in plan.json")
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
        raise CLIError(f"status must be one of {valid}")
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


def cmd_plan_review_dump(plan_dir: Path):
    """Dump all plan data in an AI-agent-friendly format for plan review."""
    plan = read_json(plan_dir / "plan.json")

    # Load all phase files
    phases_data = []
    for p_info in plan.get("phases", []):
        phase_file = plan_dir / f"phase-{p_info['phase']}.json"
        if phase_file.exists():
            phases_data.append(read_json(phase_file))

    lines = []
    lines.append("═══════════════════════════════════════")
    lines.append("PLAN REVIEW PACKET")
    lines.append("═══════════════════════════════════════")
    lines.append("")

    # ── PLAN OVERVIEW ──
    lines.append("══ PLAN OVERVIEW ══")
    lines.append(f"Name: {plan.get('name', '')}")
    lines.append(f"Status: {plan.get('status', '')}")
    lines.append(f"Created: {plan.get('created', '')}")
    lines.append(f"Total phases: {plan.get('total_phases', '?')} | Total tasks: {plan.get('total_tasks', '?')}")
    lines.append("")

    lines.append("Summary:")
    lines.append(plan.get("summary", ""))
    lines.append("")

    scope = plan.get("scope", {})
    lines.append("Scope (in):")
    for item in scope.get("in_scope", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Scope (out):")
    for item in scope.get("out_of_scope", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Component Intelligence:")
    lines.append(plan.get("component_intelligence", ""))
    lines.append("")

    lines.append("Risks:")
    for risk in plan.get("risks", []):
        impact = risk.get("impact", "").upper()
        lines.append(f"- [{impact}] {risk.get('risk', '')} → Mitigation: {risk.get('mitigation', '')}")
    lines.append("")

    lines.append("Dependency Graph:")
    for p_info in plan.get("phases", []):
        deps = p_info.get("dependencies", [])
        dep_str = ", ".join(f"P{d}" for d in deps) if deps else "none"
        lines.append(f"P{p_info['phase']} ({p_info['name']}) → depends on: {dep_str}")
    lines.append("")

    # ── PHASE sections ──
    for phase in phases_data:
        pnum = phase.get("phase", "?")
        pname = phase.get("name", "")
        pgroup = phase.get("group", "?")
        pdeps = phase.get("depends_on", [])
        dep_str = ", ".join(str(d) for d in pdeps) if pdeps else "none"
        pstatus = phase.get("status", "pending")

        lines.append(f"══ PHASE {pnum}: {pname} ══")
        lines.append(f"Group: {pgroup} | Depends on: {dep_str} | Status: {pstatus}")
        lines.append("")

        lines.append("Goal:")
        lines.append(phase.get("goal", ""))
        lines.append("")

        affected = phase.get("affected_components", [])
        lines.append(f"Affected components: {', '.join(affected)}")
        lines.append("")

        for task in phase.get("tasks", []):
            lines.append(f"--- Task {task.get('id', '?')}: {task.get('name', '')} ---")
            lines.append(f"Description: {task.get('description', '')}")
            files = task.get("files", [])
            lines.append(f"Files: {', '.join(files)}")
            lines.append("Acceptance criteria:")
            for crit in task.get("acceptance_criteria", []):
                lines.append(f"  - {crit}")
            lines.append("Test requirements:")
            for req in task.get("test_requirements", []):
                lines.append(f"  - {req}")
            lines.append("")

        lines.append("Acceptance Specs:")
        for spec in phase.get("acceptance_specs", []):
            traces = spec.get("traces_to", [])
            lines.append(f"  {spec.get('id', '?')}: {spec.get('description', '')}")
            lines.append(f"    Traces to: {', '.join(traces)}")
            lines.append(f"    Verification: {spec.get('verification_type', '')}")
            lines.append(f"    Verify by: {spec.get('verify_by', '')}")
        lines.append("")

    # ═══ CROSS-REFERENCE TABLES ═══
    lines.append("═══════════════════════════════════════")
    lines.append("CROSS-REFERENCE TABLES")
    lines.append("═══════════════════════════════════════")
    lines.append("")

    # ── FILE OWNERSHIP by parallel group ──
    lines.append("══ FILE OWNERSHIP (by parallel group) ══")

    # Collect all groups
    group_files: dict[str, dict[str, list[str]]] = {}  # group -> filepath -> [phase+task refs]
    for phase in phases_data:
        pnum = phase.get("phase", "?")
        pgroup = phase.get("group", "?")
        if pgroup not in group_files:
            group_files[pgroup] = {}
        for task in phase.get("tasks", []):
            tid = task.get("id", "?")
            ref = f"Phase {pnum} {tid}"
            for f in task.get("files", []):
                if f not in group_files[pgroup]:
                    group_files[pgroup][f] = []
                group_files[pgroup][f].append(ref)

    for group in sorted(group_files.keys()):
        lines.append(f"Group {group}:")
        for filepath, refs in sorted(group_files[group].items()):
            lines.append(f"  {filepath} → {', '.join(refs)}")
    lines.append("")

    # ── REQUIREMENT TRACE ──
    lines.append("══ REQUIREMENT TRACE ══")

    _STOP_WORDS = {"with", "and", "the", "for", "in", "of", "a", "an", "to",
                   "is", "are", "be", "by", "from", "at", "on", "that", "this",
                   "all", "its", "as", "or"}

    def _keywords(text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        return {w for w in words if w not in _STOP_WORDS and len(w) > 2}

    def _task_matches_requirement(task: dict, req_keywords: set[str]) -> bool:
        task_text = (task.get("name", "") + " " + task.get("description", "")).lower()
        task_words = _keywords(task_text)
        return len(req_keywords & task_words) >= 2

    in_scope = scope.get("in_scope", [])
    req_trace: dict[str, list[str]] = {}  # requirement text -> [phase+task refs]
    for req in in_scope:
        req_kw = _keywords(req)
        matched = []
        for phase in phases_data:
            pnum = phase.get("phase", "?")
            for task in phase.get("tasks", []):
                if _task_matches_requirement(task, req_kw):
                    matched.append(f"Phase {pnum} {task.get('id', '?')}")
        req_trace[req] = matched

    for req, refs in req_trace.items():
        if refs:
            lines.append(f'  "{req}" → {", ".join(refs)}')
        else:
            lines.append(f'  "{req}" → (none)')
    lines.append("")

    # ── ACCEPTANCE SPEC TRACE ──
    lines.append("══ ACCEPTANCE SPEC TRACE ══")

    for phase in phases_data:
        pnum = phase.get("phase", "?")
        task_ids_in_phase = {t.get("id") for t in phase.get("tasks", [])}
        for spec in phase.get("acceptance_specs", []):
            spec_id = spec.get("id", "?")
            traces_to = spec.get("traces_to", [])
            validity_parts = []
            for tid in traces_to:
                if tid in task_ids_in_phase:
                    validity_parts.append(tid)
                else:
                    validity_parts.append(f"INVALID: {tid} not found")
            validity_str = ", ".join(validity_parts) if validity_parts else "(none)"
            is_valid = all(tid in task_ids_in_phase for tid in traces_to)
            valid_label = "valid" if is_valid else "INVALID"
            lines.append(f"  Phase {pnum} {spec_id} → traces_to: [{', '.join(traces_to)}] — {valid_label}")
    lines.append("")

    # Scope coverage: for each in_scope requirement, find which specs cover it
    lines.append("  Scope coverage:")
    # Build map: for each requirement, find specs whose traced tasks also match the requirement
    for req in in_scope:
        req_kw = _keywords(req)
        covering_specs = []
        for phase in phases_data:
            pnum = phase.get("phase", "?")
            task_map = {t.get("id"): t for t in phase.get("tasks", [])}
            for spec in phase.get("acceptance_specs", []):
                spec_id = spec.get("id", "?")
                traces_to = spec.get("traces_to", [])
                # Spec covers this requirement if any of its traced tasks match the requirement
                for tid in traces_to:
                    task = task_map.get(tid)
                    if task and _task_matches_requirement(task, req_kw):
                        covering_specs.append(f"{spec_id} (Phase {pnum})")
                        break
        if covering_specs:
            lines.append(f'  "{req}" → {", ".join(covering_specs)}')
        else:
            lines.append(f'  "{req}" → (no spec)')
    lines.append("")

    # ─── Planning Rules ───────────────────────────────────────────────────────
    root = find_project_root()
    planning_rules_dir = root / ".workflow" / "rules" / "planning"
    if planning_rules_dir.is_dir():
        md_files = sorted(planning_rules_dir.glob("*.md"))
        if md_files:
            lines.append("═══════════════════════════════════════")
            lines.append("PLANNING RULES")
            lines.append("═══════════════════════════════════════")
            lines.append("")
            for md_file in md_files:
                rule_name = md_file.stem
                lines.append(f"══ RULE: {rule_name} ══")
                lines.append(md_file.read_text(encoding="utf-8"))
                lines.append("")

    print("\n".join(lines))


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
    raise CLIError(f"task '{task_id}' not found in phase {phase_num}")


# ─── State Commands ──────────────────────────────────────────────────────────

def cmd_state_get(plan_dir: Path, field: str | None):
    """Get state data — full JSON or specific field."""
    state = read_json(plan_dir / "state.json")
    if field:
        if field in state:
            val = state[field]
            print(json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val))
        else:
            raise CLIError(f"field '{field}' not found in state.json")
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
    raise CLIError(f"phase {phase_num} not found in state")


def _get_task(phase_data: dict, task_id: str) -> dict:
    """Helper: find a task in a phase."""
    for t in phase_data.get("tasks", []):
        if t["id"] == task_id:
            return t
    raise CLIError(f"task '{task_id}' not found")


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
        raise CLIError("substep status must be 'done' or 'next'")

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


def cmd_state_add_discovery(plan_dir: Path, phase_num: int, component: str,
                            what: str, why: str, risk: str, test: str, category: str):
    """Add a structured discovery entry to state."""
    valid_categories = ("hidden_behavior", "wrong_assumption", "edge_case", "integration_gotcha")
    if category not in valid_categories:
        raise CLIError(f"category must be one of {valid_categories}")

    state = read_json(plan_dir / "state.json")
    if "discoveries" not in state:
        state["discoveries"] = []

    state["discoveries"].append({
        "phase": phase_num,
        "component": component,
        "what": what,
        "why": why,
        "risk": risk,
        "test_suggestion": test,
        "category": category,
        "timestamp": now_iso(),
    })
    _save_state(plan_dir, state)
    print(json.dumps({"added": "discovery", "phase": phase_num, "component": component}))


def cmd_state_add_decision(plan_dir: Path, phase_num: int, component: str,
                           decision: str, reasoning: str, alternatives: str):
    """Add a structured decision entry to state."""
    state = read_json(plan_dir / "state.json")
    if "decisions" not in state:
        state["decisions"] = []

    state["decisions"].append({
        "phase": phase_num,
        "component": component,
        "decision": decision,
        "reasoning": reasoning,
        "alternatives": alternatives,
        "timestamp": now_iso(),
    })
    _save_state(plan_dir, state)
    print(json.dumps({"added": "decision", "phase": phase_num, "component": component}))


def cmd_state_get_discoveries(plan_dir: Path):
    """Get all discoveries from state."""
    state = read_json(plan_dir / "state.json")
    discoveries = state.get("discoveries", [])
    print(json.dumps(discoveries, indent=2))


def cmd_state_get_decisions(plan_dir: Path):
    """Get all decisions from state."""
    state = read_json(plan_dir / "state.json")
    decisions = state.get("decisions", [])
    print(json.dumps(decisions, indent=2))


# ─── Init & Find ─────────────────────────────────────────────────────────────

def cmd_find_active():
    """Find plan directories with active execution."""
    active = find_active_plans()
    if active:
        for plan_dir in active:
            print(str(plan_dir))
    else:
        raise CLIError("No active execution found.")


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
        "discoveries": [],
        "decisions": [],
    }

    write_json(plan_dir / "state.json", state)
    print(json.dumps({"created": str(plan_dir / "state.json"), "phases": len(phases)}))


# ─── Analysis ─────────────────────────────────────────────────────────────────

def _compute_hash(files: list[str]) -> str:
    """Compute SHA-256 of concatenated file contents, sorted by path."""
    resolved = sorted(files)
    h = hashlib.sha256()
    root = find_project_root()
    for f in resolved:
        p = Path(f)
        if not p.is_absolute():
            p = root / f
        if not p.exists():
            raise FileNotFoundError(f)
        h.update(p.read_bytes())
    return h.hexdigest()


def _parse_frontmatter(analysis_path: Path) -> dict | None:
    """Parse YAML frontmatter from an analysis doc. Returns dict or None."""
    text = analysis_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm_text = text[3:end].strip()
    result = {}
    current_key = None
    current_list = None
    current_dict = None

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level key: value
        if not line.startswith(" ") and not line.startswith("\t") and ":" in stripped:
            # Save previous list/dict
            if current_key and current_list is not None:
                result[current_key] = current_list
                current_list = None
                current_dict = None

            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()

            if val.startswith("[") and val.endswith("]"):
                # Inline list: [a, b, c]
                items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                result[key] = items
                current_key = None
            elif val:
                result[key] = val.strip("'\"")
                current_key = None
            else:
                # Start of a block list or nested structure
                current_key = key
                current_list = []
                current_dict = None
        elif current_key is not None and stripped.startswith("- "):
            # List item
            content = stripped[2:].strip()
            if ":" in content and not content.startswith("["):
                # Dict item start: - key: value
                k, _, v = content.partition(":")
                current_dict = {k.strip(): v.strip().strip("'\"")}
                current_list.append(current_dict)
            elif content.startswith("[") and content.endswith("]"):
                # List item that is an inline list
                items = [v.strip().strip("'\"") for v in content[1:-1].split(",") if v.strip()]
                current_list.append(items)
            else:
                current_dict = None
                current_list.append(content.strip("'\""))
        elif current_dict is not None and ":" in stripped:
            # Continuation of a dict inside a list item
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                current_dict[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
            else:
                current_dict[k] = v.strip("'\"")

    # Flush last list
    if current_key and current_list is not None:
        result[current_key] = current_list

    return result


def _find_analysis_doc(component_path: Path) -> Path:
    """Derive analysis doc path from component path."""
    if component_path.is_dir():
        return component_path / f"{component_path.name}.analysis.md"
    else:
        return component_path.parent / f"{component_path.stem}.analysis.md"


def cmd_analysis_check(component: str, recursive: bool):
    """Check if analysis doc is fresh, stale, or missing."""
    root = find_project_root()
    comp_path = Path(component)
    if not comp_path.is_absolute():
        comp_path = root / component

    analysis_path = _find_analysis_doc(comp_path)

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(root))
        except ValueError:
            return str(p)

    if not analysis_path.exists():
        print(json.dumps({
            "status": "missing",
            "expected_path": _rel(analysis_path),
        }))
        return

    rel_analysis = _rel(analysis_path)
    fm = _parse_frontmatter(analysis_path)
    if not fm:
        print(json.dumps({
            "status": "stale",
            "analysis_path": rel_analysis,
            "reason": "no frontmatter found",
        }))
        return

    entry_files = fm.get("entry_files", [])
    stored_hash = fm.get("source_hash", "")

    if not entry_files or not stored_hash:
        print(json.dumps({
            "status": "stale",
            "analysis_path": rel_analysis,
            "reason": "missing entry_files or source_hash in frontmatter",
        }))
        return

    # Check source hash
    try:
        current_hash = _compute_hash(entry_files)
    except FileNotFoundError as e:
        print(json.dumps({
            "status": "stale",
            "analysis_path": rel_analysis,
            "reason": f"entry file not found: {e}",
        }))
        return

    if current_hash != stored_hash:
        print(json.dumps({
            "status": "stale",
            "analysis_path": rel_analysis,
            "reason": "source_hash mismatch",
            "entry_files": entry_files,
        }))
        return

    # Check dependency tree if recursive
    if recursive:
        dep_tree = fm.get("dependency_tree", [])
        if dep_tree and isinstance(dep_tree, list):
            for dep in dep_tree:
                if not isinstance(dep, dict):
                    continue
                dep_name = dep.get("name", "unknown")
                dep_files = dep.get("entry_files", [])
                dep_hash = dep.get("source_hash", "")

                if isinstance(dep_files, str):
                    dep_files = [dep_files]

                if dep_files and dep_hash:
                    try:
                        current_dep_hash = _compute_hash(dep_files)
                    except FileNotFoundError as e:
                        print(json.dumps({
                            "status": "stale",
                            "analysis_path": rel_analysis,
                            "reason": f"dependency file not found: {e}",
                            "changed_deps": [dep_name],
                        }))
                        return

                    if current_dep_hash != dep_hash:
                        print(json.dumps({
                            "status": "stale",
                            "analysis_path": rel_analysis,
                            "reason": "dependency stale",
                            "changed_deps": [dep_name],
                        }))
                        return

                # Check dependency's analysis doc exists
                if dep_files:
                    dep_path = Path(dep_files[0])
                    if not dep_path.is_absolute():
                        dep_path = root / dep_files[0]
                    dep_analysis = _find_analysis_doc(dep_path)
                    if not dep_analysis.exists():
                        print(json.dumps({
                            "status": "stale",
                            "analysis_path": rel_analysis,
                            "reason": "dependency analysis missing",
                            "changed_deps": [dep_name],
                        }))
                        return

    print(json.dumps({
        "status": "fresh",
        "analysis_path": rel_analysis,
    }))


def cmd_analysis_read(component: str, level: int):
    """Read analysis doc at specified progressive loading level."""
    root = find_project_root()
    comp_path = Path(component)
    if not comp_path.is_absolute():
        comp_path = root / component

    analysis_path = _find_analysis_doc(comp_path)

    if not analysis_path.exists():
        raise CLIError(f"analysis doc not found at {analysis_path}")

    text = analysis_path.read_text(encoding="utf-8")

    if level == 2:
        print(text)
        return

    if level == 0:
        # Frontmatter only: between first --- and second ---
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                print(text[:end + 3])
                return
        # Fallback: print whole file
        print(text)
        return

    # Level 1: frontmatter + CONTENT section
    parts = []

    # Extract frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            parts.append(text[:end + 3])

    # Extract CONTENT section
    content_start = text.find("<!-- PART:CONTENT_START -->")
    content_end = text.find("<!-- PART:CONTENT_END -->")
    if content_start != -1 and content_end != -1:
        parts.append(text[content_start:content_end + len("<!-- PART:CONTENT_END -->")])
    elif content_start != -1:
        # No end marker — take from start marker to EXTRA or end of file
        extra_start = text.find("<!-- PART:EXTRA_START -->")
        if extra_start != -1:
            parts.append(text[content_start:extra_start])
        else:
            parts.append(text[content_start:])

    if content_start != -1:
        # Had CONTENT markers — return frontmatter + extracted content
        print("\n\n".join(parts))
    else:
        # No CONTENT markers — return full file as fallback
        print(text)


def cmd_analysis_list(directory: str):
    """List all .analysis.md files in a directory."""
    root = find_project_root()
    dir_path = Path(directory)
    if not dir_path.is_absolute():
        dir_path = root / directory

    if not dir_path.is_dir():
        raise CLIError(f"{directory} is not a directory.")

    for p in sorted(dir_path.rglob("*.analysis.md")):
        print(str(p.relative_to(root)))


# ─── Hash ────────────────────────────────────────────────────────────────────

def cmd_hash(files: list[str]):
    """Compute SHA-256 of concatenated file contents, sorted by path."""
    try:
        print(_compute_hash(files))
    except FileNotFoundError as e:
        raise CLIError(f"{e} not found.")


# ─── Config ──────────────────────────────────────────────────────────────────

def cmd_config_get(field: str | None):
    """Get config data from .workflow/config.json."""
    root = find_project_root()
    config_path = root / ".workflow" / "config.json"
    if not config_path.exists():
        if field:
            print("null")
        else:
            print("{}")
        return
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if field:
        val = config.get(field)
        if val is None:
            print("null")
        else:
            print(json.dumps(val))
    else:
        print(json.dumps(config, indent=2))


# ─── Read Command ─────────────────────────────────────────────────────────────

def cmd_read(file_specs: list[str]):
    """Read one or more files and output contents with section headers."""
    root = find_project_root()

    for spec in file_specs:
        # Parse optional line range: FILE:start-end
        start_line: int | None = None
        end_line: int | None = None
        filepath = spec

        # Check for range suffix — look for :\d+-\d+$ pattern
        range_match = re.search(r"^(.+):(\d+)-(\d+)$", spec)
        if range_match:
            filepath = range_match.group(1)
            start_line = int(range_match.group(2))
            end_line = int(range_match.group(3))

        p = Path(filepath)
        if not p.is_absolute():
            p = root / filepath

        if start_line is not None:
            header = f"══ FILE: {filepath}:{start_line}-{end_line} ══"
        else:
            header = f"══ FILE: {filepath} ══"

        print(header)

        if not p.exists():
            print(f"ERROR: File not found: {filepath}")
            continue

        # Binary detection: check first 1024 bytes for null bytes
        try:
            first_bytes = p.read_bytes()[:1024]
        except OSError as e:
            print(f"ERROR: Cannot read file: {e}")
            continue

        if b"\x00" in first_bytes:
            print("(binary file, skipped)")
            continue

        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = p.read_text(encoding="latin-1")
            except Exception as e:
                print(f"ERROR: Cannot decode file: {e}")
                continue

        if not text:
            print("(empty file)")
            continue

        if start_line is not None:
            lines = text.splitlines(keepends=True)
            # 1-based indexing
            selected = lines[start_line - 1:end_line]
            print("".join(selected), end="" if selected and selected[-1].endswith(("\n", "\r")) else "\n")
        else:
            print(text, end="" if text.endswith(("\n", "\r\n", "\r")) else "\n")


# ─── Grep Command ─────────────────────────────────────────────────────────────

def _grep_python_fallback(pattern: str, search_path: Path, file_type: str | None, context_lines: int):
    """Pure Python grep fallback using re module."""
    # Map common type names to extensions
    type_ext_map: dict[str, list[str]] = {
        "py": [".py"],
        "js": [".js"],
        "ts": [".ts"],
        "tsx": [".tsx"],
        "jsx": [".jsx"],
        "java": [".java"],
        "go": [".go"],
        "rs": [".rs"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
        "rb": [".rb"],
        "php": [".php"],
        "sh": [".sh"],
        "md": [".md"],
        "json": [".json"],
        "yaml": [".yaml", ".yml"],
        "toml": [".toml"],
        "html": [".html", ".htm"],
        "css": [".css"],
        "sql": [".sql"],
    }
    allowed_exts: list[str] | None = type_ext_map.get(file_type, None) if file_type else None

    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise CLIError(f"Invalid regex pattern: {e}")

    output_lines = []

    def search_file(fp: Path):
        if allowed_exts is not None and fp.suffix.lower() not in allowed_exts:
            return
        try:
            first_bytes = fp.read_bytes()[:1024]
            if b"\x00" in first_bytes:
                return
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return

        lines = text.splitlines()
        for i, line in enumerate(lines):
            if compiled.search(line):
                # Gather context lines
                ctx_start = max(0, i - context_lines)
                ctx_end = min(len(lines), i + context_lines + 1)
                for j in range(ctx_start, ctx_end):
                    sep = ":" if j == i else "-"
                    output_lines.append(f"{fp}:{j + 1}{sep} {lines[j]}")
                if context_lines > 0 and ctx_end < len(lines):
                    output_lines.append("--")

    if search_path.is_file():
        search_file(search_path)
    elif search_path.is_dir():
        for fp in sorted(search_path.rglob("*")):
            if fp.is_file():
                search_file(fp)

    return "\n".join(output_lines)


def cmd_grep(pattern: str, search_path: str | None, file_type: str | None, context_lines: int):
    """Search for a regex pattern in files using ripgrep (rg) with Python fallback."""
    root = find_project_root()

    if search_path:
        p = Path(search_path)
        if not p.is_absolute():
            p = root / search_path
    else:
        p = root

    rg_args = ["rg", pattern, str(p)]
    if file_type:
        rg_args += ["--type", file_type]
    if context_lines > 0:
        rg_args += ["-C", str(context_lines)]

    try:
        result = subprocess.run(rg_args, capture_output=True, text=True)
        output = result.stdout
        if not output.strip():
            print("(no matches)")
        else:
            print(output, end="" if output.endswith("\n") else "\n")
    except FileNotFoundError:
        # rg not found — fall back to Python implementation
        output = _grep_python_fallback(pattern, p, file_type, context_lines)
        if not output.strip():
            print("(no matches)")
        else:
            print(output)


# ─── Batch Command ────────────────────────────────────────────────────────────

def cmd_batch(commands_json: str, plan_dir_override: str | None = None):
    """Execute multiple CLI sub-commands in one call, returning sectioned output."""
    try:
        commands = json.loads(commands_json)
    except json.JSONDecodeError as e:
        raise CLIError(f"Invalid JSON for --commands: {e}")

    if not isinstance(commands, list):
        raise CLIError("--commands must be a JSON array of strings")

    total = len(commands)
    results = []
    for idx, cmd_str in enumerate(commands, start=1):
        if not isinstance(cmd_str, str):
            results.append((idx, cmd_str, f"ERROR: command must be a string, got {type(cmd_str).__name__}"))
            continue

        try:
            sub_args = shlex.split(cmd_str, posix=True)
        except ValueError as e:
            results.append((idx, cmd_str, f"ERROR: Failed to parse command: {e}"))
            continue

        try:
            output = dispatch(sub_args, plan_dir_override=plan_dir_override)
        except Exception as e:
            output = f"ERROR: {e}"

        results.append((idx, cmd_str, output))

    output_parts = []
    for idx, cmd_str, out in results:
        output_parts.append(f"══ [{idx}/{total}] {cmd_str} ══")
        output_parts.append(out.rstrip("\n") if out else "")
        output_parts.append("")

    print("\n".join(output_parts))


# ─── Dispatch & Routing ───────────────────────────────────────────────────────

def _route(args: list[str], plan_dir_override: str | None = None):
    """Route parsed args to the appropriate command function.

    Raises CLIError on user-facing errors. Does not call sys.exit().
    """
    if not args:
        print(__doc__)
        return

    # Extract --plan-dir if present
    plan_dir_arg = plan_dir_override
    if "--plan-dir" in args:
        idx = args.index("--plan-dir")
        if idx + 1 < len(args):
            plan_dir_arg = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            raise CLIError("--plan-dir requires a value")

    cmd = args[0] if args else ""
    sub = args[1] if len(args) > 1 else ""

    # ── Routing ──

    if cmd == "find-active":
        cmd_find_active()
        return

    if cmd == "init" and len(args) >= 2:
        cmd_init(args[1])
        return

    if cmd == "hash" and len(args) >= 2:
        cmd_hash(args[1:])
        return

    if cmd == "config":
        if sub == "get":
            cmd_config_get(args[2] if len(args) > 2 else None)
        else:
            raise CLIError(f"Unknown config command: {sub}")
        return

    if cmd == "analysis":
        if sub == "check" and len(args) >= 3:
            recursive = "--recursive" in args
            cmd_analysis_check(args[2], recursive)
        elif sub == "read" and len(args) >= 3:
            level = 1  # default
            if "--level" in args:
                li = args.index("--level")
                if li + 1 < len(args):
                    level = int(args[li + 1])
            cmd_analysis_read(args[2], level)
        elif sub == "list" and len(args) >= 3:
            cmd_analysis_list(args[2])
        else:
            raise CLIError(f"Unknown analysis command: {sub}")
        return

    if cmd == "read":
        if len(args) < 2:
            raise CLIError("read requires at least one FILE argument")
        cmd_read(args[1:])
        return

    if cmd == "grep":
        # grep [--path P] [--type T] [--context N] PATTERN
        remaining = args[1:]
        grep_path: str | None = None
        grep_type: str | None = None
        grep_context: int = 0

        i = 0
        while i < len(remaining):
            if remaining[i] == "--path" and i + 1 < len(remaining):
                grep_path = remaining[i + 1]
                i += 2
            elif remaining[i] == "--type" and i + 1 < len(remaining):
                grep_type = remaining[i + 1]
                i += 2
            elif remaining[i] == "--context" and i + 1 < len(remaining):
                try:
                    grep_context = int(remaining[i + 1])
                except ValueError:
                    raise CLIError(f"--context must be an integer, got: {remaining[i + 1]}")
                i += 2
            else:
                # Remaining arg is the pattern (last positional)
                i += 1

        # Pattern is the last non-flag positional argument
        positional = [
            a for j, a in enumerate(remaining)
            if not (a.startswith("--") or (j > 0 and remaining[j - 1] in ("--path", "--type", "--context")))
        ]
        if not positional:
            raise CLIError("grep requires a PATTERN argument")
        pattern = positional[-1]
        cmd_grep(pattern, grep_path, grep_type, grep_context)
        return

    if cmd == "batch":
        commands_json: str | None = None
        remaining = args[1:]
        i = 0
        while i < len(remaining):
            if remaining[i] == "--commands" and i + 1 < len(remaining):
                commands_json = remaining[i + 1]
                i += 2
            else:
                i += 1
        if commands_json is None:
            raise CLIError("batch requires --commands 'JSON_ARRAY'")
        cmd_batch(commands_json, plan_dir_override=plan_dir_arg)
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
        elif sub == "review-dump":
            cmd_plan_review_dump(plan_dir)
        else:
            raise CLIError(f"Unknown plan command: {sub}")
        return

    if cmd == "phase":
        plan_dir = resolve_plan_dir(plan_dir_arg)
        if len(args) < 3:
            raise CLIError("phase commands require a phase number")
        phase_num = int(args[2])
        if sub == "show":
            cmd_phase_show(plan_dir, phase_num)
        elif sub == "tasks":
            cmd_phase_tasks(plan_dir, phase_num)
        elif sub == "task" and len(args) >= 4:
            cmd_phase_task(plan_dir, phase_num, args[3])
        else:
            raise CLIError(f"Unknown phase command: {sub}")
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
        elif sub == "add-discovery" and len(args) >= 9:
            # state add-discovery PHASE_N COMPONENT WHAT WHY RISK TEST CATEGORY
            cmd_state_add_discovery(
                plan_dir, int(args[2]), args[3],
                args[4], args[5], args[6], args[7], args[8]
            )
        elif sub == "add-decision" and len(args) >= 7:
            # state add-decision PHASE_N COMPONENT DECISION REASONING ALTERNATIVES
            cmd_state_add_decision(
                plan_dir, int(args[2]), args[3],
                args[4], args[5], args[6] if len(args) > 6 else ""
            )
        elif sub == "get-discoveries":
            cmd_state_get_discoveries(plan_dir)
        elif sub == "get-decisions":
            cmd_state_get_decisions(plan_dir)
        elif sub == "set" and len(args) >= 4:
            cmd_state_set(plan_dir, args[2], " ".join(args[3:]))
        else:
            raise CLIError(f"Unknown state command: {sub}")
        return

    raise CLIError(f"Unknown command: {cmd}")


def dispatch(args: list[str], plan_dir_override: str | None = None) -> str:
    """Route args to the correct command and return its stdout output as a string.

    Catches CLIError and returns "ERROR: {message}" instead of raising.
    """
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            _route(args, plan_dir_override)
    except CLIError as e:
        return f"ERROR: {e}"
    return buf.getvalue()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Ensure stdout/stderr use UTF-8 on all platforms (esp. Windows)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = sys.argv[1:]
    if not args:
        sys.stdout.write(__doc__ + "\n")
        sys.exit(0)

    try:
        buf = io.StringIO()
        error_occurred = False
        error_msg = ""
        try:
            with redirect_stdout(buf):
                _route(args)
        except CLIError as e:
            error_occurred = True
            error_msg = str(e)

        if error_occurred:
            sys.stderr.write(f"Error: {error_msg}\n")
            sys.exit(1)
        else:
            output = buf.getvalue()
            if output:
                sys.stdout.write(output)
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
