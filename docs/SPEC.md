# Google Drive File Search Utility: Prompt

| | |
|---|---|
| **Version** | 1.5.0 |
| **Created** | 2026-11-10 |
| **Last updated** | 2026-11-11 |

**Changelog**
- **1.5.0** (2026-11-11): Merged the rest of the standalone build's prompt (`docs/archive/improved_prompt_v1.4.0.md`): standard file headers with per-file versions, `CHANGELOG.md`, `--include-trashed`, `--include-folders` (folders are now excluded by default), `--credentials`, `--token`, interactive prompts when run with no arguments, `--version` with release date, a `#` column, and a time zone abbreviation in the run time. Missing-`credentials.json` message lists the setup steps. New acceptance criteria.
- **1.4.0** (2026-11-11): Merged lessons from the earlier standalone `VS_Code_Lessons/drive_search` 1.0.0 build. Reports show the tool version and run ID. Rate limits are recognized in both Drive error formats. Searches request the largest page size. Report files are created exclusively. An invalid `credentials.json` gets its own message. A test enforces the module-boundary rules.
- **1.3.1** (2026-11-10): Moved from the Prompt_Engineering repo into `drive_search/docs/SPEC.md` (from Prompt_Engineering commit 27c4c13). No requirement changes.
- **1.3.0** (2026-11-10): The log folder is created on first run, its write access is checked on every run, and there is a fallback location. The default log folder is now next to the utility instead of in the current working directory.
- **1.2.0** (2026-11-10): Added a separate `logging_setup` module that records every operation, plus `--log-level` and `--log-dir` options.
- **1.1.0** (2026-11-10): Moved authentication and authorization into a separate `auth` module.
- **1.0.0** (2026-11-10): First structured version of the rough prompt.

## Goal
Build a Python command-line utility that searches my Google Drive for files by name and creation date. It prints a results report to the terminal and saves the same report as Markdown and HTML files.

## Environment
- Windows 11, PowerShell 5.1, Python 3.11+
- Access Drive through the official **Google Drive API v3** using `google-api-python-client` and `google-auth-oauthlib`.
- Authentication and authorization live in their own module. See the next section.

## Authentication and authorization module (`auth.py`)
Put all sign-in and permission logic in a separate module that the rest of the tool imports. No other module may read credential files, handle tokens, or name OAuth scopes.

- **Public interface:**
  - `get_credentials(credentials_path="credentials.json", token_path="token.json", scopes=DEFAULT_SCOPES) -> google.oauth2.credentials.Credentials`
  - `build_drive_service(credentials) -> Resource`: returns a ready-to-use Drive v3 client.
- **Flow:**
  1. If `token.json` exists and is valid, use it.
  2. If the token has expired but has a refresh token, refresh it silently and save the new token.
  3. Otherwise, run the OAuth 2.0 "Desktop app" flow (`InstalledAppFlow.run_local_server`) with the client secrets in `credentials.json`, then save the resulting token.
- **Scopes:** define `DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]` as a constant in this module. This is the narrowest scope that works. If the saved token was granted different scopes, ask me to sign in again instead of failing with an unclear error.
- **Configurable paths:** let the credential and token paths be overridden so the files can live outside the project folder. Precedence: the `--credentials` / `--token` options (passed in as function arguments), then the environment variables `GDRIVE_CREDENTIALS` / `GDRIVE_TOKEN`, then `credentials.json` / `token.json` in the project folder.
- **Errors:** raise custom exceptions (`CredentialsNotFoundError`, `AuthenticationError`) with clear messages. When `credentials.json` is missing, the message lists the numbered Google Cloud setup steps and points to `docs/google_cloud_setup.md`. A `credentials.json` that exists but isn't a valid "Desktop app" OAuth client file gets its own message telling me to download it again. Let the CLI decide how to show them, and don't call `sys.exit` inside this module.
- **Security:** never print or log token contents. Write `token.json` only to the configured path. Add `credentials.json` and `token.json` to `.gitignore`.
- **Reuse:** the module must not depend on the search or report code, so it can be reused in other Google Drive tools.

## Logging module (`logging_setup.py`)
Keep a record of every operation the tool performs. Put all logging configuration in one module, built on Python's standard `logging` library (no third-party logging packages).

- **Public interface:** `setup_logging(level="INFO", log_dir=None, verbose=False) -> str`. `None` means use the default log folder. It configures logging once, at program start, and returns a short **run ID**, for example the first 8 characters of a UUID.
- **How other modules log:** every module gets its own logger with `logger = logging.getLogger(__name__)`. No module except `logging_setup.py` adds handlers, sets formats, or calls `logging.basicConfig`. Use `logger` instead of `print` for everything except the report itself.
- **Handlers:**
  - **File:** `drive_search.log` in the log folder, UTF-8. Use a `RotatingFileHandler` (1 MB per file, keep 5 backups) so logs don't grow forever. The folder is prepared as described in "Log folder setup" below.
  - **Console:** writes to stderr so it never mixes with the report on stdout. It shows `WARNING` and above by default, or `INFO` and above with `--verbose`.
- **Format:** `2026-11-10T14:32:05.123-05:00 | INFO | run=3f9a1c2e | drive_search | Page 2 returned 100 files`. That is a local ISO 8601 timestamp with the time zone offset, then the level, run ID, module name, and message. Include the run ID on every line (use a `logging.Filter`) so you can find all the lines from one run.
- **What to log:**

  | Level | Events |
  |---|---|
  | `INFO` | Program start (tool version, Python version, search arguments) and end (exit code, total duration). Auth steps: cached token used, token refreshed, or browser sign-in started/completed. Each API page requested (query string, page number, number of files returned, time taken). Total matches. Each report file written (absolute path). |
  | `DEBUG` | Individual file names and IDs returned. Folder lookups during path rebuilding, with cache hits and misses. Full API request parameters. |
  | `WARNING` | Retries after rate limits (attempt number and wait time). Paths that couldn't be resolved. Saved token with different scopes. |
  | `ERROR` | Any failure that stops the run, with the full traceback (`logger.exception`) in the log file only. |

- **Privacy and security:** never log tokens, refresh tokens, client secrets, or the contents of `credentials.json` or `token.json`. File names are personal data, so log them only at `DEBUG`. At `INFO`, log only counts. Add `logs/` to `.gitignore`.
### Log folder setup (first run and every run)
The log folder must exist and be writable before the tool does anything else, including signing in or reading arguments beyond `--log-dir`, `--log-level`, and `--verbose`.

1. **Default location:** a `logs` folder next to the utility's own files, found with `Path(__file__).resolve().parent`, not the current working directory. That way the logs end up in the same place no matter which folder I run the tool from. `--log-dir` overrides this.
2. **First run:** create the folder and any missing parent folders (`Path.mkdir(parents=True, exist_ok=True)`). Running the tool again, or two copies at the same time, must not fail because the folder already exists.
3. **Every run, check write access:** create and then delete a small test file in the folder. Don't rely on the folder merely existing, because a folder can exist and still be read-only, locked by sync software such as OneDrive, or have changed permissions.
4. **Fallback location:** if step 2 or 3 fails, use `%LOCALAPPDATA%\DriveSearch\logs` on Windows, or `~/.drive_search/logs` if `LOCALAPPDATA` isn't set. Create and check it the same way, and print a one-line warning naming both the folder that failed and the fallback in use.
5. **Last resort:** if the fallback also fails, log to the console only, print a clear warning, and carry on with the search. Logging problems must never stop a search.
6. **Record the result:** once the handlers are attached, log at `INFO` which folder is in use. On first run, add "Created log folder at <path>". Logging isn't running when the folder is created, so hold that message until the handlers are ready.
7. **Report the folder:** `setup_logging` makes the folder actually in use available to the rest of the tool, for example as part of a small result object alongside the run ID. Error messages and `--verbose` output then show the real log path, not the requested one.

## Inputs (command-line arguments via `argparse`)
| Argument | Required | Meaning |
|---|---|---|
| `--name TEXT` | Yes | Text to match against the file name |
| `--exact` | No | Match the whole name exactly. Without it, find names that *contain* TEXT (case-insensitive) |
| `--created-on YYYY-MM-DD` | No | Only files created on this calendar date |
| `--created-after YYYY-MM-DD` / `--created-before YYYY-MM-DD` | No | Inclusive date range. Can't be combined with `--created-on` |
| `--include-shared-drives` | No | Also search shared drives, not just My Drive |
| `--include-trashed` | No | Include files in the trash. Default: excluded |
| `--include-folders` | No | Include folders in the results. Default: files only |
| `--credentials PATH` | No | OAuth client file. Default: see "Configurable paths" |
| `--token PATH` | No | Saved sign-in token file. Default: see "Configurable paths" |
| `--output-dir PATH` | No | Where to save reports. Default: `./search_results` |
| `--log-level LEVEL` | No | How much detail goes in the log file: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Default: `INFO` |
| `--log-dir PATH` | No | Where to save log files. Default: a `logs` folder next to the utility's own files (see "Log folder setup") |
| `--verbose` | No | Also show `INFO` log messages in the terminal. Without it, the terminal shows only warnings and errors |
| `--version` | No | Print `drive_search <version> (<release date>)` and exit |

**Interactive mode:** if the tool is run with no arguments at all, ask for the name text, then the optional "created after" and "created before" dates (blank skips a date). Ask again after an invalid date or a blank name. Prompts go through `rich`, not `print`. Ctrl+C or end-of-input cancels with exit code 130. All other options take their defaults.

Validate the inputs. Reject bad dates, `--created-on` combined with a range, and an "after" date that comes later than the "before" date. Each error should print a clear message and exit with a non-zero code.

## Search behavior
- Build the query with the Drive API `q` parameter (`name contains '...'`, `createdTime >= '...'`). Escape quotes in user input.
- Treat dates in my **local time zone** and convert them to UTC (RFC 3339) for the API.
- Exclude trashed files (`trashed = false`) unless `--include-trashed`. Exclude folders (`mimeType != 'application/vnd.google-apps.folder'`) unless `--include-folders`. Always include Google Docs/Sheets/Slides as well as uploaded files.
- Handle pagination (`nextPageToken`) so every match is returned, not just the first page. Request the largest page size the API allows (`pageSize=1000`) to keep the number of calls down.
- Rate limits: Drive reports them as HTTP 429, or as HTTP 403 with a reason (`rateLimitExceeded`, `userRateLimitExceeded`) in `error.errors[]`, or `RATE_LIMIT_EXCEEDED` in `error.details[]`. Recognize all of these and retry with backoff.
- **Full path:** Drive has no real paths. Rebuild one by walking each file's `parents` up to the root, for example `My Drive/Projects/2026/report.pdf`. Cache folder lookups to avoid repeated API calls. If a file has several parents, show the first one. If the path can't be resolved (for example, a file shared with me whose parent I can't see), show `(shared with me)/<name>`.
- Sort results by creation date, newest first.

## Report content (same in all three outputs)
1. Title: "Google Drive Search Report"
2. Search terms used: every argument and its value, including defaults
3. Report run date and time: local time, ISO 8601 format, with the time zone offset, followed by the time zone abbreviation, for example `2026-11-10T14:32:05-05:00 (EST)`. Windows gives long names such as "Eastern Standard Time", so shorten them to their initials.
4. Tool version and run ID, so a report can be matched to its lines in the log (`run=<id>`)
5. Total number of files found
6. Results table with these columns, in this order:
   - `#` (row number, starting at 1)
   - File name
   - Created (local time, `YYYY-MM-DD HH:MM`)
   - Modified (local time, `YYYY-MM-DD HH:MM`)
   - Full path
7. If nothing matches, show "No files found" instead of an empty table.

## Outputs
- **Terminal:** a readable aligned table (use `tabulate` or `rich`). Shorten long paths if needed so the table fits.
- **Markdown:** a valid GitHub-flavored Markdown table. Escape `|` characters in file names.
- **HTML:** a single self-contained page (inline CSS, no external dependencies) with a styled, readable table. The **full path is a hyperlink** to the file's Drive `webViewLink` and opens in a new tab. HTML-escape every value taken from Drive.
- File names: `drive_search_<YYYYMMDD_HHMMSS>.md` and `.html`, so earlier reports are never overwritten. Create each file exclusively (open mode `"x"`), adding `_2`, `_3`... on a clash, so two runs in the same second can't overwrite each other. Create the output folder if it doesn't exist.
- After saving, print the absolute paths of both report files.

## Error handling
Show friendly messages, not raw tracebacks, for these cases: `credentials.json` missing, authentication failed or was cancelled, network/API errors (retry rate-limit errors with backoff), and an output folder that can't be written to. Write the full traceback to the log file, and end the terminal message with the log file path, for example "See logs/drive_search.log for details."

## Code structure
Keep the parts separate so each can be tested on its own:

| Module | Responsibility |
|---|---|
| `auth.py` | Credentials, tokens, scopes, and building the Drive client (see above) |
| `logging_setup.py` | Setting up logging once: handlers, format, rotation, run ID (see above) |
| `cli.py` | Argument parsing, input checks, calling `setup_logging` first, and turning exceptions into friendly messages and exit codes |
| `search.py` | Building the query, calling the API, and pagination. Receives a Drive service object and never creates one itself |
| `paths.py` | Rebuilding full paths from parent folders, with caching |
| `reports.py` | Rendering the terminal, Markdown, and HTML outputs |

`__init__.py` holds the tool's `__version__` and `__release_date__`; `--version` and the reports read them from there. `__main__.py` lets the tool run as `python -m drive_search`.

The search module receives the Drive service as an argument (dependency injection). This makes it easy to pass in a mock during tests. Add type hints and short docstrings.

## Source file headers and versioning
- Use [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):
  - **MAJOR:** incompatible changes, such as a renamed or removed option, or a changed report format.
  - **MINOR:** new features that don't break existing use.
  - **PATCH:** bug fixes only.
- Every `.py` file, including tests, starts with this module docstring header. Any longer description follows after a blank line:
  ```python
  """
  Module:        drive_search/auth.py
  Description:   Google sign-in, token caching and Drive API client creation.
  Version:       1.0.0
  Created:       2026-11-10
  Last updated:  2026-11-11T09:30:00-05:00
  """
  ```
  - `Module` is the path from the project root. `Created` is a date (`YYYY-MM-DD`). `Last updated` is a full ISO 8601 timestamp with the time zone offset.
  - Each file also defines `__version__`, matching its header. Whenever a file changes, bump its version and update `Last updated`.
- The tool's own version is `__version__` in `drive_search/__init__.py`, with `__release_date__`. Each release gets an entry in `CHANGELOG.md`.

## Deliverables
1. A package with a clear entry point, for example `python -m drive_search --name budget --created-after 2026-01-01`
2. `setup/environment.yml` (the `powertools` conda environment, conda-forge first), plus `setup/requirements.txt` as a pip fallback
3. `README.md` with step-by-step Google Cloud setup (enable the Drive API, create OAuth desktop credentials, download `credentials.json`), install steps, how to reset the sign-in by deleting `token.json`, and usage examples. `CHANGELOG.md` with an entry for every release
4. `pytest` unit tests for query building, date validation and conversion, and Markdown/HTML rendering, including escaping and the "no results" case. Use a mocked Drive service so the tests make no network calls.
5. `pytest` unit tests for `auth.py` with the Google auth library mocked. Cover four cases: a valid cached token, an expired token that gets refreshed, no token (the sign-in flow runs), and a missing `credentials.json`.
6. `pytest` unit tests for logging, using `caplog` and a temporary folder. Check that:
   - the log file is created with the expected line format and run ID
   - console output respects `--verbose`
   - a missing log folder, including missing parent folders, is created on first run
   - a second run with the folder already in place works and adds to the same log file
   - an existing but read-only log folder switches to the fallback location, with a warning
   - if both the main and fallback folders fail, logging continues on the console only and the search still runs
   - no token or secret values appear in the log, even when auth fails

## Acceptance criteria
- A search with known matches returns every one of them, including results beyond the first API page and more than 1,000 files in total.
- A file named `Q1 | <Draft> & Notes.docx` displays correctly in all three outputs.
- `python -m drive_search --version` prints, for example, `drive_search 1.0.0 (2026-11-11)`.
- Every `.py` file has the standard header, and its `Version` matches its `__version__` (checked by `tests/test_project_rules.py`).
- Deleting `token.json` and running again opens the browser sign-in. A second run after that doesn't.
- All three outputs show the same search terms, run timestamp, count, and rows.
- Every path link in the HTML report opens the correct file in Drive.
- Running the tool twice produces two separate report pairs.
- Only `auth.py` reads credential or token files. A search for `credentials.json`, `token.json`, and scope URLs finds them in no other module.
- After the first sign-in, later runs don't open a browser until the token is revoked or the scopes change.
- On a fresh copy with no `logs` folder, the first run creates it next to the utility and logs "Created log folder at <path>". This works the same whichever folder I run the tool from.
- Each run adds one start line and one end line to `drive_search.log`, sharing the same run ID. Every API page, auth step, and report write in between is logged at `INFO`.
- At the default `INFO` level, the log contains no file names. At `DEBUG`, it does.
- Only `logging_setup.py` configures logging handlers. A search for `basicConfig`, `addHandler`, and `print(` finds none elsewhere, except `print` calls that output the report.
- The two rules above are enforced by a pytest test (`tests/test_project_rules.py`), not only by manual search.
- `pytest` passes.

## Out of scope
Downloading or changing files, searching file contents, and a GUI.

## Before writing code
If any requirement is ambiguous or conflicts with how the Drive API works, list your questions or assumptions first, then continue.
