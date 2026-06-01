from __future__ import annotations

import time

from playwright.sync_api import expect

from .base_page import BasePage


class LoginPage(BasePage):
    PAGE_KEY = "signin_modal"

    def login(self, email: str, password: str) -> None:
        for attempt in range(2):
            self._fill_credentials(email, password)
            submit = self._wait_for_enabled_submit()
            self._submit_and_wait(submit)
            if self._appears_logged_in():
                return
            # If the modal is still showing, the form rejected our submit
            # (race / stale CSRF). Re-open it before retrying.
            if attempt == 0:
                self._reopen_login_modal()
        # Last effort: just leave; expect_logged_in will raise with diagnostics.

    def _fill_credentials(self, email: str, password: str) -> None:
        email_loc = self.first_visible(self.selectors(self.PAGE_KEY, "email_input"))
        email_loc.click()
        email_loc.fill("")
        email_loc.type(email, delay=20)
        try:
            email_loc.dispatch_event("change")
        except Exception:
            pass

        password_loc = self.first_visible(self.selectors(self.PAGE_KEY, "password_input"))
        password_loc.click()
        password_loc.fill("")
        password_loc.type(password, delay=20)
        try:
            password_loc.dispatch_event("change")
        except Exception:
            pass

        try:
            password_loc.press("Tab")
        except Exception:
            pass

    def _wait_for_enabled_submit(self, timeout: int = 8000):
        deadline = time.time() + timeout / 1000
        last_locator = None
        while time.time() < deadline:
            for selector in self.selectors(self.PAGE_KEY, "submit_button"):
                loc = self.page.locator(selector).first
                last_locator = loc
                try:
                    if loc.count() == 0:
                        continue
                    if loc.is_visible() and loc.is_enabled():
                        return loc
                except Exception:
                    continue
            self.page.wait_for_timeout(150)
        if last_locator is not None:
            return last_locator
        raise AssertionError("Login submit button never became visible")

    def _submit_and_wait(self, submit) -> None:
        try:
            with self.page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                try:
                    submit.click(timeout=8000)
                except Exception:
                    submit.click(timeout=4000, force=True)
        except Exception:
            # No navigation event (Ajax submit). Fall back to manual waits.
            try:
                submit.click(timeout=4000, force=True)
            except Exception:
                pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    def _appears_logged_in(self) -> bool:
        for sel in [
            "a.user-logout",
            ".user-firstname",
            "a#myaccount",
            "a:has-text('My Account')",
        ]:
            try:
                if self.page.locator(sel).count() > 0:
                    return True
            except Exception:
                continue
        try:
            return self.page.locator("a.signModal").count() == 0
        except Exception:
            return False

    def _reopen_login_modal(self) -> None:
        # If the modal closed (form posted but server returned an error page),
        # reopen by clicking the sign-in link.
        for sel in [
            "a.signModal[aria-label='Login to your account']",
            "header a.signModal",
            "a.signModal",
        ]:
            try:
                link = self.page.locator(sel).first
                if link.count() == 0:
                    continue
                try:
                    link.click(timeout=3000)
                except Exception:
                    link.click(timeout=3000, force=True)
                break
            except Exception:
                continue
        try:
            self.page.wait_for_selector("form#loginForm", state="visible", timeout=8000)
        except Exception:
            pass
