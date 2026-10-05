Write idiomatic Python code for this repo. Simple, obvious, explicit. Less code beats clever code.

**Functions**
- One job per function. Return values; don't mutate caller state or globals. Inject dependencies; no package-level mutable state.
- Every function's inputs and outputs must be visible in its signature. No `*args`/`**kwargs`. No out-params that mutate caller data.
- Many parameters → options/config struct or dataclass.
- Guard clauses at top; happy path stays flat. Max 3 nesting levels.
- Name honestly. Don't abstract until the pattern appears three times.

**Errors**
- Be explicit about how a function fails. Return/raise clearly.
- Don't catch or swallow errors "just in case." Handle expected failures at boundaries; let unexpected ones propagate.
- No magic numbers; name constants.

**Code style**
- Type hints on all signatures. Use `pathlib`, f-strings.
- Config/tooling in `pyproject.toml` (ruff, pytest, mypy).
- Use venv/uv only.
- Comments explain why, not what. TODOs include ticket/context. No comments restating code.
- No docstrings that restate the signature.

**Structure**
- Feature folders (`src/image_toolkit/commands/` etc). One concept per file. Entry points at bottom, helpers above.
- Test success and failure paths if tests exist.

**Git/Docs**
- Do NOT commit or push unless explicitly asked.
- Default: no new markdown files/READMEs/docs. Improve code instead.
- Only one README at project root (directory with pyproject.toml). No READMEs deeper.
- No `docs/`, `doc/`, CHANGELOG, CONTRIBUTING, USAGE, API.md, "summary of changes".

**Tasks**
- Run lint/typecheck if commands exist (`uv run ruff check`, `uv run mypy .`) after edits.
- NEVER commit secrets/keys.
- Follow security best practices.
