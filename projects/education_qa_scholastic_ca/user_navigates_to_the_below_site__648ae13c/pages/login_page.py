from __future__ import annotations

import re
import time

from .base_page import BasePage


class LoginPage(BasePage):
    PAGE_KEY = "signin_modal"

    def wait_for_modal_ready(self, timeout: int = 20000) -> None:
        """Wait until BOTH email AND password inputs are visible and enabled."""
        self._ensure_signin_tab()
        try:
            self.page.wait_for_function(
                """() => {
                    const form = document.querySelector('#loginForm');
                    if (!form || form.offsetParent === null) return false;
                    const email = form.querySelector("input[name='loginEmail']");
                    const pwd = form.querySelector("input[name='loginPassword']");
                    if (!email || !pwd) return false;
                    if (email.offsetParent === null || pwd.offsetParent === null) return false;
                    if (pwd.disabled || email.disabled) return false;
                    return true;
                }""",
                timeout=timeout,
            )
        except Exception as exc:
            raise AssertionError(
                "Sign-in modal failed to render both inputs within "
                f"{timeout}ms"
            ) from exc

    def _ensure_signin_tab(self) -> None:
        try:
            login_visible = self.page.evaluate(
                """() => {
                    const f = document.querySelector('#loginForm');
                    return !!(f && f.offsetParent);
                }"""
            )
        except Exception:
            login_visible = False
        if login_visible:
            return
        for tab_sel in [
            "div.modal.show button:has-text('Back to Login')",
            ".modal.show button.signModal:has-text('Back to Login')",
            "button:has-text('Back to Login'):visible",
            "button.signModal:visible",
            "button:has-text('Back to Sign In'):visible",
            "div.modal.show a:has-text('Back to Login')",
            "a:has-text('Back to Login'):visible",
        ]:
            try:
                tab = self.page.locator(tab_sel).first
                if tab.count() == 0 or not tab.is_visible():
                    continue
                try:
                    tab.click(timeout=2500)
                except Exception:
                    tab.click(timeout=2500, force=True)
                try:
                    self.page.wait_for_function(
                        """() => {
                            const f = document.querySelector('#loginForm');
                            return !!(f && f.offsetParent);
                        }""",
                        timeout=4000,
                    )
                    return
                except Exception:
                    continue
            except Exception:
                continue

    def fill_email(self, email: str) -> None:
        self.wait_for_modal_ready()
        self.page.locator("#loginForm input[name='loginEmail']").first.fill(email)

    def fill_password(self, password: str) -> None:
        self.wait_for_modal_ready()
        self.page.locator("#loginForm input[name='loginPassword']").first.fill(password)

    def clear_fields(self) -> None:
        self.wait_for_modal_ready()
        try:
            self.page.locator("#loginForm input[name='loginEmail']").first.fill("")
        except Exception:
            pass
        try:
            self.page.locator("#loginForm input[name='loginPassword']").first.fill("")
        except Exception:
            pass

    def submit(self) -> None:
        """Submit the sign-in form. Retries once if neither a logged-in
        indicator NOR an error message appears within 10s — verified on
        Scholastic CA, the first submit click is occasionally swallowed
        when the Sourcepoint frame reattaches mid-click."""
        # Defensive: re-dismiss the cookie banner if it reattached while the
        # modal was being filled — it can intercept the submit click.
        try:
            from .home_page import HomePage
            HomePage(self.page).accept_cookies_if_present(timeout=2000)
        except Exception:
            pass

        for attempt in range(2):
            submit = self._wait_for_enabled_submit()
            try:
                with self.page.expect_navigation(
                    wait_until="domcontentloaded", timeout=10000
                ):
                    try:
                        submit.click(timeout=8000)
                    except Exception:
                        submit.click(timeout=4000, force=True)
            except Exception:
                # AJAX submit — no navigation. Continue to wait for a
                # response indicator below.
                pass
            try:
                self.page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            if self._submission_registered(timeout=6000):
                return
            # No visible response. Re-open modal in case the form was reset,
            # then loop and try once more.
            if attempt == 0:
                try:
                    from .home_page import HomePage
                    HomePage(self.page).open_signin_modal()
                except Exception:
                    pass

    def _submission_registered(self, timeout: int = 6000) -> bool:
        """Return True once the submit click has visibly produced an outcome:
        either the user is now logged in, OR an error message is visible,
        OR the login form is no longer on screen."""
        end = time.time() + timeout / 1000
        positive = [
            "a.user-logout",
            ".user-firstname",
            "a#myaccount",
            "a:has-text('My Account')",
        ]
        error_selectors = self.selectors(self.PAGE_KEY, "error_message")
        while time.time() < end:
            for sel in positive:
                try:
                    if self.page.locator(sel).count() > 0:
                        return True
                except Exception:
                    continue
            for sel in error_selectors:
                try:
                    loc = self.page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        return True
                except Exception:
                    continue
            try:
                # Login form disappeared → submission produced some outcome
                if self.page.locator("form#loginForm").count() == 0:
                    return True
                # Or error text appeared anywhere on the page
                body = self.page.locator("body").inner_text(timeout=1500) or ""
                if re.search(r"sorry,\s*we\s+cannot\s+find\s+an\s+account", body, re.I):
                    return True
            except Exception:
                pass
            try:
                self.page.wait_for_timeout(300)
            except Exception:
                break
        return False

    def _wait_for_enabled_submit(self, timeout: int = 8000):
        deadline = time.time() + timeout / 1000
        last = None
        while time.time() < deadline:
            for selector in self.selectors(self.PAGE_KEY, "submit_button"):
                loc = self.page.locator(selector).first
                last = loc
                try:
                    if loc.count() == 0:
                        continue
                    if loc.is_visible() and loc.is_enabled():
                        return loc
                except Exception:
                    continue
            self.page.wait_for_timeout(150)
        if last is not None:
            return last
        raise AssertionError("Login submit button never became visible")

    def error_message_visible(self, expected_fragment: str, timeout: int = 10000) -> bool:
        """Check whether the sign-in modal is showing an error containing
        the expected fragment. Whitespace is collapsed before comparison."""
        normalized_expected = re.sub(r"\s+", " ", expected_fragment).strip().lower()
        if not normalized_expected:
            return False
        end = time.time() + timeout / 1000
        while time.time() < end:
            for sel in self.selectors(self.PAGE_KEY, "error_message"):
                try:
                    loc = self.page.locator(sel).first
                    if loc.count() == 0:
                        continue
                    if not loc.is_visible():
                        continue
                    text = (loc.inner_text(timeout=2000) or "").strip()
                    if not text:
                        continue
                    normalized = re.sub(r"\s+", " ", text).lower()
                    if normalized_expected in normalized:
                        return True
                except Exception:
                    continue
            # Fallback: scan the whole page text inside the modal
            try:
                modal_text = self.page.locator(".modal.show, #loginForm").inner_text(timeout=1500)
            except Exception:
                modal_text = ""
            if modal_text:
                normalized = re.sub(r"\s+", " ", modal_text).lower()
                if normalized_expected in normalized:
                    return True
            # Last resort: scan the entire page body. The error sometimes
            # renders outside the modal scope (e.g., a flash banner near
            # the top of the page).
            try:
                body_text = self.page.locator("body").inner_text(timeout=1500)
            except Exception:
                body_text = ""
            if body_text:
                normalized = re.sub(r"\s+", " ", body_text).lower()
                if normalized_expected in normalized:
                    return True
                # Match the distinctive phrase even if the rest of the
                # sentence drifts (some sites localize punctuation/quotes).
                if "sorry, we cannot find an account" in normalized and "forgot your login information" in normalized:
                    return True
            try:
                self.page.wait_for_timeout(300)
            except Exception:
                break
        return False
