# CLAUDE.md
- created: 2026-11-10

Google Drive search CLI. The spec is `..\Prompt_Engineering\Google drive search utility - IMPROVED PROMPT.md` (v1.3.0). Change the spec first (bump its version), then the code.

## Environment
- Windows 11, PowerShell 5.1 (no `&&`, `||`, `?:`, `??`).
- Anaconda at `C:\ProgramData\Anaconda3\`. conda is NOT on PATH, so call it by full path.
- Conda env: `powertools` (shared; defined in `environment.yml`, conda-forge only).

## Commands
- Tests: `C:\ProgramData\Anaconda3\Scripts\conda.exe run -n powertools python -m pytest`
- Run: `C:\ProgramData\Anaconda3\Scripts\conda.exe run -n powertools python -m drive_search --name <text>`

## Architecture rules (from the spec)
- Only `auth.py` touches credentials, tokens, or OAuth scopes.
- Only `logging_setup.py` configures logging handlers. Other modules use `logging.getLogger(__name__)`. No `print()`: the terminal output goes through rich in `reports.py` and `cli.py`.
- `search.py` and `paths.py` receive the Drive service and never build it, so tests use `tests/fakes.py`.
- At INFO, log counts only, never file names (those go at DEBUG). Never log token contents.
- Tests must make no network calls.

## Never commit
`credentials.json`, `token.json`, `logs/`, `search_results/`, `*transcript*` (all in `.gitignore`).
