from __future__ import annotations

import re
import time

from playwright.sync_api import expect

from .base_page import BasePage


class CartPage(BasePage):
    PAGE_KEY = "cart"

    def wait_for_cart(self, timeout: int = 20000) -> None:
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass
        for sel in self.selectors(self.PAGE_KEY, "cart_line_item"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        for sel in self.selectors(self.PAGE_KEY, "cart_heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=5000)
                return
            except Exception:
                continue
        raise AssertionError("Cart page did not render line items or cart heading")

    def cart_text(self) -> str:
        return self.page.locator("body").inner_text()

    def has_item_with_name(self, name: str) -> bool:
        if not name:
            return False
        normalized = re.sub(r"\s+", " ", name).strip().lower()
        body_text = re.sub(r"\s+", " ", self.cart_text()).lower()
        return normalized in body_text

    def has_price(self, price: str) -> bool:
        normalized = (price or "").replace(" ", "").replace("$", "").strip()
        if not normalized:
            return False
        target = normalized.replace(",", "")
        body_text = self.cart_text()
        for token in re.findall(r"\d[\d,]*\.\d{2}", body_text):
            if token.replace(",", "") == target:
                return True
        return False

    def is_on_your_cart_page(self, timeout: int = 15000) -> bool:
        try:
            self.page.wait_for_url(re.compile(r".*/cart"), timeout=timeout)
        except Exception:
            pass
        for sel in self.selectors(self.PAGE_KEY, "cart_heading"):
            try:
                loc = self.page.locator(sel).first
                if loc.count() == 0:
                    continue
                if loc.is_visible():
                    text = (loc.inner_text(timeout=2000) or "").strip()
                    if "your cart" in text.lower() or "shopping cart" in text.lower():
                        return True
            except Exception:
                continue
        return "/cart" in self.page.url

    def increase_quantity(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "quantity_increase"):
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
                    self._wait_for_idle()
                    return
                except Exception:
                    try:
                        btn.click(timeout=5000, force=True)
                        self._wait_for_idle()
                        return
                    except Exception:
                        continue
            except Exception:
                continue
        raise AssertionError("Quantity '+' button not found on cart page")

    def click_clear_my_order(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "clear_my_order"):
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
        raise AssertionError("Clear My Order control not found")

    def clear_cart_popup_visible(self, timeout: int = 8000) -> bool:
        for sel in self.selectors(self.PAGE_KEY, "clear_popup"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return True
            except Exception:
                continue
        return False

    def click_yes_in_popup(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "popup_yes"):
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
        raise AssertionError("Yes button on Clear Cart popup not found")

    def is_empty_cart(self, timeout: int = 15000) -> bool:
        end = time.time() + timeout / 1000
        while time.time() < end:
            try:
                self.page.wait_for_load_state("networkidle", timeout=2000)
            except Exception:
                pass
            for sel in self.selectors(self.PAGE_KEY, "empty_cart_message"):
                try:
                    loc = self.page.locator(sel).first
                    if loc.count() and loc.is_visible():
                        return True
                except Exception:
                    continue
            try:
                line_items = self.page.locator(", ".join(self.selectors(self.PAGE_KEY, "cart_line_item"))).count()
            except Exception:
                line_items = -1
            try:
                body = self.page.locator("body").inner_text() or ""
            except Exception:
                body = ""
            if line_items == 0 and re.search(r"empty|no items", body, re.I):
                return True
            self.page.wait_for_timeout(300)
        return False

    def _wait_for_idle(self) -> None:
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
