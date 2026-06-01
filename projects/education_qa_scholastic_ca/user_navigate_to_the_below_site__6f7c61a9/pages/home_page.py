from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


_FRAME_COOKIE_SELECTORS = [
    "button[title='Accept All Cookies']",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Accept All')",
    "button[aria-label*='Accept' i]",
]


class HomePage(BasePage):
    PAGE_KEY = "home"

    def navigate(self, url: str) -> None:
        # Skip wait_for_load_state("networkidle") — the storefront has long-tail
        # tracking requests that never let the network go idle, so the wait
        # always burns its full 10s timeout. Step defs that need a particular
        # element wait on that element directly instead.
        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

    def accept_cookies_if_present(self, timeout: int = 4000) -> bool:
        # Main-frame buttons (e.g. OneTrust)
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
        # Sourcepoint CMP iframe (id^="sp_message_iframe_") or generic CMP iframes
        deadline_ms = max(timeout, 1000)
        try:
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        for frame in list(self.page.frames):
            if frame is self.page.main_frame:
                continue
            for sel in _FRAME_COOKIE_SELECTORS:
                try:
                    btn = frame.locator(sel).first
                    if btn.count() == 0:
                        continue
                    try:
                        btn.wait_for(state="visible", timeout=min(deadline_ms, 2000))
                    except Exception:
                        continue
                    try:
                        btn.click(timeout=2000)
                    except Exception:
                        btn.click(timeout=2000, force=True)
                    try:
                        self.page.wait_for_timeout(500)
                    except Exception:
                        pass
                    return True
                except Exception:
                    continue
        return False

    def open_signin_modal(self) -> None:
        self.accept_cookies_if_present(timeout=2000)
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
        raise AssertionError("User does not appear logged in: " + ", ".join(last_seen))

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
