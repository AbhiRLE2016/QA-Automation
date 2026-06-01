from __future__ import annotations

import pytest
from playwright.sync_api import BrowserContext, Page

# Importing the step_defs module registers all pytest-bdd step handlers and
# generates the scenario test functions.
from step_defs.story_1_manager_pli_end_to_end_steps import *  # noqa: F401,F403


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
def _ensure_clean_state(
    page: Page, context: BrowserContext, dialog_recorder: DialogRecorder
):
    """Setup: if Priya Sharma 7777 was left in the dashboard by a prior run,
    delete her so the scenario starts fresh. Clears storage so the scenario's
    Given step lands on the login page."""
    try:
        page.goto(
            "http://localhost:5173/", wait_until="domcontentloaded", timeout=15000
        )
        try:
            page.wait_for_selector("#manager-id", state="visible", timeout=3000)
            page.locator("#manager-id").fill("499")
            page.locator("#password").fill("Mngr@101Pass!")
            page.locator("button:has-text('Login')").click()
        except Exception:
            pass
        try:
            page.wait_for_url("**/dashboard/**", timeout=8000)
        except Exception:
            pass
        del_btn = page.locator('button[aria-label="Delete employee 7777"]')
        try:
            del_btn.wait_for(state="visible", timeout=2500)
            del_btn.click()
            confirm = page.get_by_role("button", name="Delete", exact=True)
            confirm.wait_for(state="visible", timeout=3000)
            confirm.click()
            page.wait_for_timeout(800)
        except Exception:
            pass
    except Exception:
        pass
    try:
        page.evaluate(
            "() => { try{localStorage.clear(); sessionStorage.clear();}catch(e){} }"
        )
    except Exception:
        pass
    try:
        context.clear_cookies()
    except Exception:
        pass
    yield
