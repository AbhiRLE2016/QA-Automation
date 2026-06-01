from __future__ import annotations

import re

from playwright.sync_api import Locator, expect

from .base_page import BasePage


class SearchResultsPage(BasePage):
    PAGE_KEY = "search_results"

    NAME_NOISE = {"quick look", "add to cart", "add to wish list", "bonus", "new", "sale"}

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

    def fallback_navigate_to_all_items(self, base_url: str) -> None:
        for path in ("/en/search?q=", "/s/cec-ca/en/search?q=", "/s/edu-ca/en/search?q="):
            target = base_url.rstrip("/") + path
            try:
                self.page.goto(target, wait_until="domcontentloaded")
                return
            except Exception:
                continue
        target = base_url.rstrip("/") + "/en/search?q="
        self.page.goto(target, wait_until="domcontentloaded")

    def first_tile(self) -> Locator:
        for sel in self.selectors(self.PAGE_KEY, "product_tile"):
            tile = self.page.locator(sel).first
            try:
                expect(tile).to_be_visible(timeout=10000)
                return tile
            except Exception:
                continue
        raise AssertionError("No product tile is visible on the search results page")

    def _is_real_name(self, value: str) -> bool:
        cleaned = (value or "").strip()
        return bool(cleaned) and cleaned.lower() not in self.NAME_NOISE and len(cleaned) > 3

    def first_item_name(self) -> str:
        tile = self.first_tile()
        for sel in self.selectors(self.PAGE_KEY, "first_tile_name"):
            loc = tile.locator(sel).first
            try:
                if loc.count() == 0:
                    continue
                title_attr = (loc.get_attribute("title") or "").strip()
                if self._is_real_name(title_attr):
                    return title_attr
                text = (loc.inner_text() or "").strip()
                if self._is_real_name(text):
                    return text
            except Exception:
                continue
        try:
            link_title = tile.locator("a[title]").first.get_attribute("title") or ""
            if self._is_real_name(link_title):
                return link_title.strip()
        except Exception:
            pass
        for line in tile.inner_text().splitlines():
            if self._is_real_name(line):
                return line.strip()
        return tile.inner_text().strip().splitlines()[0]

    def first_item_price(self) -> str:
        price_pattern = re.compile(r"\$\s?\d[\d,]*\.\d{2}")
        tile = self.first_tile()
        for sel in self.selectors(self.PAGE_KEY, "first_tile_price"):
            loc = tile.locator(sel).first
            try:
                if loc.count() > 0:
                    text = (loc.inner_text() or "").strip()
                    m = price_pattern.search(text)
                    if m:
                        return m.group(0).replace(" ", "")
            except Exception:
                continue
        m = price_pattern.search(tile.inner_text())
        if not m:
            raise AssertionError("No price found in first product tile text")
        return m.group(0).replace(" ", "")

    def add_first_item_to_cart(self, cart_count_before: int = -1) -> None:
        tile = self.first_tile()
        try:
            tile.scroll_into_view_if_needed(timeout=5000)
        except Exception:
            pass

        for sel in self.selectors(self.PAGE_KEY, "first_tile_add_to_cart"):
            btn = tile.locator(sel).first
            if self._click_if_present(btn):
                self._wait_for_add_confirmation(cart_count_before)
                return

        for sel in self.selectors(self.PAGE_KEY, "first_tile_add_to_cart"):
            btn = self.page.locator(sel).first
            if self._click_if_present(btn):
                self._wait_for_add_confirmation(cart_count_before)
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

    def _wait_for_add_confirmation(self, cart_count_before: int = -1) -> None:
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
