"""Manual step-by-step login probe to figure out what makes story 1 succeed but story 2 fail."""
from __future__ import annotations

from playwright.sync_api import sync_playwright

URL = "https://storefront:storefront@education-qa.scholastic.ca"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"


def main() -> None:
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
        print(f"after navigate: url={page.url}")

        # cookies in iframe
        for fr in page.frames:
            if fr is page.main_frame:
                continue
            try:
                btn = fr.locator("button:has-text('Accept All Cookies')").first
                if btn.count() and btn.is_visible():
                    btn.click()
                    print("accepted cookies in iframe")
                    break
            except Exception:
                pass
        page.wait_for_timeout(800)

        # click sign-in
        page.locator("a.signModal[aria-label='Login to your account']").first.click()
        page.wait_for_selector("form#loginForm", state="visible", timeout=15000)
        print(f"after sign-in click: modal visible, loginForm count={page.locator('form#loginForm').count()}")

        email_loc = page.locator("form#loginForm input[name='loginEmail']").first
        password_loc = page.locator("form#loginForm input[name='loginPassword']").first
        print(f"email visible: {email_loc.is_visible()}, password visible: {password_loc.is_visible()}")

        email_loc.click()
        email_loc.fill("")
        email_loc.type(EMAIL, delay=20)
        password_loc.click()
        password_loc.fill("")
        password_loc.type(PASSWORD, delay=20)
        password_loc.press("Tab")
        page.wait_for_timeout(500)

        submit = page.locator("form#loginForm button[type='submit']").first
        print(f"submit enabled: {submit.is_enabled()}")
        submit.click()
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        print(f"after submit: url={page.url}")
        print(f"signModal={page.locator('a.signModal').count()}, user-logout={page.locator('a.user-logout').count()}")
        # Capture any error message
        try:
            err_text = page.locator(".alert-danger, .form-error, .modal-error, [data-testid='login-error']").all_inner_texts()
            print(f"errors: {err_text}")
        except Exception:
            pass
        # snippet of body
        body = page.locator("body").inner_text()[:600]
        print(f"BODY excerpt: {body!r}")

        page.screenshot(path="reports/manual_post_login.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
