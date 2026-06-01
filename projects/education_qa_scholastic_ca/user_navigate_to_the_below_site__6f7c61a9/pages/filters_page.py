from __future__ import annotations

import time

from playwright.sync_api import expect

from .base_page import BasePage


class FiltersPage(BasePage):
    PAGE_KEY = "filters"

    EXPECTED: list[str] = [
        "Curriculum",
        "Grade",
        "Language",
        "GRL: F&P",
        "GRL: DRA",
        "Program",
        "Subject",
        "Price",
        "Product Type",
        "Book Type",
    ]

    def filter_by_label_visible(self, timeout: int = 15000) -> bool:
        for selector in self.selectors(self.PAGE_KEY, "filter_by_label"):
            try:
                expect(self.page.locator(selector).first).to_be_visible(timeout=timeout)
                return True
            except Exception:
                continue
        return False

    def visible_filter_names(self) -> set[str]:
        names: set[str] = set()
        try:
            handles = self.page.locator(".refinement h4[aria-label]").all()
        except Exception:
            handles = []
        for h4 in handles:
            try:
                lbl = (h4.get_attribute("aria-label") or "").strip()
                if lbl:
                    names.add(lbl)
            except Exception:
                continue
        return names

    def has_filter_option(self, name: str) -> bool:
        escaped = name.replace("'", r"\'")
        try:
            if self.page.locator(f".refinement h4[aria-label='{escaped}']").count() > 0:
                return True
        except Exception:
            pass
        try:
            return self.page.locator(f".refinement :text-is('{escaped}')").count() > 0
        except Exception:
            return False

    def _h4(self, name: str):
        escaped = name.replace("'", r"\'")
        h4 = self.page.locator(f".refinement h4[aria-label='{escaped}']").first
        if h4.count() == 0:
            h4 = self.page.locator(f".refinement :text-is('{escaped}')").first
        return h4

    def _card_for(self, name: str):
        return self._h4(name).locator(
            "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' refinement ')][1]"
        ).first

    def _header_for(self, name: str):
        return self._card_for(name).locator(
            "xpath=./div[contains(concat(' ', normalize-space(@class), ' '), ' card-header ')]"
        ).first

    def _body_for(self, name: str):
        return self._card_for(name).locator(
            "xpath=./div[contains(concat(' ', normalize-space(@class), ' '), ' card-body ')]"
        ).first

    def expand_filter(self, name: str) -> None:
        header = self._header_for(name)
        try:
            header.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        try:
            header.click(timeout=4000)
        except Exception:
            try:
                header.click(timeout=4000, force=True)
            except Exception:
                try:
                    self._h4(name).click(timeout=3000, force=True)
                except Exception:
                    pass
        self._wait_for_state(name, expanded=True, timeout=4000)

    def is_filter_expanded(self, name: str) -> bool:
        body = self._body_for(name)
        if body.count() == 0:
            return False
        try:
            cls = body.get_attribute("class") or ""
            return "show" in cls.split()
        except Exception:
            return False

    def _wait_for_state(self, name: str, expanded: bool, timeout: int = 4000) -> None:
        end = time.time() + timeout / 1000
        while time.time() < end:
            if self.is_filter_expanded(name) == expanded:
                return
            self.page.wait_for_timeout(150)

    def click_clear_all(self) -> None:
        for selector in self.selectors(self.PAGE_KEY, "clear_all"):
            try:
                btns = self.page.locator(selector)
                count = btns.count()
                for index in range(count):
                    btn = btns.nth(index)
                    try:
                        if not btn.is_visible():
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
            except Exception:
                continue
        raise AssertionError("Clear All button not found")

    def all_filters_collapsed(self, timeout: int = 5000) -> bool:
        end = time.time() + timeout / 1000
        while time.time() < end:
            if not any(self.is_filter_expanded(name) for name in self.EXPECTED):
                return True
            self.page.wait_for_timeout(200)
        return not any(self.is_filter_expanded(name) for name in self.EXPECTED)
