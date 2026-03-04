## Description

<!-- Brief description of WHAT changed and WHY. Use Conventional Commits format for the PR title. -->

## Feature / Task

<!-- 1–3 sentences explaining the motivation. Link to the related issue. -->

Refs #<!-- ISSUE_NUMBER -->

---

## Changes

<!-- One section per logical change. List affected files and what changed. -->

### Change 1

**Files affected:**
- `path/to/file` — description of change

---

## Type of Change

- [ ] New feature (non-breaking)
- [ ] Bug fix (non-breaking)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] CI/CD change
- [ ] Dependency update
- [ ] Installer improvement

---

## Checklist

- [ ] Self-review completed
- [ ] Code follows project conventions (`ruff check .` passes)
- [ ] Code is formatted (`ruff format --check .` passes)
- [ ] Tests added/updated and passing (`uv run pytest`)
- [ ] No secrets committed (`detect-secrets scan`)
- [ ] Documentation updated if needed (README, CHANGELOG)
- [ ] No breaking changes to public tool contracts
- [ ] Installer tested with `--dry-run` (if installer changes)

---

## Testing

<!-- Describe how to verify this change. Include commands, expected output, etc. -->

```bash
uv run pytest -v
```

---

## Screenshots / Examples (optional)

<!-- Add screenshots, terminal output, or before/after examples if relevant. -->

---

## Additional Notes (optional)

<!-- Any extra context, trade-offs, or follow-up work. -->
