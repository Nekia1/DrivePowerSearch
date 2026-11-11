> **Archived (2026-11-11).** This is the build prompt behind the earlier standalone `drive_search` 1.0.0 (a flat `drive_search.py` / `auth.py` / `log_setup.py` layout). Its requirements were merged into [`docs/SPEC.md`](../SPEC.md) 1.4.0 and 1.5.0, which replaces it. Kept unchanged below for history. Module names and some defaults here differ from the current tool.

# Google Drive File Search Utility

| | |
|---|---|
| **Document** | Build prompt: Google Drive File Search Utility |
| **Version** | 1.4.0 |
| **Created** | 2026-11-10 |
| **Last updated** | 2026-11-11 |

**Change log**
- **1.4.0** (2026-11-11): The project now uses the conda environment `powertools`, defined in `environment.yml` (conda-forge first, pip only as a fallback). This replaces `requirements.txt`.
- **1.3.0** (2026-11-11): The log folder is created automatically on first run, next to the script instead of the current folder. Added a write check, a backup location and a terminal-only fallback, so logging is always available.
- **1.2.0** (2026-11-11): Added a separate `log_setup.py` logging module, `--log-level` and `--log-dir` options, and logging requirements for every operation.
- **1.1.0** (2026-11-11): Moved authentication into a separate `auth.py` module. Added version and timestamp headers to all source files, a `--version` flag, and the tool version in the report header.
- **1.0.0** (2026-11-10): First structured version of the prompt.

## Goal
Build a Python command-line utility that searches my Google Drive for files by **name** and **creation date range**. It prints a report of matching files to the terminal and saves the same report as **Markdown** and **HTML** files in a `search_results` folder.

If any requirement below is ambiguous or conflicts with how the Google Drive API works, ask me before writing code.

## Environment
- Windows 11, Python 3.11+ (Anaconda). Use `pathlib` so the tool also runs on macOS and Linux.
- Google Drive API v3 via `google-api-python-client` and `google-auth-oauthlib`.
- Conda environment **`powertools`**, defined in the existing `environment.yml`. Python 3.12.
  - Channels: `conda-forge` only (`nodefaults`). Use pip only for a package that isn't on conda-forge, listed under the file's `pip:` section with an exact version.
  - Don't add a package without adding it to `environment.yml`. Keep the file's header (version and last-updated date) current.
- Authentication and authorization live in their own module, `auth.py`. See [Authentication module](#authentication-module-authpy).
- Logging setup lives in its own module, `log_setup.py`. See [Logging module](#logging-module-log_setuppy).

## Authentication module (`auth.py`)
All Google sign-in, token handling and API client creation goes in `auth.py`. No other module imports Google auth libraries or reads credential files directly.

**Public interface**
```python
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

class AuthError(Exception):
    """Raised when credentials are missing, invalid or cannot be refreshed."""

def get_credentials(credentials_path: Path, token_path: Path,
                    scopes: list[str] = SCOPES) -> Credentials: ...

def build_drive_service(credentials_path: Path, token_path: Path): ...
    # Returns an authorized Drive API v3 client.
```

**Behavior**
- Uses the OAuth "Desktop app" flow and requests only the **read-only** scope above.
- Load the cached token from `token_path` if it exists and is valid.
- If the token is expired but has a refresh token, refresh it silently.
- If refresh fails (token revoked, or scopes changed), delete the cached token and run the browser sign-in again.
- After a successful sign-in or refresh, save the token back to `token_path`.
- If `credentials_path` doesn't exist, raise `AuthError` with step-by-step setup instructions. Don't print or call `sys.exit()` inside `auth.py`; the command-line code catches `AuthError`, prints the message and exits.
- Never log or print token contents.
- Default paths are `credentials.json` and `token.json` next to the script. Both can be overridden with command-line arguments.
- Neither file is ever committed; include a `.gitignore`.

## Logging module (`log_setup.py`)
Every operation the tool performs is recorded in a log file, so I can see what happened on any run and troubleshoot failures.

Name the module `log_setup.py`, **not** `logging.py`. A file called `logging.py` would hide Python's built-in `logging` library.

**Public interface**
```python
def setup_logging(log_dir: Path | None = None,
                  console_level: str = "WARNING",
                  file_level: str = "DEBUG") -> tuple[str, Path | None]: ...
    # Configures logging once per run.
    # Returns (run_id, log_file_path). log_file_path is None only if no folder could be written to.
```

**Design**
- Use Python's standard `logging` library.
- `log_setup.py` is the only place handlers and formats are configured. Every other module just calls `logger = logging.getLogger(__name__)` and logs through it.
- `drive_search.py` calls `setup_logging()` first, before any other work, including authentication.
- Never use `print()` for diagnostic messages. `print()` (or `rich`) is only for the report itself and the final "saved to" lines.

**Log folder: created automatically on first run**

The utility must always have a usable log folder, with no manual setup. On every run, `setup_logging()` does the following before anything else is logged:

1. **Pick the folder.**
   - If `--log-dir` is given, use it.
   - Otherwise use a `logs` folder **next to the script** (`Path(__file__).resolve().parent / "logs"`), not the current folder. This puts logs in the same place no matter which folder the tool is run from, including Windows Task Scheduler.
2. **Create it if missing.** Use `mkdir(parents=True, exist_ok=True)`, so the first run creates it and later runs reuse it. Two runs starting at the same moment must not crash.
3. **Confirm it can be written to.** Create and delete a small test file in the folder. Checking that the folder exists isn't enough, because it may be read-only or blocked by permissions, OneDrive sync or antivirus.
4. **If that fails, use a backup folder** in the user's own app-data folder, which is always writable:
   - Windows: `%LOCALAPPDATA%\drive_search\logs`
   - macOS: `~/Library/Logs/drive_search`
   - Linux: `~/.local/state/drive_search/logs`

   Create and test it the same way. Then log a `WARNING` saying the first folder wasn't writable and where logs are going instead.
5. **If both fail, keep running with terminal-only logging.** Print one warning to `stderr` explaining that no log file could be created and why. A logging problem must never stop a search.
6. **On first creation**, log an `INFO` line: `Log folder created: <full path>`.

Use only the Python standard library for this (`pathlib`, `os`); no extra packages.

**Log file**
- Written to `drive_search.log` inside the log folder.
- Rotate the file at 5 MB and keep 5 old copies (`RotatingFileHandler`), so logs never fill the disk.
- UTF-8 encoding, so file names in any language log correctly.
- The file records everything at `DEBUG` level and above.
- Line format:
  ```
  2026-11-11T09:30:00.123-05:00 | INFO | a1b2c3d4 | drive_search | Search started: name="budget", created_after=2025-01-01
  ```
  The fields are: ISO 8601 timestamp with time zone offset, level, run ID, module name and message.
- The run ID is a short random ID (first 8 characters of a UUID) generated once per run. It's added to every line, so all lines from one run can be found together. Also print it in the report header.

**Console**
- Log messages go to the terminal's error stream (`stderr`), so they never mix into the report output.
- The default terminal level is `WARNING`, so normal runs show only the report. `--log-level DEBUG` or `--log-level INFO` shows more.

**What gets logged**

| Level | Events |
|---|---|
| `INFO` | Run start (tool version, run ID, all arguments, Python version, operating system). Sign-in method used: cached token, silent refresh, or browser sign-in. Search started. Total files found. Each report file written, with its path. Run finished, with exit code and total duration. |
| `DEBUG` | The Drive query string. Each API page fetched, with file count. Folder lookups during path resolution, with cache hits and misses. Output folder created. |
| `WARNING` | API retries (status code, attempt number, wait time). Files with more than one parent. Parent folders that couldn't be accessed. Zero results. |
| `ERROR` | Invalid arguments. `AuthError`. API failures after all retries. Errors writing report files. |
| `CRITICAL` | Any unexpected error. Log it with the full traceback (`logger.exception`) in the log file. The terminal shows only a one-line message and the log file path. |

**Privacy and security**
- Never log access tokens, refresh tokens, client secrets, or the contents of `credentials.json` or `token.json`. File paths to those files are fine.
- Individual file names from my Drive appear only at `DEBUG` level. At `INFO` and above, log counts only.

## Inputs (command-line arguments)

| Argument | Required | Meaning | Example |
|---|---|---|---|
| `--name` | Yes | Text to match in the file name. Case-insensitive "contains" match. | `--name "budget"` |
| `--exact` | No | Match the whole file name exactly instead of "contains". | `--exact` |
| `--created-after` | No | Earliest creation date, `YYYY-MM-DD`, inclusive. | `--created-after 2025-01-01` |
| `--created-before` | No | Latest creation date, `YYYY-MM-DD`, inclusive (whole day). | `--created-before 2025-12-31` |
| `--include-trashed` | No | Include files in the trash. Default: excluded. | |
| `--include-folders` | No | Include folders in results. Default: files only. | |
| `--output-dir` | No | Where reports are saved. Default: `./search_results`. | |
| `--credentials` | No | Path to the OAuth client file. Default: `credentials.json` next to the script. | |
| `--token` | No | Path to the cached token file. Default: `token.json` next to the script. | |
| `--log-level` | No | Terminal log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default: `WARNING`. The log file always records `DEBUG`. | `--log-level INFO` |
| `--log-dir` | No | Where log files are saved. Default: a `logs` folder next to the script, created automatically on first run. | |
| `--version` | No | Print the tool's version and release date, then exit. | |

- To search a single day, pass the same date to both `--created-after` and `--created-before`.
- Dates are interpreted in my local time zone and converted to UTC for the API query.
- If the script is run with no arguments, prompt interactively for the name and the optional dates.
- Reject invalid dates, or `--created-after` later than `--created-before`, with a clear message.

## Search behavior
- Search My Drive, shared drives, and files shared with me (`corpora=allDrives`, `supportsAllDrives=True`, `includeItemsFromAllDrives=True`).
- Escape quotes and backslashes in the name before inserting it into the Drive query string.
- Follow `nextPageToken` until all results are retrieved. Never silently stop at the first page.
- Request only the fields needed: `id, name, mimeType, createdTime, modifiedTime, parents, webViewLink`.
- Retry on HTTP 429 and 5xx errors with exponential backoff (max 5 attempts).
- Note in the README that Drive's `name contains` operator matches word prefixes, so `--name port` finds "port_report.txt" but may not find "report.txt".

## Full path resolution
The Drive API does not return file paths, so build one by walking each file's `parents` up to the root.
- Cache folder lookups so each folder is fetched only once.
- Root naming: `My Drive/...` for My Drive, `<Shared drive name>/...` for shared drives, `Shared with me/<file name>` when parent folders are not accessible.
- If a file has more than one parent, use the first one.

## Report contents (identical in all three outputs)

**Header**
1. Title: "Google Drive Search Report"
2. Search terms used: every parameter, including defaults (e.g. "Trashed: excluded").
3. Report generated: local date and time with time zone, e.g. `2026-11-10 14:32:05 EST`.
4. Tool version and run ID, e.g. `drive_search 1.0.0, run a1b2c3d4`.
5. Total files found.

**Results table**, sorted by creation date, newest first:

| # | File name | Created | Modified | Full path |
|---|---|---|---|---|

- Created and Modified are shown as `YYYY-MM-DD HH:MM` in local time.
- If no files match, show "No files matched these search terms." instead of an empty table.

## Outputs
1. **Terminal:** a readable, aligned table (use `rich` or `tabulate`). Long paths may be shortened to fit the terminal width; the saved files always contain the full path.
2. **Markdown:** `search_results/drive_search_YYYYMMDD_HHMMSS.md` as a GitHub-flavored Markdown table. Escape `|` and other Markdown-special characters in file names and paths.
3. **HTML:** same base name with a `.html` extension. A single self-contained file with inline CSS and no external dependencies.
   - The **Full path** cell is a link to the file's `webViewLink`, opening in a new tab (`target="_blank" rel="noopener noreferrer"`).
   - HTML-escape all file names and paths.
- Create the output folder if it doesn't exist. Use a timestamp in the filename so earlier reports are never overwritten.
- After saving, print the paths of both report files.

## Error handling and exit codes
- `AuthError` from `auth.py` (e.g. missing `credentials.json`): print its setup instructions and exit with code `1`.
- API or network failure after retries: print a clear error (not a raw traceback) and exit.
- Every error is also logged as described in the [Logging module](#logging-module-log_setuppy) section. The terminal error message ends with the log file path.
- Exit codes: `0` = success (including zero results), `1` = runtime or API error, `2` = invalid arguments.

## Source file headers and versioning
- Use [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`), starting at `1.0.0`:
  - **MAJOR**: incompatible changes, such as renamed or removed arguments, or a changed report format.
  - **MINOR**: new features that don't break existing use.
  - **PATCH**: bug fixes only.
- Every `.py` file starts with a module docstring header in this format:
  ```python
  """
  Module:        auth.py
  Description:   Google OAuth sign-in, token caching and Drive API client creation.
  Version:       1.0.0
  Created:       2026-11-11
  Last updated:  2026-11-11T09:30:00-05:00
  """
  ```
  - `Created` is a date (`YYYY-MM-DD`). `Last updated` is a full ISO 8601 timestamp with time zone offset.
  - Each module also defines `__version__ = "1.0.0"`, matching its header.
- The tool's version is defined once, as `__version__` and `__release_date__` in `drive_search.py`. The `--version` flag and the report header read it from there.
- Whenever a file changes, bump its version and update `Last updated`.
- Add a `CHANGELOG.md` with an entry for `1.0.0`.

## Deliverables
1. `auth.py`: the authentication module described above.
2. `log_setup.py`: the logging module described above.
3. `drive_search.py`: the command-line entry point. Organize it into separate functions for query building, searching, path resolution and report rendering, so rendering can be tested without calling the API. It gets its Drive client only from `auth.build_drive_service()`, and calls `log_setup.setup_logging()` before anything else.
4. `environment.yml` (already exists): update it only if a new package is needed.
5. `README.md` covering: creating and activating the `powertools` environment (`conda env create -f environment.yml`, `conda activate powertools`), creating a Google Cloud project, enabling the Drive API, creating OAuth Desktop credentials, the first-run sign-in, how to reset a sign-in by deleting `token.json`, where logs are saved and how to use `--log-level`, and 3 example commands.
6. `CHANGELOG.md`.
7. `tests/` with `pytest` tests that run offline using fake data:
   - `test_auth.py`: mock the Google libraries to cover a valid cached token, refreshing an expired token, a failed refresh falling back to a new sign-in, and a missing `credentials.json` raising `AuthError`.
   - `test_log_setup.py`: using temporary folders, check that:
     - a missing log folder (including missing parent folders) is created on first run and reused on the second
     - a read-only log folder falls back to the backup location, with a warning
     - when no folder can be written to, the tool keeps running with terminal-only logging, and `setup_logging()` returns `None` for the log file path
     - the line format and run ID are correct
     - calling `setup_logging()` twice doesn't add duplicate handlers
   - `test_drive_search.py`: query building and escaping, date parsing and validation, path resolution, and Markdown/HTML rendering.
   - A test using pytest's `caplog` that runs the auth flow with a fake token and confirms the token value never appears in the logs.
8. `.gitignore` excluding `credentials.json`, `token.json`, `search_results/` and `logs/`.

## Acceptance criteria
- `python drive_search.py --name "budget" --created-after 2025-01-01 --created-before 2025-12-31` prints the report and saves one `.md` and one `.html` file to `search_results/`.
- Every file in the HTML report has a working link to that file in Google Drive.
- A file named `Q1 | <Draft> & Notes.docx` displays correctly in all three outputs.
- A search returning more than 1,000 files returns all of them.
- `pytest` passes with no network access.
- Deleting `token.json` and running again opens the browser sign-in. A second run after that doesn't.
- `python drive_search.py --version` prints e.g. `drive_search 1.0.0 (2026-11-11)`.
- Every `.py` file has the standard header, and its `Version` matches its `__version__`.
- No module other than `auth.py` imports `google.oauth2`, `google_auth_oauthlib` or `google.auth`.
- With no `logs` folder present, the first run creates it next to the script and logs `Log folder created: <full path>`. This works even when the tool is run from a different folder.
- If the log folder is made read-only, the next run still completes and writes its log to the backup folder.
- After any run, `drive_search.log` has a start line and a finish line for that run with the same run ID, including the exit code and duration.
- A normal run with default settings shows only the report and the "saved to" lines in the terminal.
- A forced API failure is logged with its full traceback in the log file, while the terminal shows a one-line message.
- No module other than `log_setup.py` creates logging handlers or calls `logging.basicConfig()`.
- No log line ever contains a token or client secret.

## Out of scope
- Searching file contents, and downloading, moving, or modifying files.
- Scheduled or background runs. (This can be added later with Windows Task Scheduler.)
