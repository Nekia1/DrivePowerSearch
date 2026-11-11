# Changelog
All notable changes to Drive Search (`drive_search`). The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/). Each release names the spec version it implements ([`docs/SPEC.md`](docs/SPEC.md)).

## [1.0.0] - 2026-11-11 (spec 1.5.0)
Merges the best of the earlier standalone build (a separate 1.0.0 in `VS_Code_Lessons/drive_search`, built from the prompt now archived in [`docs/archive/improved_prompt_v1.4.0.md`](docs/archive/improved_prompt_v1.4.0.md)) into this package.

### Added
- Standard header (Module, Description, Version, Created, Last updated) and a matching `__version__` in every `.py` file, checked by `tests/test_project_rules.py`.
- `__release_date__` in `drive_search/__init__.py`. `--version` prints `drive_search 1.0.0 (2026-11-11)`.
- Interactive mode: run with no arguments to be asked for the name and optional dates.
- `--include-trashed` and `--include-folders`.
- `--credentials` and `--token`, which take priority over `GDRIVE_CREDENTIALS` / `GDRIVE_TOKEN`.
- `#` row-number column in all three report outputs.
- Time zone abbreviation after the run time, for example `2026-11-10T14:32:05-05:00 (EST)`.
- A warning (file ID only) when a file has several parent folders.
- This changelog, and the archived standalone-build prompt.

### Changed
- **Folders are now excluded by default.** Use `--include-folders` to get them back.
- The missing-`credentials.json` message lists the five setup steps, not only a pointer to the guide.

## [0.2.0] - 2026-11-11 (spec 1.4.0)
### Added
- Reports show the tool version and run ID, matching the log's `run=<id>`.
- A clear message when `credentials.json` exists but isn't a valid "Desktop app" OAuth client file.
- `tests/test_project_rules.py`: only `auth.py` touches credentials, tokens and scopes, only `logging_setup.py` configures handlers, and no `print()` in the package.

### Changed
- Searches request 1,000 results per page (the API maximum) instead of 100.
- Report files are created exclusively, so two runs in the same second can't overwrite each other.
- `.gitignore` matches "transcript" in any letter case, on every operating system.

### Fixed
- HTTP 403 rate-limit errors that include Google's `details` block were not retried.

## [0.1.0] - 2026-11-10 (spec 1.3.1)
### Added
- First version of the package: `auth`, `logging_setup`, `cli`, `search`, `paths` and `reports` modules, an offline pytest suite with a fake Drive service, and the Google Cloud setup guide.
