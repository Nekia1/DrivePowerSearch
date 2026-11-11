# CLAUDE.md
- created: 2026-11-10

Google Drive search CLI. The spec is `docs/SPEC.md` (v1.5.x); the original idea is in `docs/rough_prompt.md`. Change the spec first (bump its version), then the code, ideally in the same commit.

## Layout
| Path | Contents |
|---|---|
| `drive_search/` | The package (6 modules, see below) |
| `tests/` | pytest suite; `tests/fakes.py` is the fake Drive service |
| `docs/` | `SPEC.md`, `rough_prompt.md`, `google_cloud_setup.md` (Drive API credentials guide; keep its error messages in sync with `auth.py`/`cli.py`), `archive/` (superseded documents, kept unchanged) |
| `CHANGELOG.md` | One entry per release (Keep a Changelog format), naming the spec version |
| `setup/` | `environment.yml` (conda env `powertools`), `requirements.txt` (pip fallback) |
| `pyproject.toml` | pytest settings (stays at the top level) |

## Environment
- Windows 11, PowerShell 5.1 (no `&&`, `||`, `?:`, `??`).
- Anaconda at `C:\ProgramData\Anaconda3\`. conda is NOT on PATH, so call it by full path. Never use conda `base`.
- Conda env: `powertools`, defined in `setup/environment.yml` (conda-forge only).

## Commands
- Tests: `C:\ProgramData\Anaconda3\Scripts\conda.exe run -n powertools python -m pytest`
- Run: `C:\ProgramData\Anaconda3\Scripts\conda.exe run -n powertools python -m drive_search --name <text>`

## Architecture rules (from the spec)
- Only `auth.py` touches credentials, tokens, or OAuth scopes.
- Only `logging_setup.py` configures logging handlers. Other modules use `logging.getLogger(__name__)`. No `print()`: the terminal output goes through rich in `reports.py` and `cli.py`.
- `search.py` and `paths.py` receive the Drive service and never build it, so tests use `tests/fakes.py`.
- At INFO, log counts only, never file names (those go at DEBUG). Never log token contents.
- Tests must make no network calls.

## File headers and versions (spec "Source file headers and versioning")
- Every `.py` file, tests included, starts with the standard header (Module path from the project root, Description, Version, Created, Last updated as an ISO 8601 timestamp with offset) and defines a matching `__version__`. `tests/test_project_rules.py` enforces this.
- When you change a file, bump its semver and update `Last updated`. New files start at `1.0.0`.
- The tool version is `__version__` and `__release_date__` in `drive_search/__init__.py`. For a release, bump it and add a `CHANGELOG.md` entry.

## Never commit
`credentials.json`, `token.json`, `logs/`, `search_results/`, `*transcript*` (all in `.gitignore`).
