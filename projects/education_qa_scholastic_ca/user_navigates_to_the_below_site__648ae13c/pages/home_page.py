from __future__ import annotations

import re
import time

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

_SP_CONTAINER_PATTERN = "sp_message_container_"
_SP_IFRAME_PATTERN = "sp_message_iframe_"


class HomePage(BasePage):
    PAGE_KEY = "home"

    def navigate(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

    def accept_cookies_if_present(self, timeout: int = 8000) -> bool:
        """Dismiss the Sourcepoint/OneTrust cookie banner. Tries the SP frame
        idiom first (verified-working on Scholastic CA), then enumerates
        non-main frames as a fallback."""
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

        deadline = time.time() + max(timeout, 1000) / 1000
        while time.time() < deadline:
            for selector in self.selectors("common", "cookie_accept"):
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() == 0 or not btn.is_visible():
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

            for frame in list(self.page.frames):
                if frame is self.page.main_frame:
                    continue
                for sel in _FRAME_COOKIE_SELECTORS:
                    try:
                        btn = frame.locator(sel).first
                        if btn.count() == 0 or not btn.is_visible():
                            continue
                        try:
                            btn.click(timeout=2500)
                        except Exception:
                            try:
                                btn.click(timeout=2500, force=True)
                            except Exception:
                                continue
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
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
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
        # Wait for modal to render
        for selector in self.selectors("signin_modal", "dialog"):
            try:
                self.page.wait_for_selector(selector, state="visible", timeout=10000)
                return
            except Exception:
                continue

    def submit_empty_search(self) -> None:
        """Submit an empty search to retrieve all items.

        Try clicking the search submit button first; fall back to focusing
        the search box and pressing Enter."""
        for selector in self.selectors(self.PAGE_KEY, "search_submit_button"):
            try:
                btn = self.page.locator(selector).first
                if btn.count() == 0 or not btn.is_visible():
                    continue
                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                try:
                    btn.click(timeout=4000)
                except Exception:
                    btn.click(timeout=4000, force=True)
                return
            except Exception:
                continue
        # Fall back: focus the search field and press Enter with empty value
        for selector in self.selectors(self.PAGE_KEY, "search_textbox"):
            try:
                loc = self.page.locator(selector).first
                if loc.count() == 0 or not loc.is_visible():
                    continue
                loc.click()
                loc.fill("")
                loc.press("Enter")
                return
            except Exception:
                continue
        raise AssertionError("Could not submit search to retrieve all items")

    def expect_logged_in(self, timeout: int = 20000) -> None:
        positive_selectors = [
            "a.user-logout",
            ".user-firstname",
            "a#myaccount",
            "a:has-text('My Account')",
            "header :text-matches('Welcome,', 'i')",
        ]
        end = time.time() + timeout / 1000
        while time.time() < end:
            for sel in positive_selectors:
                try:
                    if self.page.locator(sel).count() > 0:
                        return
                except Exception:
                    continue
            try:
                if self.page.locator("a.signModal").count() == 0:
                    return
            except Exception:
                pass
            try:
                self.page.wait_for_timeout(300)
            except Exception:
                break
        raise AssertionError(
            "User does not appear logged in. url=%s signModal=%d loginForm=%d"
            % (
                self.page.url,
                self.page.locator("a.signModal").count(),
                self.page.locator("form#loginForm").count(),
            )
        )

    def expect_not_logged_in(self, timeout: int = 5000) -> None:
        """Negative-login assertion. We are NOT logged in if the login form
        is still visible OR the sign-in link is still present in the header."""
        end = time.time() + timeout / 1000
        while time.time() < end:
            try:
                form = self.page.locator("form#loginForm").count()
                signin = self.page.locator("a.signModal").count()
                logged = self.page.locator(
                    "a.user-logout, .user-firstname, a#myaccount, a:has-text('My Account')"
                ).count()
            except Exception:
                form = signin = logged = 0
            if logged > 0:
                raise AssertionError("User appears LOGGED IN; expected NOT logged in")
            if form > 0 or signin > 0:
                return
            try:
                self.page.wait_for_timeout(200)
            except Exception:
                break
        if self.page.locator("a.signModal, form#loginForm").count() > 0:
            return
        raise AssertionError(
            "Could not confirm logged-out state — neither sign-in link nor login form visible"
        )

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
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
