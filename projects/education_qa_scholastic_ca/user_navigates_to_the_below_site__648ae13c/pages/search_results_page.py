from __future__ import annotations

import re

from playwright.sync_api import Locator, expect

from .base_page import BasePage


class SearchResultsPage(BasePage):
    PAGE_KEY = "search_results"

    def wait_for_results(self, timeout: int = 20000) -> None:
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass
        for selector in self.selectors(self.PAGE_KEY, "product_tile"):
            try:
                expect(self.page.locator(selector).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        raise AssertionError("Search results did not render any product tiles")

    def first_tile(self) -> Locator:
        for sel in self.selectors(self.PAGE_KEY, "product_tile"):
            tile = self.page.locator(sel).first
            try:
                expect(tile).to_be_visible(timeout=10000)
                return tile
            except Exception:
                continue
        raise AssertionError("No product tile is visible on the search results page")

    def first_item_price(self) -> str:
        """Return first tile's price as displayed (e.g. '$48.99'). Returns
        empty string if no price found — callers can decide whether to fail."""
        price_pattern = re.compile(r"\$\s?\d[\d,]*\.\d{2}")
        try:
            tile = self.first_tile()
        except AssertionError:
            return ""
        for sel in self.selectors(self.PAGE_KEY, "first_tile_price"):
            try:
                loc = tile.locator(sel).first
                if loc.count() == 0:
                    continue
                text = (loc.inner_text() or "").strip()
                m = price_pattern.search(text)
                if m:
                    return m.group(0).replace(" ", "")
            except Exception:
                continue
        try:
            m = price_pattern.search(tile.inner_text())
            if m:
                return m.group(0).replace(" ", "")
        except Exception:
            pass
        return ""

    def add_first_item_to_cart(self) -> None:
        tile = self.first_tile()
        try:
            tile.scroll_into_view_if_needed(timeout=5000)
        except Exception:
            pass

        for sel in self.selectors(self.PAGE_KEY, "first_tile_add_to_cart"):
            btn = tile.locator(sel).first
            if self._click_if_present(btn):
                self._wait_for_add_confirmation()
                return

        for sel in self.selectors(self.PAGE_KEY, "first_tile_add_to_cart"):
            btn = self.page.locator(sel).first
            if self._click_if_present(btn):
                self._wait_for_add_confirmation()
                return

        raise AssertionError("Could not find an Add to Cart control on the first product tile")

    def _click_if_present(self, btn: Locator) -> bool:
        try:
            if btn.count() == 0:
                return False
            try:
                btn.scroll_into_view_if_needed(timeout=4000)
            except Exception:
                pass
            try:
                btn.click(timeout=4000)
                return True
            except Exception:
                btn.click(timeout=4000, force=True)
                return True
        except Exception:
            return False

    def _wait_for_add_confirmation(self) -> None:
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        for sel in self.selectors(self.PAGE_KEY, "added_confirmation"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=4000)
                return
            except Exception:
                continue

    def added_to_cart_confirmation_visible(self, timeout: int = 8000) -> bool:
        for sel in self.selectors(self.PAGE_KEY, "added_confirmation"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return True
            except Exception:
                continue
        # Fallback: check body text for "added to cart"
        try:
            text = self.page.locator("body").inner_text() or ""
            if re.search(r"added to (your )?cart", text, re.IGNORECASE):
                return True
        except Exception:
            pass
        return False
