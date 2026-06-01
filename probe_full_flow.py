from __future__ import annotations

from pathlib import Path
import re

from playwright.sync_api import sync_playwright

from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage

URL = "https://storefront:storefront@bookclubs-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"


def main() -> None:
    out = Path("reports/probe")
    out.mkdir(parents=True, exist_ok=True)

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

        try:
            home.click_search()
        except Exception:
            home.submit_empty_search_via_enter()

        srp = SearchResultsPage(page)
        srp.wait_for_results()

        tile = srp.first_tile()
        tile_html = tile.evaluate("el => el.outerHTML")
        (out / "tile.html").write_text(tile_html, encoding="utf-8")

        # Probe potential name candidates
        candidates = {}
        for sel in [".product-name", "a.thumb-link[title]", "a.name-link[title]", ".product-name a", "div.product-name"]:
            loc = tile.locator(sel).first
            try:
                if loc.count() > 0:
                    candidates[sel] = {
                        "innerText": (loc.inner_text() or "").strip(),
                        "title": loc.get_attribute("title"),
                    }
            except Exception as e:
                candidates[sel] = {"err": str(e)}

        name = srp.first_item_name()
        price = srp.first_item_price()

        # Capture network calls during add-to-cart
        network_log: list[dict] = []
        page.on("request", lambda req: network_log.append({"req": req.method + " " + req.url}))
        page.on("response", lambda res: network_log.append({"res": str(res.status) + " " + res.url}))

        # Take a screenshot before clicking add
        page.screenshot(path=str(out / "before_add.png"), full_page=True)

        # Find and click the actual button (verbose)
        tile = srp.first_tile()
        add_btn = tile.locator("button.add-to-cart:not(.donateToClass):not(.d-none)").first
        print("BTN_COUNT:", add_btn.count())
        try:
            add_btn.scroll_into_view_if_needed(timeout=4000)
        except Exception as e:
            print("SCROLL_ERR:", e)
        try:
            add_btn.click(timeout=10000)
            print("CLICK: ok")
        except Exception as e:
            print("CLICK_ERR:", e)
            try:
                add_btn.click(timeout=4000, force=True)
                print("CLICK_FORCE: ok")
            except Exception as e2:
                print("CLICK_FORCE_ERR:", e2)

        # Wait for added-product modal
        for sel in [
            "#addedProductwrapper:has-text('Added')",
            "#addedProductwrapper .added-product-name",
            ".added-product-name",
            "div[role='dialog']:has-text('Added')",
            "div[role='dialog']:has-text('added')",
        ]:
            try:
                page.wait_for_selector(sel, timeout=12000)
                print("MODAL_SEL_FOUND:", sel)
                break
            except Exception:
                continue

        page.screenshot(path=str(out / "after_add.png"), full_page=True)
        body_after_add = page.locator("body").inner_text()
        (out / "after_add_body.txt").write_text(body_after_add, encoding="utf-8")
        try:
            (out / "addedwrap.html").write_text(
                page.locator("#addedProductwrapper").inner_html(timeout=2000), encoding="utf-8"
            )
        except Exception as e:
            print("ADDEDWRAP_ERR:", e)
        # Save last 50 network entries
        (out / "network.txt").write_text("\n".join([str(x) for x in network_log[-200:]]), encoding="utf-8")

        home.go_to_cart()
        cart = CartPage(page)
        cart.wait_for_cart()

        cart_text = page.locator("body").inner_text()
        (out / "cart.html").write_text(page.content(), encoding="utf-8")
        (out / "cart_text.txt").write_text(cart_text, encoding="utf-8")

        prices_in_cart = re.findall(r"\$\s?\d[\d,]*\.\d{2}", cart_text)

        report = {
            "noted_name": name,
            "noted_price": price,
            "candidates": candidates,
            "cart_url": page.url,
            "cart_prices": prices_in_cart[:20],
        }
        import json
        (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
