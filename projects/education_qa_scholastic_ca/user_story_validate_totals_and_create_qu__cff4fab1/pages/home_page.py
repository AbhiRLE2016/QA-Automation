from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


_FRAME_COOKIE_SELECTORS = [
    "button[title='Accept All Cookies']",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Accept All')",
    "button:has-text('I Accept')",
    "button:has-text('ACCEPT ALL')",
    "button[aria-label*='Accept' i]",
    "button[title*='Accept' i]",
]

# Sourcepoint CMP container id pattern. Container element (a div with role=dialog)
# wraps the iframe; we want to dismiss the whole container, not just the iframe.
_SP_CONTAINER_PATTERN = "sp_message_container_"
_SP_IFRAME_PATTERN = "sp_message_iframe_"


class HomePage(BasePage):
    PAGE_KEY = "home"

    def navigate(self, url: str) -> None:
        # Skip wait_for_load_state("networkidle") — the storefront has long-tail
        # tracking requests that never let the network go idle, so the wait
        # always burns its full 10s timeout. Step defs that need a particular
        # element wait on that element directly instead.
        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

    def accept_cookies_if_present(self, timeout: int = 8000) -> bool:
        """Dismiss the cookie consent banner. Verified-working strategy used by
        Playwright MCP itself for the Scholastic CA Sourcepoint banner:
            `page.locator('iframe[title="SP Consent Message"]').contentFrame()
             .getByRole('button', { name: 'Accept All Cookies' }).click()`
        Tries this idiom first, falls back to the legacy iframe enumeration."""
        # ---- Strategy 0: Playwright frame_locator on the SP iframe by title ----
        try:
            sp_frame = self.page.frame_locator("iframe[title='SP Consent Message']")
            for label in ("Accept All Cookies", "Accept All", "Allow All", "I Accept"):
                try:
                    btn = sp_frame.get_by_role("button", name=label)
                    if btn.count() == 0:
                        continue
                    try:
                        btn.first.click(timeout=4000)
                    except Exception:
                        btn.first.click(timeout=4000, force=True)
                    self._wait_for_cmp_to_dismiss(timeout_ms=5000)
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        import time as _time
        deadline = _time.time() + max(timeout, 1000) / 1000

        while _time.time() < deadline:
            # --- Main-frame banners (e.g. OneTrust) ---
            for selector in self.selectors("common", "cookie_accept"):
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() == 0:
                        continue
                    if not btn.is_visible():
                        continue
                    try:
                        btn.click(timeout=2000)
                    except Exception:
                        btn.click(timeout=2000, force=True)
                    try:
                        btn.wait_for(state="hidden", timeout=3000)
                    except Exception:
                        pass
                    return True
                except Exception:
                    continue

            # --- Sourcepoint CMP iframe (id^="sp_message_iframe_") ---
            for frame in list(self.page.frames):
                if frame is self.page.main_frame:
                    continue
                frame_name = (frame.name or "") + " " + (frame.url or "")
                # Prefer Sourcepoint frames first; fall back to any non-main iframe
                is_cmp = _SP_IFRAME_PATTERN in frame_name or "privacy-mgmt" in frame_name
                if not is_cmp and len(self.page.frames) > 2:
                    # Skip non-CMP iframes when there are many (e.g., trackers)
                    pass
                for sel in _FRAME_COOKIE_SELECTORS:
                    try:
                        btn = frame.locator(sel).first
                        if btn.count() == 0:
                            continue
                        if not btn.is_visible():
                            continue
                        try:
                            btn.click(timeout=2500)
                        except Exception:
                            try:
                                btn.click(timeout=2500, force=True)
                            except Exception:
                                continue
                        # After the click, wait up to 5s for the iframe / container
                        # to disappear so subsequent clicks aren't intercepted.
                        self._wait_for_cmp_to_dismiss(timeout_ms=5000)
                        return True
                    except Exception:
                        continue

            try:
                self.page.wait_for_timeout(300)
            except Exception:
                break
        return False

    def _wait_for_cmp_to_dismiss(self, timeout_ms: int = 5000) -> None:
        """After clicking Accept, wait until the Sourcepoint container/iframe is
        gone — otherwise the next click can still be intercepted by it."""
        import time as _time
        end = _time.time() + timeout_ms / 1000
        while _time.time() < end:
            try:
                container_count = self.page.locator(
                    f"div[id^='{_SP_CONTAINER_PATTERN}']"
                ).count()
                iframe_count = self.page.locator(
                    f"iframe[id^='{_SP_IFRAME_PATTERN}']"
                ).count()
            except Exception:
                container_count = 0
                iframe_count = 0
            if container_count == 0 and iframe_count == 0:
                return
            try:
                self.page.wait_for_timeout(250)
            except Exception:
                break

    def open_signin_modal(self) -> None:
        # Sourcepoint banner can attach late; give it a generous window to appear
        # AND dismiss before we try to interact with the sign-in link.
        self.accept_cookies_if_present(timeout=8000)
        for selector in self.selectors(self.PAGE_KEY, "sign_in_link"):
            try:
                link = self.page.locator(selector).first
                if link.count() == 0:
                    continue
                try:
                    link.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                try:
                    link.click(timeout=5000)
                except Exception:
                    link.click(timeout=5000, force=True)
                break
            except Exception:
                continue
        for selector in self.selectors("signin_modal", "dialog"):
            try:
                expect(self.page.locator(selector).first).to_be_visible(timeout=10000)
                return
            except Exception:
                continue

    def click_search(self, timeout: int = 8000) -> None:
        for selector in self.selectors(self.PAGE_KEY, "search_submit_button"):
            btn = self.page.locator(selector).first
            try:
                if btn.count() == 0:
                    continue
                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                try:
                    btn.click(timeout=timeout)
                    return
                except Exception:
                    try:
                        btn.click(timeout=timeout, force=True)
                        return
                    except Exception:
                        continue
            except Exception:
                continue
        raise AssertionError("Search submit control not found")

    def submit_empty_search_via_enter(self) -> None:
        loc = self.first_visible(self.selectors(self.PAGE_KEY, "search_textbox"))
        loc.click()
        loc.press("Enter")

    def search_for(self, query: str) -> None:
        """Type the given query into the header search box and submit it."""
        loc = self.first_visible(self.selectors(self.PAGE_KEY, "search_textbox"))
        loc.click()
        loc.fill("")
        loc.fill(str(query))
        try:
            self.click_search(timeout=4000)
        except AssertionError:
            loc.press("Enter")

    def _capture_login_diagnostic(self) -> str:
        """Pull any visible error / state hint after a failed login submit."""
        try:
            return self.page.evaluate(
                """() => {
                    const errs = Array.from(document.querySelectorAll(
                        '.alert.alert-danger, .login-form-error, .form-error, '
                        + '#loginForm .error-message, #loginForm .invalid-feedback, '
                        + '#loginForm small.text-danger, .modal.show .text-danger'
                    )).filter(e => e.offsetParent !== null).map(e => (e.textContent || '').trim()).filter(Boolean);
                    return errs.slice(0, 4).join(' | ') || '';
                }"""
            )
        except Exception:
            return ""

    def expect_logged_in(self, timeout: int = 20000) -> None:
        import time as _time

        positive_selectors = [
            "a.user-logout",
            ".user-firstname",
            "a#myaccount",
            "a:has-text('My Account')",
            "header :text-matches('Welcome,', 'i')",
        ]
        end = _time.time() + timeout / 1000
        while _time.time() < end:
            for sel in positive_selectors:
                try:
                    if self.page.locator(sel).count() > 0:
                        return
                except Exception:
                    continue
            try:
                if self.page.locator("a.signModal").count() == 0:
                    # The sign-in link is gone — user must be logged in.
                    return
            except Exception:
                pass
            try:
                self.page.wait_for_timeout(300)
            except Exception:
                break
        last_seen: list[str] = []
        try:
            last_seen = [
                f"url={self.page.url}",
                f"signModal={self.page.locator('a.signModal').count()}",
                f"loginForm={self.page.locator('form#loginForm').count()}",
                f"user-logout={self.page.locator('a.user-logout').count()}",
                f"myaccount={self.page.locator('a#myaccount').count()}",
            ]
        except Exception:
            pass
        err = self._capture_login_diagnostic()
        msg = "User does not appear logged in: " + ", ".join(last_seen)
        if err:
            msg += f" | form error: {err}"
        raise AssertionError(msg)

    def cart_count(self) -> int:
        for selector in self.selectors(self.PAGE_KEY, "cart_link"):
            try:
                loc = self.page.locator(selector).first
                if loc.count() == 0:
                    continue
                text = loc.inner_text() or ""
                m = re.search(r"\d+", text)
                if m:
                    return int(m.group(0))
            except Exception:
                continue
        return -1

    def go_to_cart(self) -> None:
        clicked = False
        for selector in self.selectors(self.PAGE_KEY, "cart_link"):
            try:
                link = self.page.locator(selector).first
                if link.count() == 0:
                    continue
                try:
                    link.click(timeout=4000)
                except Exception:
                    link.click(timeout=4000, force=True)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            raise AssertionError("Cart link not found")
        try:
            self.page.wait_for_url(re.compile(r".*/cart"), timeout=15000)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
