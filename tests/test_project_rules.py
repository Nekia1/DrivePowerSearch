"""Project-wide architecture rules (CLAUDE.md, spec acceptance criteria).

Ported from the earlier standalone build (VS_Code_Lessons/drive_search 1.0.0),
so the rules are checked on every test run instead of by hand.
"""

import re
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent.parent / "drive_search"
MODULES = sorted(PACKAGE.glob("*.py"))

AUTH_ONLY = re.compile(
    r"^\s*(from|import)\s+(google\.oauth2|google\.auth|google_auth_oauthlib)\b"
    r"|credentials\.json|token\.json|googleapis\.com/auth/",
    re.M,
)
LOGGING_ONLY = re.compile(r"\bbasicConfig\b|\baddHandler\b|\b\w*Handler\(")
BARE_PRINT = re.compile(r"(?<![\w.])print\(")  # rich's console.print(...) is allowed


def test_package_modules_found():
    assert {"auth.py", "logging_setup.py", "cli.py"} <= {p.name for p in MODULES}


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
