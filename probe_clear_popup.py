"""Probe the structure of the Clear your Cart confirmation popup."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://storefront:storefront@education-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"

OUT = Path("reports/clear_popup_probe.json")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    findings: dict = {"steps": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_load_state("networkidle", timeout=10000)

        # accept cookies in iframe
        for fr in page.frames:
            if fr is page.main_frame:
                continue
            try:
                btn = fr.locator("button:has-text('Accept All Cookies')").first
                if btn.count() and btn.is_visible():
                    btn.click()
                    break
            except Exception:
                continue
        page.wait_for_timeout(700)

        # sign in
        page.locator("a.signModal[aria-label='Login to your account']").first.click()
        page.wait_for_selector("form#loginForm", state="visible", timeout=15000)
        page.locator("form#loginForm input[name='loginEmail']").first.click()
        page.locator("form#loginForm input[name='loginEmail']").first.type(EMAIL, delay=15)
        page.locator("form#loginForm input[name='loginPassword']").first.click()
        page.locator("form#loginForm input[name='loginPassword']").first.type(PASSWORD, delay=15)
        page.locator("form#loginForm input[name='loginPassword']").first.press("Tab")
        page.wait_for_timeout(400)
        page.locator("form#loginForm button[type='submit']").first.click()
        page.wait_for_load_state("networkidle", timeout=20000)

        # search
        page.locator("form[role='search'] svg[name='search-button']").first.click()
        try:
            page.wait_for_url("**/search*", timeout=10000)
        except Exception:
            pass
        page.wait_for_load_state("networkidle", timeout=15000)

        # add first item
        tile = page.locator("div.product-tile").first
        tile.scroll_into_view_if_needed()
        tile.locator("button.add-to-cart").first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(800)

        # navigate to cart
        page.locator("header a.minicart-link").first.click()
        page.wait_for_url("**/cart", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)

        # press '+'
        plus_candidates = [
            "button.quantity-form-increase",
            "button[aria-label*='Increase' i]",
            "button.btn-plus",
            "button.plus",
            "button:has-text('+')",
        ]
        for sel in plus_candidates:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click()
                findings["steps"].append({"step": "plus_click", "selector": sel})
                page.wait_for_load_state("networkidle", timeout=10000)
                break

        # click Clear My Order
        for sel in [
            "button:has-text('Clear My Order')",
            "a:has-text('Clear My Order')",
            "button.clear-cart",
        ]:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click()
                findings["steps"].append({"step": "clear_my_order_click", "selector": sel})
                break

        page.wait_for_timeout(1500)

        # Probe popup
        modal_candidates = [
            "div.modal.show",
            "div.modal[style*='display: block']",
            "div[role='dialog']",
            "#clearCartModal",
            "#removeProductModal",
            "div.modal:has-text('Clear')",
        ]
        modal_info = {}
        for sel in modal_candidates:
            try:
                modal_info[sel] = page.locator(sel).count()
            except Exception:
                modal_info[sel] = -1
        findings["steps"].append({"step": "modal_counts", "counts": modal_info})

        # Inspect any visible modal
        for sel in modal_candidates:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    html = loc.evaluate("el => el.outerHTML")
                    findings["steps"].append({"step": "modal_html", "selector": sel, "html": html[:3000]})
                    # gather buttons
                    btns = loc.locator("button").all()
                    btn_info = []
                    for b in btns[:10]:
                        try:
                            btn_info.append({
                                "text": (b.inner_text() or "").strip()[:80],
                                "class": b.get_attribute("class"),
                                "id": b.get_attribute("id"),
                                "aria": b.get_attribute("aria-label"),
                                "data-action": b.get_attribute("data-action"),
                            })
                        except Exception:
                            continue
                    findings["steps"].append({"step": "modal_buttons", "selector": sel, "buttons": btn_info})
                    break
            except Exception:
                continue

        OUT.write_text(json.dumps(findings, indent=2), encoding="utf-8")
        print(json.dumps(findings, indent=2)[:6000])
        browser.close()


if __name__ == "__main__":
    main()
