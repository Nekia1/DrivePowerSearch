# Drive Search

| | |
|---|---|
| **Version** | 1.0.0 (released 2026-11-11, see [`CHANGELOG.md`](CHANGELOG.md)) |
| **Created** | 2026-11-10 |
| **Spec** | [`docs/SPEC.md`](docs/SPEC.md) v1.5.0 (original idea: [`docs/rough_prompt.md`](docs/rough_prompt.md)) |

A command-line tool that searches your Google Drive by file name and creation date. It prints a report in the terminal and saves the same report as Markdown and HTML in `search_results/`. In the HTML report, each file path is a link that opens the file in Drive.

It asks only for **read-only access to file details** (names, dates, folders). It can't open, change or delete your files.

---

## 1. One-time setup

***You MUST to replace {user_account} with your own Windows local user account folder name for these commands below to work correctly.***

### 1.1 Conda environment
In **Anaconda Prompt**:
```
cd "C:\Users\{user_account}\Documents\00_PythonWIP\DrivePowerSearch"
conda env create -f setup\environment.yml      # skip if "powertools" already exists
conda activate powertools
```

### 1.2 Google Cloud setup (creates `credentials.json`)
You only do this once. It takes about 15 minutes in a browser, and it's free.

**Follow the step-by-step guide: [docs/google_cloud_setup.md](docs/google_cloud_setup.md).** It covers every screen, a checklist to confirm it worked, troubleshooting for common errors, and security tips.

In short: create a Google Cloud project, turn on the Google Drive API, set up the OAuth consent screen (External, Testing) and add yourself as a test user, then create a **Desktop app** OAuth client. Download its JSON as **`credentials.json`** into this folder:
`C:\Users\{user_account}\Documents\00_PythonWIP\DrivePowerSearch\credentials.json`

`credentials.json` and `token.json` are listed in `.gitignore`. **Never commit or share them.**

### 1.3 First sign-in
The first search opens your browser:
- Choose your account.
- Google will say **"Google hasn't verified this app"**. That's expected for a personal app in testing mode. Click **Continue**.
- Allow read-only access.

The tool saves the sign-in as `token.json`, so later runs don't open the browser.

**To reset the sign-in** (for example, to switch Google accounts), delete `token.json` and run the tool again. The browser sign-in opens once more.

> **Testing-mode note:** while the app's publishing status is "Testing", Google expires the saved sign-in after **7 days**. When that happens, the tool simply opens the browser again. You can avoid this by publishing the app, but the permission the tool uses is one Google classes as "restricted", so read the guide's "Testing vs In production" section first.

---

## 2. Usage
```
conda activate powertools
cd "C:\Users\{user_account}\Documents\00_PythonWIP\DrivePowerSearch"
python -m drive_search --name budget
```

**Interactive mode:** run `python -m drive_search` with no options, and the tool asks for the name and the optional dates. Leave a date blank to skip it. An invalid date is asked again. Ctrl+C cancels.

**Examples**
```
# Names containing "budget", created in 2026
python -m drive_search --name budget --created-after 2026-01-01 --created-before 2026-12-31

# Exact name, created on one day
python -m drive_search --name "Q3 Report.docx" --exact --created-on 2026-10-02

# Include shared drives and show progress messages
python -m drive_search --name invoice --include-shared-drives --verbose

# Include folders and trashed files
python -m drive_search --name "Old Projects" --include-folders --include-trashed

# Keep the Google sign-in files outside the project folder
python -m drive_search --name budget --credentials D:\secrets\credentials.json --token D:\secrets\token.json
```

**Options**
| Option | Meaning |
|---|---|
| `--name TEXT` | **Required.** Text to match in file names |
| `--exact` | Match the whole name exactly (case-sensitive). Default: name contains TEXT (case-insensitive) |
| `--created-on YYYY-MM-DD` | Only files created on this local date |
| `--created-after` / `--created-before YYYY-MM-DD` | Inclusive date range. Can't be combined with `--created-on` |
| `--include-shared-drives` | Also search shared drives |
| `--include-trashed` | Include files in the trash. Default: excluded |
| `--include-folders` | Include folders. Default: files only |
| `--credentials PATH` | OAuth client file. Default: the `GDRIVE_CREDENTIALS` environment variable, then `credentials.json` in this folder |
| `--token PATH` | Saved sign-in file. Default: the `GDRIVE_TOKEN` environment variable, then `token.json` in this folder |
| `--output-dir PATH` | Report folder. Default: `./search_results` (relative to where you run the command) |
| `--log-level LEVEL` | `DEBUG`, `INFO` (default), `WARNING` or `ERROR` |
| `--log-dir PATH` | Log folder. Default: `logs/` in this project folder |
| `--verbose` | Show progress (INFO) messages in the terminal |
| `--version` | Print the version and release date, for example `drive_search 1.0.0 (2026-11-11)` |
| `--help` | List every option |

**Exit codes:** 0 success · 1 unexpected error · 2 invalid arguments · 3 sign-in problem · 4 Google Drive error · 5 reports couldn't be saved · 130 cancelled (Ctrl+C)

---

## 3. Output
- **Terminal:** the report tables.
- **`search_results/drive_search_<YYYYMMDD_HHMMSS>.md` and `.html`:** a new pair on every run, so earlier reports are never overwritten.
- Each report contains the search terms (including defaults), the run date and time with your UTC offset and time zone (for example `2026-11-10T14:32:05-05:00 (EST)`), the tool version and run ID, the number of files found, and a table with row number, file name, created, modified and full path.

**About "full path":** Google Drive has no real paths, so the tool rebuilds one from each file's folders, for example `My Drive/Projects/2026/report.pdf`. Files shared with you, whose folders you can't see, show as `(shared with me)/...`. A file with several parent folders shows the first one.

## 4. Logs
`logs/drive_search.log` (created automatically on first run). It records each run's start and end, sign-in steps, each page of results, and the reports written. Every line in a run shares the same `run=xxxxxxxx` ID, and each report shows that ID, so you can find a report's log lines.
- At the default `INFO` level, the log records **counts, not file names**. Use `--log-level DEBUG` to include names.
- Tokens and secrets are never logged.
- If `logs/` can't be written to, logs go to `%LOCALAPPDATA%\DriveSearch\logs`. If that fails too, they go to the terminal only.

## 5. Versioning and file headers
- The tool's version is in `drive_search/__init__.py` (`__version__` and `__release_date__`), and every release is listed in [`CHANGELOG.md`](CHANGELOG.md). Versions follow [Semantic Versioning](https://semver.org/): major for breaking changes, minor for new features, patch for fixes.
- Every `.py` file starts with a standard header, and has a matching `__version__`:
  ```python
  """
  Module:        drive_search/auth.py
  Description:   Google sign-in, token caching, OAuth scopes and Drive API client creation.
  Version:       1.0.0
  Created:       2026-11-10
  Last updated:  2026-11-11T15:20:00-05:00
  """
  ```
- When you change a file, bump its `Version` and `__version__` and update `Last updated`. `tests/test_project_rules.py` fails if a header is missing or doesn't match.

## 6. Tests
```
conda activate powertools
python -m pytest
```
The tests use a fake Drive and make no network calls.

## 7. Known limitations
- **"Contains" means word-prefix matching.** Google's `name contains` matches the start of words: `--name budg` finds "Budget 2026.xlsx", but `--name get` does not. Searching for a whole word works as you'd expect.
- Dates use your computer's time zone.

## 8. Project layout
| File | Responsibility |
|---|---|
| `drive_search/__init__.py` | Tool version and release date |
| `drive_search/auth.py` | Sign-in, tokens, permissions, Drive client |
| `drive_search/logging_setup.py` | Log folder, handlers, format, run ID |
| `drive_search/cli.py` | Options, input checks, error messages, exit codes |
| `drive_search/search.py` | Drive query, paging, retries |
| `drive_search/paths.py` | Rebuilding full paths (cached) |
| `drive_search/reports.py` | Terminal, Markdown and HTML reports |
| `tests/` | pytest suite with a fake Drive (`tests/fakes.py`). `test_project_rules.py` enforces the file-header and module-boundary rules |
| `docs/SPEC.md` | The spec this code implements, and `docs/rough_prompt.md`, the original idea |
| `docs/google_cloud_setup.md` | Step-by-step Google Cloud setup and troubleshooting |
| `docs/archive/` | Superseded documents kept for history, such as the earlier standalone build's prompt |
| `CHANGELOG.md` | Every release and what changed |
| `setup/environment.yml` | Conda environment `powertools`, plus `requirements.txt` for pip users |
