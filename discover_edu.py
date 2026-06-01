"""Live discovery of selectors for the Education Storefront feature.

Run via: python discover_edu.py
Writes findings to mcp-selectors/discovery_edu.json so they can be reviewed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = "https://storefront:storefront@education-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"

OUT = ROOT / "mcp-selectors" / "discovery_edu.json"


def probe_signin_form(page):
    info = {}
    info["form_present"] = page.locator("form#dwfrm_login").count()
    info["username_dynamic_name"] = page.locator(
        'form#dwfrm_login input[name^="dwfrm_login_username"]'
    ).count()
    info["password_dynamic"] = page.locator('form#dwfrm_login input[type="password"]').count()
    info["submit_btn"] = page.locator('form#dwfrm_login button[name="dwfrm_login_login"]').count()
    return info


def main():
    findings = {"steps": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        # 1. Navigate
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        findings["steps"].append({"step": "home_loaded", "url": page.url, "title": page.title()})

        # Header probe
        findings["steps"].append(
            {
                "step": "header_probe",
                "myaccount_count": page.locator("a#myaccount").count(),
                "user_logout_count": page.locator("a.user-logout").count(),
                "minicart_count": page.locator(".minicart-link").count(),
                "any_signin": page.locator('a[data-element-linkname*="Sign In"], a.signInLink-wrapper').count(),
            }
        )

        # 2. Cookie banner
        cmp_iframes = page.locator('iframe[id^="sp_message_iframe_"]').all()
        findings["steps"].append({"step": "cmp_iframe_count", "count": len(cmp_iframes)})
        if cmp_iframes:
            try:
                frame = cmp_iframes[0].content_frame
                if frame is not None:
                    btn = frame.locator('button[title="Accept All Cookies"]').first
                    btn.wait_for(state="visible", timeout=5000)
                    btn.click()
                    findings["steps"].append({"step": "cookies_accepted", "ok": True})
                    page.wait_for_timeout(500)
            except Exception as exc:
                findings["steps"].append({"step": "cookies_accepted", "ok": False, "error": str(exc)})

        # 3. Open sign-in modal via My Account
        page.locator("a#myaccount").first.click()
        page.wait_for_selector("form#dwfrm_login", state="visible", timeout=15000)
        findings["steps"].append({"step": "sign_in_modal_visible", "form": probe_signin_form(page)})

        # 4. Fill credentials and submit
        page.locator('form#dwfrm_login input[name^="dwfrm_login_username"]').first.fill(EMAIL)
        page.locator('form#dwfrm_login input[type="password"]').first.fill(PASSWORD)
        page.locator('form#dwfrm_login button[name="dwfrm_login_login"]').first.click()
        page.wait_for_load_state("networkidle", timeout=30000)
        try:
            page.locator("a.user-logout").first.wait_for(state="attached", timeout=20000)
            findings["steps"].append({"step": "logged_in", "ok": True})
        except Exception as exc:
            findings["steps"].append(
                {
                    "step": "logged_in",
                    "ok": False,
                    "error": str(exc),
                    "url": page.url,
                    "user_logout_count": page.locator("a.user-logout").count(),
                }
            )

        # 5. Click search icon (without query) → all items
        # Education search uses a search button. Need to discover.
        candidates = [
            "button.global-search-button",
            'form[name="simpleSearch"] button[type="submit"]',
            'form[name="simpleSearch"] button.search-button',
            'button[aria-label*="Search"]',
            'button[aria-label*="search"]',
            "button.search-button-icon",
            'a[href*="/search?"]',
        ]
        search_probe = {}
        for sel in candidates:
            search_probe[sel] = page.locator(sel).count()
        findings["steps"].append({"step": "search_button_probe", "counts": search_probe})

        # Try clicking the first non-zero candidate
        clicked = None
        for sel in candidates:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                try:
                    loc.first.click()
                    clicked = sel
                    break
                except Exception:
                    continue
        findings["steps"].append({"step": "search_clicked", "selector": clicked})
        if clicked:
            try:
                page.wait_for_url("**/search*", timeout=15000)
            except Exception:
                pass
            page.wait_for_load_state("networkidle", timeout=20000)
        findings["steps"].append({"step": "after_search", "url": page.url, "title": page.title()})

        # 6. First product tile + price + add to cart
        tile_count = page.locator(".product-tile").count()
        findings["steps"].append({"step": "tile_count", "count": tile_count})
        if tile_count:
            first = page.locator(".product-tile").first
            findings["steps"].append(
                {
                    "step": "first_tile",
                    "data_itemid": first.get_attribute("data-itemid"),
                    "name_text": first.locator(".product-name").first.inner_text() if first.locator(".product-name").count() else None,
                }
            )
            for sel in [
                ".price-value",
                ".product-sales-price.our-price .price-value",
                ".sales .price-value",
            ]:
                if first.locator(sel).count():
                    findings["steps"].append({"step": "tile_price_probe", "selector": sel, "text": first.locator(sel).first.inner_text()})
                    break
            for sel in [
                'button[data-satellite-key="add-to-cart-button"]',
                "button.add-to-cart",
            ]:
                if first.locator(sel).count():
                    btn = first.locator(sel).first
                    try:
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        findings["steps"].append({"step": "add_to_cart_clicked", "selector": sel})
                        page.wait_for_load_state("networkidle", timeout=20000)
                        break
                    except Exception as exc:
                        findings["steps"].append({"step": "add_to_cart_failed", "selector": sel, "error": str(exc)})

        # 7. Cart navigation
        cart_link_count = page.locator('a[href$="/en/cart"]').count()
        findings["steps"].append({"step": "cart_link_count", "count": cart_link_count})
        try:
            page.locator('a[href$="/en/cart"]').first.click()
            page.wait_for_url("**/cart", timeout=15000)
        except Exception:
            page.goto("https://storefront:storefront@education-qa.scholastic.ca/en/cart", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=20000)
        findings["steps"].append({"step": "cart_loaded", "url": page.url, "title": page.title()})

        # 8. Probe cart selectors (header label, row id, plus button, clear cart, modal)
        cart_probe = {}
        for sel in [
            "h1",
            ".cart-header h1",
            ".cart h1",
            "[id^=\"productRow-\"]",
            "button.add-quantity, button.qty-plus, button.quantity-plus, button[data-action=\"plus\"], button.plus",
            ".quantity-form .plus, input.quantity-input + .plus",
            'button[data-target="#clearCartModal"], button.clear-cart',
            "#clearCartModal",
            "#clearCartModal .btn-yes, #clearCartModal button.confirm-yes, #clearCartModal button[data-dismiss-action=\"yes\"]",
            ".empty-cart-msg, .cart-empty",
        ]:
            cart_probe[sel] = page.locator(sel).count()
        findings["steps"].append({"step": "cart_probe", "counts": cart_probe})

        # h1 text and any heading text
        try:
            h1_texts = page.locator("h1").all_text_contents()
            findings["steps"].append({"step": "cart_h1_texts", "texts": h1_texts})
        except Exception:
            pass

        # Quantity controls inspection (snippet of first cart row)
        if page.locator('[id^="productRow-"]').count():
            row = page.locator('[id^="productRow-"]').first
            html = row.evaluate("el => el.outerHTML")
            # Find anything that looks like a plus button
            plus_html = re.findall(r"<button[^>]*plus[^>]*>", html, flags=re.I)[:3]
            qty_html = re.findall(r"<button[^>]*qty[^>]*>", html, flags=re.I)[:3]
            findings["steps"].append({"step": "row_html_excerpts", "plus": plus_html, "qty": qty_html, "row_id": row.get_attribute("id")})

        # Clear cart modal probe
        if page.locator("#clearCartModal").count():
            modal_html = page.locator("#clearCartModal").first.evaluate("el => el.outerHTML")
            findings["steps"].append({"step": "clear_cart_modal_excerpt", "html": modal_html[:1500]})

        OUT.write_text(json.dumps(findings, indent=2), encoding="utf-8")
        print(f"Wrote {OUT}")
        print(json.dumps(findings, indent=2))

        context.close()
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
