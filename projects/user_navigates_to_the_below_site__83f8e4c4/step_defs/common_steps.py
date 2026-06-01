"""Steps shared by all three storefront feature files.

The same Gherkin text appears under different keywords (Given/When/And/Then)
across the three stories, so each phrase is registered under @given/@when/@then
as needed.

State management note: `conftest.py` caches `storage_state` between tests for
faster runs (cookie consent + session). That means a later scenario can start
already logged-in. `click_sign_in_link` therefore *forces* a logged-out state
first (clicks the logout link if present) — guaranteeing the sign-in modal is
visible for the steps that follow. The cost is one extra logout per scenario
when the cache is warm; the benefit is that every scenario sees the same
baseline regardless of what ran before it.
"""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Page
from pytest_bdd import given, parsers, then, when

from pages.home_page import HomePage
from pages.login_page import LoginPage


def _logout_if_logged_in(page: Page) -> None:
    """Click `a.user-logout` if it's visible; otherwise do nothing. Used to
    reset baseline state when a previous scenario's storage_state left us
    authenticated."""
    for sel in ("a.user-logout", "header a.user-logout", "a:has-text('Log out')"):
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            if not loc.is_visible():
                continue
            try:
                loc.click(timeout=4000)
            except Exception:
                loc.click(timeout=4000, force=True)
            # After logout the page navigates; wait briefly for the sign-in link
            # to reappear so we don't race the next click.
            try:
                page.wait_for_selector("a.signModal", state="visible", timeout=8000)
            except Exception:
                pass
            return
        except Exception:
            continue


@given(parsers.parse('the user navigates to "{url}"'))
def navigate_to_storefront(page: Page, story_context: dict, url: str) -> None:
    home = HomePage(page)
    home.navigate(url)
    parsed = urlparse(url)
    story_context["base_url"] = f"{parsed.scheme}://{parsed.netloc}"
    story_context["start_url"] = url


@when("the user accepts all cookies if the cookie banner is displayed")
@given("the user accepts all cookies if the cookie banner is displayed")
def accept_cookies_if_displayed(page: Page) -> None:
    HomePage(page).accept_cookies_if_present(timeout=8000)


@when("the user clicks the sign in link")
@given("the user clicks the sign in link")
def click_sign_in_link(page: Page) -> None:
    _logout_if_logged_in(page)
    HomePage(page).open_signin_modal()


@when(parsers.parse('the user logs in with email "{email}" and password "{password}"'))
@given(parsers.parse('the user logs in with email "{email}" and password "{password}"'))
def login_with_credentials(page: Page, email: str, password: str) -> None:
    LoginPage(page).login(email, password)


@then("the user lands on the homepage")
@given("the user lands on the homepage")
def lands_on_homepage(page: Page) -> None:
    HomePage(page).expect_logged_in()
