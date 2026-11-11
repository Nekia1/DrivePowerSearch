"""
Module:        tests/test_cli.py
Description:   End-to-end tests for the command-line interface.
Version:       1.0.0
Created:       2026-11-10
Last updated:  2026-11-11T15:20:00-05:00
"""

import argparse
import re

import pytest

from drive_search import cli
from drive_search.auth import CredentialsNotFoundError
from drive_search.logging_setup import LOG_FILE_NAME
from fakes import FakeService, drive_file, make_http_error

__version__ = "1.0.0"

FOLDERS = {"f1": {"id": "f1", "name": "Projects", "parents": ["root-id"]}}


@pytest.fixture
def dirs(tmp_path):
    return tmp_path / "out", tmp_path / "logs"


def run(dirs, *extra):
    out, logs = dirs
    return cli.main(["--name", "report", "--output-dir", str(out), "--log-dir", str(logs), *extra])


def fake_drive(monkeypatch, pages=None):
    service = FakeService(pages=pages or [{"files": [drive_file("x1", "report.pdf", parents=["f1"])]}], folders=FOLDERS)
    service.auth_calls = []

    def fake_credentials(*args):
        service.auth_calls.append(args)
        return object()

    monkeypatch.setattr(cli.auth, "get_credentials", fake_credentials)
    monkeypatch.setattr(cli.auth, "build_drive_service", lambda creds: service)
    return service


def log_text(dirs):
    return (dirs[1] / LOG_FILE_NAME).read_text(encoding="utf-8")


def test_parse_date_rejects_bad_input():
    with pytest.raises(argparse.ArgumentTypeError, match="YYYY-MM-DD"):
        cli.parse_date("10/11/2026")


@pytest.mark.parametrize(
    "args, message",
    [
        (["--created-on", "2026-01-01", "--created-after", "2025-01-01"], "can't be combined"),
        (["--created-after", "2026-02-01", "--created-before", "2026-01-01"], "is later than"),
        (["--created-on", "2026-13-01"], "not a valid date"),
    ],
)
def test_invalid_arguments_exit_2(dirs, capsys, args, message):
    assert run(dirs, *args) == cli.EXIT_USAGE
    assert message in capsys.readouterr().err


def test_missing_name_exits_2(tmp_path, capsys):
    assert cli.main(["--log-dir", str(tmp_path)]) == cli.EXIT_USAGE
    assert "--name" in capsys.readouterr().err


def test_successful_search_end_to_end(dirs, monkeypatch, capsys):
    fake_drive(monkeypatch)
    assert run(dirs) == cli.EXIT_OK

    out = capsys.readouterr().out
    assert "report.pdf" in out and "Markdown report:" in out and "HTML report:" in out
    md_files, html_files = list(dirs[0].glob("*.md")), list(dirs[0].glob("*.html"))
    assert len(md_files) == 1 and len(html_files) == 1
    md = md_files[0].read_text(encoding="utf-8")
    assert "My Drive/Projects/report.pdf" in md
    assert "**Files found:** 1" in md
    assert 'href="https://drive.google.com/file/d/x1/view"' in html_files[0].read_text(encoding="utf-8")

    log = log_text(dirs)
    run_ids = set(re.findall(r"run=([0-9a-f]{8})", log))
    assert len(run_ids) == 1
    assert "starting" in log and "Finished with exit code 0" in log
    assert "Total matches: 1" in log and "Wrote HTML report" in log
    assert "report.pdf" not in log  # file names only at DEBUG


def test_debug_level_logs_file_names(dirs, monkeypatch):
    fake_drive(monkeypatch)
    assert run(dirs, "--log-level", "debug") == cli.EXIT_OK
    assert "report.pdf" in log_text(dirs)


def test_no_results(dirs, monkeypatch, capsys):
    fake_drive(monkeypatch, pages=[{"files": []}])
    assert run(dirs) == cli.EXIT_OK
    assert "No files found" in capsys.readouterr().out


def test_two_runs_make_two_report_pairs(dirs, monkeypatch):
    fake_drive(monkeypatch, pages=[{"files": []}])
    run(dirs)
    fake_drive(monkeypatch, pages=[{"files": []}])
    run(dirs)
    assert len(list(dirs[0].glob("*.md"))) == 2
    assert len(list(dirs[0].glob("*.html"))) == 2


def test_missing_credentials_is_friendly(dirs, monkeypatch, capsys):
    def missing(*args):
        raise CredentialsNotFoundError("OAuth client file not found: C:\\x\\credentials.json.")

    monkeypatch.setattr(cli.auth, "get_credentials", missing)
    assert run(dirs) == cli.EXIT_AUTH
    err = capsys.readouterr().err
    assert "credentials.json" in err and LOG_FILE_NAME in err
    assert "Traceback" not in err
    assert "Traceback" in log_text(dirs)


def test_drive_error_exit_4(dirs, monkeypatch, capsys):
    fake_drive(monkeypatch, pages=[[make_http_error(400, "badRequest")]])
    assert run(dirs) == cli.EXIT_DRIVE
    assert "HTTP 400" in capsys.readouterr().err


def test_unwritable_output_exit_5(tmp_path, monkeypatch, capsys):
    fake_drive(monkeypatch)
    blocker = tmp_path / "file_not_folder"
    blocker.write_text("x")
    assert run((blocker, tmp_path / "logs")) == cli.EXIT_OUTPUT
    assert "Could not write reports" in capsys.readouterr().err


def test_version_flag(tmp_path, capsys):
    from drive_search import __version__

    assert cli.main(["--version", "--log-dir", str(tmp_path)]) == 0
    assert __version__ in capsys.readouterr().out


def test_report_run_id_matches_the_log(dirs, monkeypatch):
    fake_drive(monkeypatch)
    assert run(dirs) == cli.EXIT_OK
    (log_run_id,) = set(re.findall(r"run=([0-9a-f]{8})", log_text(dirs)))
    md = next(dirs[0].glob("*.md")).read_text(encoding="utf-8")
    assert f"run {log_run_id}" in md


def test_version_format(tmp_path, capsys):
    from drive_search import __release_date__, __version__

    assert cli.main(["--version", "--log-dir", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == f"drive_search {__version__} ({__release_date__})"


def test_credential_paths_are_passed_to_auth(dirs, monkeypatch, tmp_path):
    service = fake_drive(monkeypatch)
    secrets, token = str(tmp_path / "c.json"), str(tmp_path / "t.json")
    assert run(dirs, "--credentials", secrets, "--token", token) == cli.EXIT_OK
    assert service.auth_calls == [(secrets, token)]


def test_trashed_and_folder_options_reach_query_and_report(dirs, monkeypatch):
    service = fake_drive(monkeypatch)
    assert run(dirs, "--include-trashed", "--include-folders") == cli.EXIT_OK
    query = service.files_api.list_calls[0]["q"]
    assert "trashed" not in query and "mimeType" not in query
    md = next(dirs[0].glob("*.md")).read_text(encoding="utf-8")
    assert "| Include trashed files | yes |" in md and "| Include folders | yes |" in md


def test_defaults_exclude_trashed_and_folders(dirs, monkeypatch):
    service = fake_drive(monkeypatch)
    run(dirs)
    query = service.files_api.list_calls[0]["q"]
    assert "trashed = false" in query and "mimeType != 'application/vnd.google-apps.folder'" in query


class TestInteractive:
    def test_prompt_reasks_blank_name_and_invalid_date(self):
        answers = iter(["", "budget", "2025-13-01", "2025-01-01", ""])
        told = []
        argv = cli.prompt_for_terms(lambda label: next(answers), told.append)
        assert argv == ["--name", "budget", "--created-after", "2025-01-01"]
        assert len(told) == 1 and "YYYY-MM-DD" in told[0]

    def _run_interactive(self, tmp_path, monkeypatch, stdin_text):
        import io

        from rich.console import Console

        from drive_search.logging_setup import setup_logging

        monkeypatch.chdir(tmp_path)  # default ./search_results lands in tmp_path
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        info = setup_logging(log_dir=tmp_path / "logs")
        return cli._run([], info, Console(file=io.StringIO(), width=200))

    def test_no_arguments_runs_interactively(self, tmp_path, monkeypatch):
        service = fake_drive(monkeypatch)
        assert self._run_interactive(tmp_path, monkeypatch, "report\n\n\n") == cli.EXIT_OK
        assert "name contains 'report'" in service.files_api.list_calls[0]["q"]
        assert len(list((tmp_path / "search_results").glob("*.md"))) == 1

    def test_end_of_input_cancels(self, tmp_path, monkeypatch):
        fake_drive(monkeypatch)
        assert self._run_interactive(tmp_path, monkeypatch, "") == cli.EXIT_INTERRUPTED
