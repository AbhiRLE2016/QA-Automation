"""End-to-end probe of login on education-qa using exactly the same primitives as the page objects."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from pages.home_page import HomePage
from pages.login_page import LoginPage

URL = "https://storefront:storefront@education-qa.scholastic.ca"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"


def main() -> None:
    Path("reports").mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()

        home = HomePage(page)
        home.navigate(URL)
        print(f"after navigate url={page.url}, signModal={page.locator('a.signModal').count()}, loginForm={page.locator('form#loginForm').count()}")

        ok = home.accept_cookies_if_present(timeout=8000)
        print(f"after cookies ok={ok}")

        home.open_signin_modal()
        print(f"after open_signin url={page.url}, modal_show={page.locator('div.modal.show').count()}, loginForm_visible={page.locator('form#loginForm:visible').count()}")

        try:
            page.locator("form#loginForm").first.wait_for(state="visible", timeout=10000)
        except Exception as e:
            print(f"loginForm visible wait failed: {e}")
            page.screenshot(path="reports/login_modal_state.png", full_page=True)

        try:
            LoginPage(page).login(EMAIL, PASSWORD)
            print(f"after login url={page.url}, signModal={page.locator('a.signModal').count()}, user-logout={page.locator('a.user-logout').count()}, welcome={page.locator('.user-firstname').count()}")
        except Exception as e:
            print(f"login failed: {e}")
            page.screenshot(path="reports/login_fail_state.png", full_page=True)

        page.screenshot(path="reports/post_login_state.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
