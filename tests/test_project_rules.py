"""
Module:        tests/test_project_rules.py
Description:   Project-wide rules: file headers and module boundaries.
Version:       1.0.0
Created:       2026-11-11
Last updated:  2026-11-11T15:20:00-05:00

Project-wide architecture rules (CLAUDE.md, spec acceptance criteria).

Ported from the earlier standalone build (VS_Code_Lessons/drive_search 1.0.0),
so the rules are checked on every test run instead of by hand.
"""

import re
from pathlib import Path

import pytest

__version__ = "1.0.0"

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "drive_search"
MODULES = sorted(PACKAGE.glob("*.py"))
ALL_PY_FILES = sorted([*MODULES, *(ROOT / "tests").glob("*.py")])

# Spec "Source file headers and versioning".
HEADER = re.compile(
    r'^"""\n'
    r"Module:        (?P<module>\S+)\n"
    r"Description:   \S.*\n"
    r"Version:       (?P<version>\d+\.\d+\.\d+)\n"
    r"Created:       \d{4}-\d{2}-\d{2}\n"
    r"Last updated:  \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\n"
)

AUTH_ONLY = re.compile(
    r"^\s*(from|import)\s+(google\.oauth2|google\.auth|google_auth_oauthlib)\b"
    r"|credentials\.json|token\.json|googleapis\.com/auth/",
    re.M,
)
LOGGING_ONLY = re.compile(r"\bbasicConfig\b|\baddHandler\b|\b\w*Handler\(")
BARE_PRINT = re.compile(r"(?<![\w.])print\(")  # rich's console.print(...) is allowed


def test_package_modules_found():
    assert {"auth.py", "logging_setup.py", "cli.py"} <= {p.name for p in MODULES}


@pytest.mark.parametrize("path", ALL_PY_FILES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_standard_header_matches_version(path):
    text = path.read_text(encoding="utf-8")
    header = HEADER.match(text)
    assert header, f"{path.name} is missing the standard header (see docs/SPEC.md)"
    assert header["module"] == path.relative_to(ROOT).as_posix()
    declared = re.search(r'^__version__ = "([^"]+)"', text, re.M)
    assert declared, f"{path.name} has no __version__"
    assert declared.group(1) == header["version"], f"{path.name}: header and __version__ differ"


@pytest.mark.parametrize("path", [p for p in MODULES if p.name != "auth.py"], ids=lambda p: p.name)
def test_only_auth_touches_credentials_tokens_and_scopes(path):
    match = AUTH_ONLY.search(path.read_text(encoding="utf-8"))
    assert match is None, f"{path.name} contains {match.group(0)!r}; only auth.py may"


@pytest.mark.parametrize("path", [p for p in MODULES if p.name != "logging_setup.py"], ids=lambda p: p.name)
def test_only_logging_setup_configures_handlers(path):
    match = LOGGING_ONLY.search(path.read_text(encoding="utf-8"))
    assert match is None, f"{path.name} contains {match.group(0)!r}; only logging_setup.py may"


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_no_bare_print(path):
    assert BARE_PRINT.search(path.read_text(encoding="utf-8")) is None, f"{path.name} uses print(); use rich or logging"
