from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage

URL = "https://storefront:storefront@bookclubs-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()

        cart_calls: list[tuple[str, int, str]] = []
        page.on(
            "response",
            lambda r: (
                cart_calls.append((r.request.method, r.status, r.url))
                if re.search(r"cart|addtocart|AddProductToCart|addProduct", r.url, re.I)
                else None
            ),
        )

        home = HomePage(page)
        home.navigate(URL)
        home.open_signin_modal()
        LoginPage(page).login(EMAIL, PASSWORD)
        home.expect_logged_in()
        home.click_search()
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        srp = SearchResultsPage(page)
        srp.wait_for_results()

        try:
            count_before = page.locator(".minicart-quantity, .mini-cart-link, [data-totalitems], a[href*='/en/cart']").first.inner_text()
        except Exception:
            count_before = "?"
        print("MINI BEFORE:", count_before[:80])

        name = srp.first_item_name()
        price = srp.first_item_price()
        print("Captured name:", name)
        print("Captured price:", price)

        tile = srp.first_tile()
        try:
            tile.scroll_into_view_if_needed(timeout=5000)
        except Exception:
            pass
        btn = tile.locator("button.add-to-cart:not(.donateToClass):not(.d-none)").first
        print("BTN count:", btn.count(), "visible:", btn.is_visible() if btn.count() else False)
        try:
            btn.click(force=True, timeout=5000)
            print("CLICKED")
        except Exception as e:
            print("CLICK ERR", e)

        try:
            page.wait_for_timeout(4000)
        except Exception:
            pass

        # Try detecting an opened modal that may need confirmation
        for sel in [
            "div[role='dialog']:has-text('Added')",
            "div.modal.in",
            "div.modal.show",
            "div[role='dialog']:visible",
            ".add-to-cart-messages",
            ".addedtocart",
            ".added-to-cart",
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    print(f"VISIBLE MODAL: {sel} -> {loc.inner_text()[:200]!r}")
            except Exception:
                continue

        try:
            count_after = page.locator(".minicart-quantity, .mini-cart-link, [data-totalitems], a[href*='/en/cart']").first.inner_text()
        except Exception:
            count_after = "?"
        print("MINI AFTER:", count_after[:80])

        print("CART NET CALLS:", len(cart_calls))
        for m, s, u in cart_calls[-15:]:
            print(f"  {m} {s} {u[:140]}")

        out_dir = Path("reports")
        out_dir.mkdir(exist_ok=True)
        (out_dir / "after_add.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(out_dir / "after_add.png"), full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
