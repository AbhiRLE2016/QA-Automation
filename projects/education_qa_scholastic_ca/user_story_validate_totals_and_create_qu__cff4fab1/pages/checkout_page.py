from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class CheckoutPage(BasePage):
    """Checkout summary page — Subtotal / Shipping / HST / Total + Create-Quote entry."""

    PAGE_KEY = "checkout"

    def click_checkout_or_create_quote(self) -> None:
        """Click the 'Checkout or Create Quote' button on the cart page that brings
        the user to the checkout summary."""
        for sel in self.selectors(self.PAGE_KEY, "checkout_or_quote_button"):
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
        raise AssertionError("'Checkout or Create Quote' button not found on cart page")

    def wait_for_checkout(self, timeout: int = 20000) -> None:
        """Wait for the checkout page heading or order-summary block to render."""
        # First try the heading
        for sel in self.selectors(self.PAGE_KEY, "page_heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=timeout)
                return
            except Exception:
                continue
        # Fallback — any of the totals selectors is good enough
        for sel in self.selectors(self.PAGE_KEY, "total_value"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(timeout=5000)
                return
            except Exception:
                continue
        if "checkout" not in (self.page.url or "").lower():
            raise AssertionError("Checkout page did not render — neither heading nor totals visible")

    # Label-based lookup is the robust path: find a node whose text is exactly the
    # given label (e.g. "Total" — NOT "Subtotal"), walk up to the surrounding row,
    # and pull the first `$NN.NN` value from that row's text. Verified live against
    # the Scholastic CA checkout DOM (May 2026): rows are `<div class="d-flex
    # justify-content-between"><span>Label</span><span>$N.NN</span></div>` and the
    # grand total wrapper has the stable class `sc-checkout-total`.
    _VALUE_RE = re.compile(r"\$\s?[\d,]+\.\d{2}")

    def _value_for_label(self, label: str) -> str:
        """Return the dollar value associated with `label`. Uses `text-is` so
        looking up 'Total' does NOT match 'Subtotal'."""
        try:
            candidates = self.page.locator(
                f"span:text-is('{label}'), strong:text-is('{label}'), div:text-is('{label}')"
            )
            n = candidates.count()
            for i in range(min(n, 5)):
                span = candidates.nth(i)
                # Walk up to the nearest row-ish ancestor and scan its text
                row = span.locator(
                    "xpath=ancestor::*[contains(@class,'d-flex') or contains(@class,'row') "
                    "or contains(@class,'section-divider') or contains(@class,'sc-checkout-total') "
                    "or contains(@class,'order-summary') or contains(@class,'totals')][1]"
                )
                if row.count():
                    text = row.first.inner_text() or ""
                    m = self._VALUE_RE.search(text)
                    if m:
                        return m.group(0).replace(" ", "")
                # One level up if the row ancestor didn't catch
                parent = span.locator("xpath=..")
                if parent.count():
                    text = parent.inner_text() or ""
                    m = self._VALUE_RE.search(text)
                    if m:
                        return m.group(0).replace(" ", "")
        except Exception:
            pass

        # Strategy 2: Subtotal lives in a SINGLE div containing both label and value
        # — find a heading/div that contains the label text and extract the $ from it.
        try:
            container = self.page.locator(
                f"div.heading:has-text('{label}'), div.text-right:has-text('{label}')"
            ).first
            if container.count():
                text = container.inner_text() or ""
                m = self._VALUE_RE.search(text)
                if m:
                    return m.group(0).replace(" ", "")
        except Exception:
            pass

        raise AssertionError(f"No $ value found for label '{label}' on checkout page")

    def subtotal_text(self) -> str:
        return self._value_for_label("Subtotal")

    def shipping_text(self) -> str:
        try:
            return self._value_for_label("Shipping & Handling")
        except AssertionError:
            return self._value_for_label("Shipping")

    def hst_text(self) -> str:
        return self._value_for_label("HST")

    def total_text(self) -> str:
        # The class `sc-checkout-total` is the most stable hook for the grand
        # total on this site — try it first, then fall back to label lookup.
        try:
            total = self.page.locator(".sc-checkout-total").first
            if total.count():
                text = total.inner_text() or ""
                m = self._VALUE_RE.search(text)
                if m:
                    return m.group(0).replace(" ", "")
        except Exception:
            pass
        return self._value_for_label("Total")

    def click_payment_or_create_quote(self) -> None:
        for sel in self.selectors(self.PAGE_KEY, "payment_or_quote_button"):
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
        raise AssertionError("'Payment or Create Quote' button not found")

    def click_create_quote_link(self) -> None:
        """The red 'Payment or Create Quote' button transitions the page from
        stage=shipping to stage=payment — we need to wait for that transition
        before the tab nav-link is rendered, otherwise count()/is_visible() race
        and we never find it."""
        # Wait for the URL to flip to the payment stage so the tab nav exists
        try:
            self.page.wait_for_url(
                lambda u: "stage=payment" in (u or "") or "#payment" in (u or ""),
                timeout=8000,
            )
        except Exception:
            pass
        # `a.ppo-tab` is the most specific hook for the Create-Quote tab link.
        # Prefer it; fall back to the generic text-based selectors.
        ordered = ["a.ppo-tab"] + list(self.selectors(self.PAGE_KEY, "create_quote_link"))
        for sel in ordered:
            try:
                loc = self.page.locator(sel).first
                try:
                    expect(loc).to_be_visible(timeout=10000)
                except Exception:
                    continue
                try:
                    loc.click(timeout=5000)
                    return
                except Exception:
                    loc.click(timeout=5000, force=True)
                    return
            except Exception:
                continue
        raise AssertionError("'Create Quote' link not found on checkout page")
