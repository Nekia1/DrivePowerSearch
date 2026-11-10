# Drive Search

| | |
|---|---|
| **Version** | 0.1.0 |
| **Created** | 2026-11-10 |
| **Spec** | [`docs/SPEC.md`](docs/SPEC.md) v1.3.1 (original idea: [`docs/rough_prompt.md`](docs/rough_prompt.md)) |

A command-line tool that searches your Google Drive by file name and creation date. It prints a report in the terminal and saves the same report as Markdown and HTML in `search_results/`. In the HTML report, each file path is a link that opens the file in Drive.

It asks only for **read-only access to file details** (names, dates, folders). It can't open, change or delete your files.

---

## 1. One-time setup

### 1.1 Conda environment
In **Anaconda Prompt**:
```
cd "C:\Users\{user_account}\Documents\00_PythonWIP\drive_search"
conda env create -f setup\environment.yml      # skip if "powertools" already exists
conda activate powertools
```

### 1.2 Google Cloud setup (creates `credentials.json`)
You only do this once. It takes about 10 minutes in a browser.

1. Go to <https://console.cloud.google.com/> and sign in with the Google account whose Drive you want to search.
2. **Create a project:** click the project picker at the top, choose **New project**, name it something like `Drive Search`, and click **Create**. Make sure it's selected.
3. **Turn on the Drive API:** go to **APIs & Services → Library**, search for **Google Drive API**, and click **Enable**.
4. **Set up the consent screen:** go to **Google Auth Platform** (or **APIs & Services → OAuth consent screen**) and click **Get started**.
   - App name: `Drive Search`. Support email: your email.
   - Audience: **External** (choose **Internal** if you're on a Google Workspace account and only you will use it).
   - Contact email: your email. Agree to the policy, then click **Create**.
   - Under **Audience → Test users**, click **Add users** and add **your own email**.
5. **Create the OAuth client:** go to **Clients → Create client**, choose application type **Desktop app**, name it `Drive Search CLI`, and click **Create**.
6. Click **Download JSON**, rename the file to **`credentials.json`**, and put it in this folder:
   `C:\Users\{user_account}\Documents\00_PythonWIP\drive_search\credentials.json`

`credentials.json` and `token.json` are listed in `.gitignore`. **Never commit or share them.**

### 1.3 First sign-in
The first search opens your browser:
- Choose your account.
- Google will say **"Google hasn't verified this app"**. That's expected for a personal app in testing mode. Click **Continue**.
- Allow read-only access.

The tool saves the sign-in as `token.json`, so later runs don't open the browser.

> **Testing-mode note:** while the app's publishing status is "Testing", Google expires the saved sign-in after **7 days**. When that happens, the tool simply opens the browser again. To avoid this, you can publish the app ("In production"). For a personal app with only the read-only metadata permission, that doesn't need Google's review, though you'll still see the "unverified app" screen.

---

## 2. Usage
```
conda activate powertools
cd "C:\Users\{user_account}\Documents\00_PythonWIP\drive_search"
python -m drive_search --name budget
```

**Examples**
```
# Names containing "budget", created in 2026
python -m drive_search --name budget --created-after 2026-01-01 --created-before 2026-12-31

# Exact name, created on one day
python -m drive_search --name "Q3 Report.docx" --exact --created-on 2026-10-02

# Include shared drives and show progress messages
python -m drive_search --name invoice --include-shared-drives --verbose
```

**Options**
| Option | Meaning |
|---|---|
| `--name TEXT` | **Required.** Text to match in file names |
| `--exact` | Match the whole name exactly (case-sensitive). Default: name contains TEXT (case-insensitive) |
| `--created-on YYYY-MM-DD` | Only files created on this local date |
| `--created-after` / `--created-before YYYY-MM-DD` | Inclusive date range. Can't be combined with `--created-on` |
| `--include-shared-drives` | Also search shared drives |
| `--output-dir PATH` | Report folder. Default: `./search_results` (relative to where you run the command) |
| `--log-level LEVEL` | `DEBUG`, `INFO` (default), `WARNING` or `ERROR` |
| `--log-dir PATH` | Log folder. Default: `logs/` in this project folder |
| `--verbose` | Show progress (INFO) messages in the terminal |
| `--version` / `--help` | |

**Exit codes:** 0 success · 1 unexpected error · 2 invalid arguments · 3 sign-in problem · 4 Google Drive error · 5 reports couldn't be saved · 130 cancelled (Ctrl+C)

---

## 3. Output
- **Terminal:** the report tables.
- **`search_results/drive_search_<YYYYMMDD_HHMMSS>.md` and `.html`:** a new pair on every run, so earlier reports are never overwritten.
- Each report contains the search terms (including defaults), the run date and time with your UTC offset, the number of files found, and a table with file name, created, modified and full path.

**About "full path":** Google Drive has no real paths, so the tool rebuilds one from each file's folders, for example `My Drive/Projects/2026/report.pdf`. Files shared with you, whose folders you can't see, show as `(shared with me)/...`. A file with several parent folders shows the first one.

## 4. Logs
`logs/drive_search.log` (created automatically on first run). It records each run's start and end, sign-in steps, each page of results, and the reports written. Every line in a run shares the same `run=xxxxxxxx` ID.
- At the default `INFO` level, the log records **counts, not file names**. Use `--log-level DEBUG` to include names.
- Tokens and secrets are never logged.
- If `logs/` can't be written to, logs go to `%LOCALAPPDATA%\DriveSearch\logs`. If that fails too, they go to the terminal only.

## 5. Tests
```
conda activate powertools
python -m pytest
```
The tests use a fake Drive and make no network calls.

## 6. Known limitations
- **"Contains" means word-prefix matching.** Google's `name contains` matches the start of words: `--name budg` finds "Budget 2026.xlsx", but `--name get` does not. Searching for a whole word works as you'd expect.
- Dates use your computer's time zone.

## 7. Project layout
| File | Responsibility |
|---|---|
| `drive_search/auth.py` | Sign-in, tokens, permissions, Drive client |
| `drive_search/logging_setup.py` | Log folder, handlers, format, run ID |
| `drive_search/cli.py` | Options, input checks, error messages, exit codes |
| `drive_search/search.py` | Drive query, paging, retries |
| `drive_search/paths.py` | Rebuilding full paths (cached) |
| `drive_search/reports.py` | Terminal, Markdown and HTML reports |
| `tests/` | pytest suite with a fake Drive (`tests/fakes.py`) |
| `docs/SPEC.md` | The spec this code implements, and `docs/rough_prompt.md`, the original idea |
| `setup/environment.yml` | Conda environment `powertools`, plus `requirements.txt` for pip users |
