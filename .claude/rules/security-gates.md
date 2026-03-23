---
alwaysApply: true
---

## Security Gates

### Blocked (always reject — no exceptions)
- `DROP DATABASE`, `TRUNCATE TABLE`
- `git push --force` to main/master
- `rm -rf /`
- Piped remote execution: `curl | sh`, `wget | bash`
- Hardcoded secrets in source code (API keys, passwords, tokens)

### Ask Confirmation (pause and confirm with user)
- `git reset --hard`
- Destructive database migrations (column drops, table drops)
- File deletion outside project directory
- `npm install` / `pip install` / `cargo add` of new dependencies
- Modifications to CI/CD pipeline files
- Changes to authentication/authorization logic

### Why
AI agents can and do execute dangerous commands. Blocking the catastrophic ones and gating the risky ones prevents irreversible damage. The blocked list is non-negotiable. The confirmation list is a speed bump — the user can approve but must be aware.
