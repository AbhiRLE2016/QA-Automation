from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from pages.cart_page import CartPage  # noqa: F401
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

        home = HomePage(page)
        home.navigate(URL)
        home.open_signin_modal()
        LoginPage(page).login(EMAIL, PASSWORD)
        home.expect_logged_in()

        # search icon click
        try:
            home.click_search()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
        except Exception as e:
            print("SEARCH_CLICK_ERR:", e)

        srp = SearchResultsPage(page)
        try:
            srp.wait_for_results()
        except Exception as e:
            print("WAIT_RESULTS_ERR:", e)

        out_dir = Path("reports")
        out_dir.mkdir(exist_ok=True)
        (out_dir / "search_results.html").write_text(page.content(), encoding="utf-8")

        info = {"url": page.url}

        candidates = [
            "div.product-tile",
            "article.product-tile",
            "div[class*='product-tile']",
            "li[class*='product-tile']",
            "div[data-product-id]",
            "div[class*='grid-tile']",
            "div[class*='product']",
            "[data-pid]",
            "[data-product-id]",
            "li[data-itemid]",
            "div[data-itemid]",
        ]
        info["tile_counts"] = {sel: page.locator(sel).count() for sel in candidates}

        tile_html = None
        for sel in candidates:
            loc = page.locator(sel).first
            try:
                if loc.count() > 0:
                    tile_html = loc.evaluate("el => el.outerHTML")
                    info["tile_selector_used"] = sel
                    info["tile_html_len"] = len(tile_html)
                    break
            except Exception:
                continue
        if tile_html:
            (out_dir / "first_tile.html").write_text(tile_html, encoding="utf-8")

        for label_sel in [
            "button:has-text('Add to Cart')",
            "button:has-text('Add to cart')",
            "button:has-text('Add To Cart')",
            "button:has-text('Add')",
            "a:has-text('Add to Cart')",
            "[data-action*='cart' i]",
            "button[aria-label*='cart' i]",
            "button[name*='add' i]",
            "button[class*='add-to-cart' i]",
            "input[value*='Add to Cart' i]",
            "button[data-action='Cart-AddProduct']",
            "button.add-to-cart",
            "button[data-action*='Add' i]",
            "[role='button']:has-text('Add')",
        ]:
            info[f"count[{label_sel}]"] = page.locator(label_sel).count()

        # Find any element whose accessible text or value contains "Add"
        info["aria_add_count"] = page.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('button, a, input[type=submit], input[type=button]').forEach(el => {
                    const txt = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                    if (/add( to)?( cart| basket)?/i.test(txt)) {
                        out.push({
                            tag: el.tagName,
                            cls: el.className,
                            id: el.id,
                            name: el.getAttribute('name'),
                            txt: txt.slice(0,60),
                            data_action: el.getAttribute('data-action'),
                        });
                    }
                });
                return out.slice(0, 10);
            }"""
        )

        print(json.dumps(info, indent=2))

        browser.close()


if __name__ == "__main__":
    main()
