---
alwaysApply: true
---

## Analysis Documents

Analysis docs (`.analysis.md`) are the component-level knowledge layer — persistent, enriched with each execution.

### Location & Naming
- **Co-located** with source: `src/services/authService.ts` → `src/services/authService.analysis.md`
- **Single-file:** `{FileName}.analysis.md` next to `{FileName}.{ext}`
- **Multi-file module:** `{module-name}.analysis.md` at module root (e.g., `src/modules/auth/auth.analysis.md`)

### Progressive Loading Levels
Use the CLI `analysis read` command with `--level` to read only what you need:

| Level | Contents | Tokens | Use case |
|-------|----------|--------|----------|
| 0 | Frontmatter only | ~50 | Scanning, staleness checks, dependency mapping |
| 1 | Frontmatter + CONTENT section | ~300-500 | Planning, understanding API, executor context |
| 2 | Full document | ~500-800 | Modifying the component's internals |

### Freshness
Use the CLI `analysis check` command to verify before reading. See `.claude/scripts/workflow_cli.reference.md`.
