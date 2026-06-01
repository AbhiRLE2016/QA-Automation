from __future__ import annotations

import pytest
from playwright.sync_api import BrowserContext, Page

# Importing the step_defs modules registers all pytest-bdd step handlers for
# every feature in this workspace. Prior story's step defs stay imported so
# the existing fixtures (walk_state etc.) and any reused step phrases remain
# available; the new delete-employee story brings its own set on top.
from step_defs.story_1_all_employees_directory_walk_steps import *  # noqa: F401,F403
from step_defs.story_1_delete_employee_steps import *  # noqa: F401,F403
from step_defs.story_1_verify_all_employees_against_csv_steps import *  # noqa: F401,F403


class DialogRecorder:
    """Auto-accepts every JS alert/confirm/prompt and records the message text
    so step defs can assert on it."""

    def __init__(self) -> None:
        self.last: str | None = None
        self.messages: list[str] = []

    def __call__(self, dialog) -> None:
        try:
            self.last = dialog.message
            self.messages.append(dialog.message)
        except Exception:
            pass
        try:
            dialog.accept()
        except Exception:
            pass


@pytest.fixture()
def dialog_recorder(page: Page) -> DialogRecorder:
    rec = DialogRecorder()
    page.on("dialog", rec)
    return rec


@pytest.fixture(autouse=True)
def _ensure_clean_state(page: Page, context: BrowserContext, dialog_recorder: DialogRecorder):
    """Each scenario starts from a logged-out, cookie-clean context so the
    'Given the user is a manager' step always lands on the login page."""
    try:
        page.context.clear_cookies()
    except Exception:
        pass
    try:
        page.goto("about:blank", wait_until="domcontentloaded", timeout=5000)
        page.evaluate(
            "() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }"
        )
    except Exception:
        pass
    yield
