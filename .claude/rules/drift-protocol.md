---
alwaysApply: true
---

## Drift Prevention Protocol

Long-running skills and multi-task agents suffer from attention drift — the model attends to its recent output rather than earlier instructions. Checkpoints are structured attention anchors emitted at step/task boundaries to prevent this.

### Skill Checkpoints (Main Session)

After completing each step in a skill, emit a checkpoint before proceeding to the next step.

```
---CHECKPOINT---
Done: [what was just completed — 1 line]
Next: [what the next step requires — summarize the instruction
       in your own words. If the step has substeps, outline the
       key actions. This is active recall of the SKILL.md
       instruction, not just the step name.]
User directives: [list any corrections, decisions, or constraints
                  the user gave during this session that are still
                  active. "None" if none.]
---END CHECKPOINT---
```

**Why "Next" must include instruction detail:** By the time you finish a step, the SKILL.md instruction for the next step is in system context but far from your attention. Outputting what the next step requires forces active recall — re-engaging with the instruction and placing it near the generation point where you will use it.

### Agent Checkpoints (Subagents)

Agents are self-contained — they receive all instructions upfront and do not interact with the user. Their drift is from generated code overwhelming the initial prompt. They need state re-anchoring, not directive tracking.

After completing each task (executor) or component (analyzer), emit a checkpoint before the next one.

```
---CHECKPOINT---
Done: [task/component completed — 1 line]
Next: [next task/component]
Goal: [re-state the phase goal or analysis goal — 1 line]
---END CHECKPOINT---
```

**Why re-state the goal:** After thousands of tokens of generated code, the phase goal from the initial prompt is far away. Re-stating it prevents scope drift in later tasks.

### Directive Capture (Main Session)

When the user provides a correction, decision, or constraint during skill execution:

1. Acknowledge: "Captured: {summary}"
2. Include in all subsequent checkpoint `User directives` fields
3. When spawning agents that have a `{user_directives}` placeholder in their prompt template, include active directives
4. If a plan is active (`$PLAN_DIR` set), also persist for cross-session survival: `state log "DIRECTIVE: {text}" --plan-dir $PLAN_DIR`
