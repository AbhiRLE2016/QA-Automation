from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class QuotePage(BasePage):
    """Create-Quote modal + Submit-Quote flow + Quote Confirmation page."""

    PAGE_KEY = "quote_modal"

    def wait_for_modal(self, timeout: int = 10000) -> None:
        # The Scholastic CA checkout uses a tab pane (#ppo-content) for the
        # Create-Quote panel rather than a true modal dialog. Accept either.
        candidates = list(self.selectors(self.PAGE_KEY, "modal_dialog")) + [
            "#ppo-content.active",
            ".tab-pane.ppo-content.active",
        ]
        for sel in candidates:
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        raise AssertionError("Quote modal/panel did not appear after Create Quote click")

    def close_modal_if_present(self) -> None:
        """Tab-pane variant: there isn't a true 'Close' button — the user just
        proceeds to Submit. Best-effort dismiss if a Close button exists."""
        for sel in self.selectors(self.PAGE_KEY, "close_button") + [
            "#ppo-content button.close",
            "#ppo-content button:has-text('Close')",
        ]:
            try:
                btn = self.page.locator(sel).first
                if btn.count() == 0 or not btn.is_visible():
                    continue
                try:
                    btn.click(timeout=2000)
                    return
                except Exception:
                    pass
            except Exception:
                continue
        # No close button visible — that's OK for a tab pane.

    def close_modal(self) -> None:
        """Click the Close button on the Create-Quote panel. If no Close button
        is visible (tab-pane variant), this is a no-op so the flow can proceed
        to Submit Quote."""
        for sel in (
            list(self.selectors(self.PAGE_KEY, "close_button"))
            + ["#ppo-content button.close", "#ppo-content button:has-text('Close')"]
        ):
            try:
                btn = self.page.locator(sel).first
                if btn.count() == 0:
                    continue
                if not btn.is_visible():
                    continue
                try:
                    btn.click(timeout=3000)
                    return
                except Exception:
                    try:
                        btn.click(timeout=3000, force=True)
                        return
                    except Exception:
                        continue
            except Exception:
                continue
        # No close found — tab pane has no real close button. Continue silently.

    def click_submit_quote(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "submit_quote_button"):
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
        raise AssertionError("'Submit Quote' button not found")

    def expect_confirmation_page(self, timeout: int = 20000) -> None:
        for sel in self.selectors(self.PAGE_KEY, "confirmation_heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        # URL-based fallback
        if "confirmation" in (self.page.url or "").lower() or "quote" in (self.page.url or "").lower():
            return
        raise AssertionError("Quote Confirmation page did not render")
