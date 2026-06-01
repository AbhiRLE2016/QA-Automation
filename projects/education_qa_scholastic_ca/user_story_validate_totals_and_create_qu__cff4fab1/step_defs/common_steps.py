"""Steps shared by multiple stories.

Each step is registered under both @given/@when (and @when/@then where applicable)
so the same Gherkin text can match regardless of which keyword (Given/When/And/Then)
the feature file uses.
"""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Page
from pytest_bdd import given, parsers, then, when

from pages.home_page import HomePage
from pages.login_page import LoginPage


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
    HomePage(page).accept_cookies_if_present(timeout=5000)


@when("the user clicks the sign in link")
@given("the user clicks the sign in link")
def click_sign_in_link(page: Page) -> None:
    HomePage(page).open_signin_modal()


@when(parsers.parse('the user logs in with email "{email}" and password "{password}"'))
@given(parsers.parse('the user logs in with email "{email}" and password "{password}"'))
def login_with_credentials(page: Page, email: str, password: str) -> None:
    LoginPage(page).login(email, password)


@then("the user lands on the homepage")
@given("the user lands on the homepage")
def lands_on_homepage(page: Page) -> None:
    HomePage(page).expect_logged_in()
