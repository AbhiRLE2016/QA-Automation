from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class AccountPage(BasePage):
    """My Account → My Quotes & Orders → delete-quote flow + 'no quotes' assertion."""

    PAGE_KEY = "account"

    def open_my_account(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "my_account_link"):
            try:
                link = self.page.locator(sel).first
                if link.count() == 0:
                    continue
                if not link.is_visible():
                    continue
                try:
                    link.hover(timeout=2000)
                except Exception:
                    pass
                try:
                    link.click(timeout=5000)
                    return
                except Exception:
                    link.click(timeout=5000, force=True)
                    return
            except Exception:
                continue
        raise AssertionError("'My Account' link not found")

    def click_my_quotes_and_orders(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "my_quotes_and_orders_link"):
            try:
                link = self.page.locator(sel).first
                if link.count() == 0:
                    continue
                if not link.is_visible():
                    continue
                try:
                    link.click(timeout=5000)
                    return
                except Exception:
                    link.click(timeout=5000, force=True)
                    return
            except Exception:
                continue
        raise AssertionError("'My Quotes and Orders' link not found")

    def wait_for_my_quotes_page(self, timeout: int = 15000) -> None:
        for sel in self.selectors(self.PAGE_KEY, "my_quotes_heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        if "quote" in (self.page.url or "").lower():
            return
        raise AssertionError("'My Quotes and Orders' page did not render")

    def click_delete_quote(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "delete_quote_link"):
            try:
                btn = self.page.locator(sel).first
                if btn.count() == 0:
                    continue
                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                if not btn.is_visible():
                    continue
                try:
                    btn.click(timeout=5000)
                    return
                except Exception:
                    btn.click(timeout=5000, force=True)
                    return
            except Exception:
                continue
        raise AssertionError("Delete-quote link not found")

    def wait_for_delete_popup(self, timeout: int = 8000) -> None:
        for sel in self.selectors(self.PAGE_KEY, "delete_popup"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        raise AssertionError("Delete-quote popup did not appear")

    def click_yes_in_delete_popup(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "delete_popup_yes"):
            try:
                btn = self.page.locator(sel).first
                if btn.count() == 0:
                    continue
                if not btn.is_visible():
                    continue
                try:
                    btn.click(timeout=5000)
                    return
                except Exception:
                    btn.click(timeout=5000, force=True)
                    return
            except Exception:
                continue
        raise AssertionError("Yes button in delete-quote popup not found")

    def expect_no_quotes_message(self, timeout: int = 15000) -> None:
        for sel in self.selectors(self.PAGE_KEY, "no_quotes_text"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        raise AssertionError("'You have no quotes' empty-state text not visible")
