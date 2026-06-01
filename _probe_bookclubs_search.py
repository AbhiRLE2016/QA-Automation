"""Probe v4: full bookclubs-qa flow — login, dismiss overlays, search, tiles, cart."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://storefront:storefront@bookclubs-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"


def dismiss_cmp(page) -> bool:
    page.wait_for_timeout(2500)
    for frame in list(page.frames):
        if frame is page.main_frame:
            continue
        for sel in ["button:has-text('Accept All Cookies')", "button:has-text('Accept All')", "button:has-text('Accept')"]:
            try:
                btn = frame.locator(sel).first
                if btn.count() and btn.is_visible():
                    try:
                        btn.click(timeout=3000)
                    except Exception:
                        btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(1500)
                    return True
            except Exception:
                continue
    return False


def dismiss_overlays(page) -> None:
    """Force-remove Monetate / image-credits / leftover overlays that block clicks."""
    try:
        page.evaluate(
            "() => { ['monetate_lightbox','sp_message_container_1423723','imageCredits'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); }); document.querySelectorAll('.modal-backdrop').forEach(e => e.remove()); }"
        )
    except Exception:
        pass


def main() -> None:
    out = Path("reports/probe_bookclubs5")
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        dismiss_cmp(page)
        dismiss_overlays(page)

        # Open signin
        page.locator("a.signInLink-wrapper").first.dispatch_event("click")
        page.wait_for_selector("#signInModal.show form#dwfrm_login", timeout=15000)
        page.wait_for_timeout(700)

        page.locator("#signInModal input.email-input").first.fill(EMAIL)
        page.locator("#signInModal input.validatepassword").first.fill(PASSWORD)
        page.locator("#signInModal button[name='dwfrm_login_login'][type='submit']").first.click(timeout=10000)

        # Wait for modal to close OR for loginStatus to flip
        for _ in range(40):
            try:
                login_status = page.evaluate(
                    "() => (window.dumbleData && window.dumbleData.omniture && window.dumbleData.omniture.user && window.dumbleData.omniture.user.loginStatus) || false"
                )
            except Exception:
                login_status = False
            try:
                modal_cls = page.locator("#signInModal").first.get_attribute("class") or ""
            except Exception:
                modal_cls = ""
            if login_status or "show" not in modal_cls:
                break
            page.wait_for_timeout(500)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        post_login = {
            "url": page.url,
            "loginStatus": login_status,
            "modal_class": modal_cls,
            "userObj": page.evaluate("() => (window.dumbleData && JSON.stringify(window.dumbleData.omniture.user)) || ''"),
        }
        Path(out / "01_post_login.json").write_text(json.dumps(post_login, indent=2), encoding="utf-8")
        dismiss_overlays(page)
        page.screenshot(path=str(out / "01_post_login.png"), full_page=True)

        # Find search trigger; clean overlays first
        dismiss_overlays(page)
        page.wait_for_timeout(500)

        # Capture header markup once
        try:
            header_html = page.locator("header").first.evaluate("el => el.outerHTML.substring(0, 6000)")
            Path(out / "02_header.html").write_text(header_html, encoding="utf-8")
        except Exception:
            pass

        # Try to click search submit
        clicked_with = None
        for sel in [
            "header form[role='search'] button[type='submit']",
            "header button[aria-label='Search']",
            "header form[role='search'] button",
            "form[role='search'] button[type='submit']",
            "header form[name='simpleSearch'] button",
            "header svg[name='search-button']",
            "header .search-icon",
            "header button.search",
            "header button[type='submit']",
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    try:
                        loc.click(timeout=3000)
                    except Exception:
                        loc.click(timeout=3000, force=True)
                    clicked_with = sel
                    break
            except Exception:
                continue
        if not clicked_with:
            try:
                box = page.locator("header input[name='q']").first
                box.click()
                box.press("Enter")
                clicked_with = "Enter"
            except Exception as e:
                Path(out / "03_search_click_err.txt").write_text(str(e), encoding="utf-8")

        Path(out / "03_search_clicked.txt").write_text(str(clicked_with or ""), encoding="utf-8")

        try:
            page.wait_for_url(lambda u: "/search" in u or "/en/search" in u or "q=" in u, timeout=15000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        dismiss_overlays(page)

        Path(out / "04_search_url.txt").write_text(page.url, encoding="utf-8")
        page.screenshot(path=str(out / "04_search.png"), full_page=True)

        tile_diag: list[str] = []
        for sel in [
            "div.product-tile",
            "div[class*='product-tile']",
            "div.grid-tile",
            "li.grid-tile",
            "div[data-itemid]",
            "div.product",
            "div[class*='product-card']",
            "[class*='item-card']",
            "div.search-result-content",
        ]:
            try:
                cnt = page.locator(sel).count()
                visible = page.locator(sel).first.is_visible() if cnt else False
                tile_diag.append(f"{sel}: count={cnt} visible={visible}")
            except Exception as e:
                tile_diag.append(f"{sel}: err={e}")
        Path(out / "05_tile_diag.txt").write_text("\n".join(tile_diag), encoding="utf-8")

        # Capture top of search-results page
        try:
            body_html = page.locator("body").first.evaluate(
                "el => el.outerHTML.substring(0, 12000)"
            )
            Path(out / "06_search_body_top.html").write_text(body_html, encoding="utf-8")
        except Exception:
            pass

        for idx, sel in enumerate([
            "div.product-tile",
            "div[class*='product-tile']",
            "li.grid-tile",
            "div.grid-tile",
            "div[data-itemid]",
            "div[class*='product-card']",
        ]):
            try:
                if page.locator(sel).count():
                    html = page.locator(sel).first.evaluate("el => el.outerHTML.substring(0, 6000)")
                    Path(out / f"07_first_tile_{idx}.html").write_text(html, encoding="utf-8")
                    break
            except Exception:
                continue

        # If we got tiles, try to click add to cart on first
        clicked_add = None
        for sel in [
            "button.add-to-cart:not(.donateToClass):not(.d-none)",
            "button.add-to-cart",
            "button:has-text('Add to Cart')",
            "button.add-to-bag",
            "button:has-text('Add to Bag')",
        ]:
            try:
                btn = page.locator(sel).first
                if btn.count() and btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed(timeout=3000)
                    except Exception:
                        pass
                    try:
                        btn.click(timeout=4000)
                    except Exception:
                        btn.click(timeout=4000, force=True)
                    clicked_add = sel
                    break
            except Exception:
                continue
        Path(out / "08_addtocart_clicked.txt").write_text(str(clicked_add or ""), encoding="utf-8")

        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        dismiss_overlays(page)
        page.screenshot(path=str(out / "09_after_add.png"), full_page=True)

        # Mini cart number
        try:
            minicart_html = page.locator("a.minicart-link, header a[href$='/en/cart'], header a[href*='/cart']").first.evaluate("el => el.outerHTML")
            Path(out / "10_minicart.html").write_text(minicart_html, encoding="utf-8")
        except Exception as e:
            Path(out / "10_minicart.html").write_text(f"err: {e}", encoding="utf-8")

        # Go to cart
        try:
            page.goto(page.url.split("?")[0].rstrip("/").rsplit("/", 1)[0] + "/en/cart", wait_until="domcontentloaded", timeout=20000)
        except Exception:
            try:
                page.locator("a.minicart-link, header a[href$='/en/cart']").first.click(timeout=4000)
            except Exception:
                pass
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.screenshot(path=str(out / "11_cart.png"), full_page=True)
        Path(out / "12_cart_url.txt").write_text(page.url, encoding="utf-8")

        cart_diag: list[str] = []
        for sel in [
            "div.product-info",
            "div.line-item",
            "div.cart-item",
            "h1:has-text('Your Cart')",
            "h1:has-text('Cart')",
            "h1.page-title",
            ".empty-cart-message",
            ":text-matches('cart is empty', 'i')",
        ]:
            try:
                cnt = page.locator(sel).count()
                visible = page.locator(sel).first.is_visible() if cnt else False
                cart_diag.append(f"{sel}: count={cnt} visible={visible}")
            except Exception as e:
                cart_diag.append(f"{sel}: err={e}")
        Path(out / "13_cart_diag.txt").write_text("\n".join(cart_diag), encoding="utf-8")
        try:
            cart_body = page.locator("main, body").first.evaluate("el => el.innerText.substring(0, 4000)")
            Path(out / "14_cart_text.txt").write_text(cart_body, encoding="utf-8")
        except Exception:
            pass

        browser.close()


if __name__ == "__main__":
    main()
