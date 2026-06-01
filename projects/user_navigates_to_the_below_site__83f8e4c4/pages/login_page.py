from __future__ import annotations

import time

from playwright.sync_api import expect

from .base_page import BasePage


class LoginPage(BasePage):
    PAGE_KEY = "signin_modal"

    def login(self, email: str, password: str) -> None:
        # Defensive: if the Sourcepoint cookie iframe reattached between
        # cookie acceptance and now, dismiss it before clicking inputs —
        # otherwise the iframe intercepts pointer events and the click
        # times out. Cheap no-op when the banner isn't present.
        try:
            from .home_page import HomePage
            HomePage(self.page).accept_cookies_if_present(timeout=3000)
        except Exception:
            pass
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

    def _ensure_signin_tab(self) -> None:
        """The sign-in modal hosts BOTH the login form AND the forgot-password
        form as tabs. If the modal landed on the Reset tab (which can happen
        depending on prior state), switch to the Sign-In tab so #loginForm
        becomes visible. Verified live: the diagnostic dump showed
        `requestPasswordResetForm: visible=True; loginForm: visible=False`."""
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
        # Verified live: the Scholastic signin modal sometimes opens directly on
        # "Forgot your login information?" mode (requestPasswordResetForm). The
        # way back is a BUTTON (not a link) with class "signModal" and text
        # "Back to Login". Search by visible-text first so we don't depend on
        # fragile class fragments.
        for tab_sel in [
            "div.modal.show button:has-text('Back to Login')",
            ".modal.show button.signModal:has-text('Back to Login')",
            "button:has-text('Back to Login'):visible",
            "button.signModal:visible",
            "button:has-text('Back to Sign In'):visible",
            # Fallbacks if site changes to link form
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
                # Wait for the login form to become visible
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

    def _fill_credentials(self, email: str, password: str) -> None:
        """Wait for the login modal to be fully ready (BOTH inputs visible
        simultaneously, password not disabled), then fill them in one shot.
        Re-opens the modal once if it disappears between checks. Verified live
        against the Scholastic CA sign-in flow (May 2026)."""
        self._ensure_signin_tab()
        # Single atomic check — eliminates the race where email succeeds but
        # password is still mid-animation, which was the cause of intermittent
        # 100s+ password-not-found failures.
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
                timeout=20000,
            )
        except Exception:
            # The modal didn't render both inputs. Reopen and try once more.
            try:
                self._reopen_login_modal()
                self.page.wait_for_function(
                    """() => {
                        const f = document.querySelector('#loginForm');
                        if (!f) return false;
                        const e = f.querySelector("input[name='loginEmail']");
                        const p = f.querySelector("input[name='loginPassword']");
                        return e && p && e.offsetParent && p.offsetParent && !p.disabled;
                    }""",
                    timeout=15000,
                )
            except Exception as exc:
                # Diagnostic: dump page state so we can debug post-mortem
                try:
                    self.page.screenshot(path="reports/screenshots/login_failure.png", full_page=True)
                except Exception:
                    pass
                try:
                    state = self.page.evaluate("""() => ({
                        url: location.href,
                        login_forms: document.querySelectorAll('#loginForm').length,
                        login_form_visible: document.querySelector('#loginForm') ? document.querySelector('#loginForm').offsetParent !== null : null,
                        all_login_forms: Array.from(document.querySelectorAll('form')).map(f => ({id: f.id, visible: f.offsetParent !== null})),
                        email_inputs: document.querySelectorAll("input[name='loginEmail']").length,
                        pwd_inputs: document.querySelectorAll("input[name='loginPassword']").length,
                        modal_show: document.querySelectorAll('.modal.show').length,
                        sp_iframe: !!document.querySelector('iframe[id^=\"sp_message_iframe_\"]'),
                    })""")
                    diag = f"page state: {state}"
                except Exception:
                    diag = "(could not gather page state)"
                raise AssertionError(
                    "Login modal failed to render both email AND password inputs "
                    "within 35s total. " + diag
                ) from exc

        self.page.locator("#loginForm input[name='loginEmail']").first.fill(email)
        self.page.locator("#loginForm input[name='loginPassword']").first.fill(password)
        try:
            self.page.locator("#loginForm input[name='loginPassword']").first.press("Tab")
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
