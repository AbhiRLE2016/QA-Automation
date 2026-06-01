"""Step definitions for `features/login_and_cart_management.feature`.

One step per Gherkin line. Each step delegates to a POM method so any locator
brittleness is contained in the page objects.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page
from pytest_bdd import parsers, then, when

from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage


# ---------------------------------------------------------------------------
# Sign-in flow
# ---------------------------------------------------------------------------

@when(parsers.parse('user clicks on the "{label}" link'))
def click_named_link(page: Page, label: str) -> None:
    label_low = label.strip().lower()
    if label_low == "sign in":
        HomePage(page).open_signin_modal()
        return
    # Generic fallback for other labels: click first visible link with that text.
    page.locator(f"a:has-text('{label}'), button:has-text('{label}')").first.click(timeout=8000)


@when(parsers.parse('user enters email "{email}"'))
def enter_email(page: Page, email: str) -> None:
    LoginPage(page).fill_email(email)


@when(parsers.parse('user enters password "{password}"'))
def enter_password(page: Page, password: str) -> None:
    LoginPage(page).fill_password(password)


@when("user clears the email and password fields")
def clear_credentials(page: Page) -> None:
    LoginPage(page).clear_fields()


@when("user submits the sign in form")
def submit_signin(page: Page) -> None:
    LoginPage(page).submit()


@then("user should not be logged in")
def not_logged_in(page: Page) -> None:
    HomePage(page).expect_not_logged_in(timeout=8000)


# The Gherkin line escapes inner quotes (\"Forgot…\"), so a parse.parse
# `"{message}"` capture stops at the first inner quote. Use regex with a
# greedy capture to grab the entire quoted span.
@then(parsers.re(r'the message "(?P<message>.+)" should be displayed'))
def error_message_displayed(page: Page, message: str) -> None:
    # The captured text contains literal backslashes from the Gherkin escapes.
    # Strip them so we can compare to the rendered (unescaped) page text.
    cleaned = message.replace('\\"', '"').replace("\\'", "'")
    assert LoginPage(page).error_message_visible(cleaned, timeout=10000), (
        f"Expected error message not displayed: {cleaned!r}"
    )


@then("user lands on the homepage")
def lands_on_homepage(page: Page) -> None:
    HomePage(page).expect_logged_in()


# ---------------------------------------------------------------------------
# Search & cart
# ---------------------------------------------------------------------------

@when("user clicks on the search icon to get all the items")
def submit_empty_search(page: Page) -> None:
    HomePage(page).submit_empty_search()
    SearchResultsPage(page).wait_for_results(timeout=20000)


@when("user adds the first item to the cart and notes its price")
def add_first_item(page: Page, story_context: dict) -> None:
    sr = SearchResultsPage(page)
    story_context["first_item_price"] = sr.first_item_price()
    sr.add_first_item_to_cart()


@then("the item should be added to the cart")
def item_added(page: Page) -> None:
    sr = SearchResultsPage(page)
    if sr.added_to_cart_confirmation_visible(timeout=8000):
        return
    # Fallback: minicart count > 0
    try:
        count_text = page.locator("header a.minicart-link").first.inner_text() or ""
        m = re.search(r"\d+", count_text)
        if m and int(m.group(0)) > 0:
            return
    except Exception:
        pass
    raise AssertionError("No confirmation that the item was added to the cart")


@when("user clicks on the cart icon")
def click_cart_icon(page: Page) -> None:
    HomePage(page).go_to_cart()


@then(parsers.parse('user should navigate to the "{label}" page'))
def navigated_to_named_page(page: Page, label: str) -> None:
    if "cart" in label.lower():
        cart = CartPage(page)
        cart.wait_for_cart()
        assert cart.is_on_your_cart_page(), f"Not on the {label!r} page"
        return
    page.wait_for_selector(
        f"h1:has-text('{label}'), h2:has-text('{label}')", timeout=15000
    )


@when(parsers.parse(
    'user clicks the "{symbol}" button to increase the quantity of the item'
))
def click_plus(page: Page, symbol: str) -> None:
    CartPage(page).increase_quantity()


@when(parsers.parse('user clicks the "{label}" button'))
def click_named_cart_button(page: Page, label: str) -> None:
    label_low = label.strip().lower()
    if label_low == "clear my order":
        CartPage(page).click_clear_my_order()
        return
    if label_low == "yes":
        CartPage(page).click_yes_in_popup()
        return
    # Generic fallback
    btn = page.locator(
        f"button:has-text('{label}'), a:has-text('{label}')"
    ).first
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@then(parsers.parse('the "{label}" popup should be displayed'))
def popup_displayed(page: Page, label: str) -> None:
    if "clear" in label.lower() and "cart" in label.lower():
        assert CartPage(page).clear_cart_popup_visible(timeout=10000), (
            f"{label!r} popup not displayed"
        )
        return
    page.wait_for_selector(
        f"div[role='dialog']:has-text('{label}'), .modal.show:has-text('{label}')",
        timeout=10000,
    )


@when(parsers.parse('user clicks the "{label}" button on the popup'))
def click_in_popup(page: Page, label: str) -> None:
    if label.strip().lower() == "yes":
        CartPage(page).click_yes_in_popup()
        return
    btn = page.locator(
        f"div[role='dialog'] :has-text('{label}'), .modal.show :has-text('{label}')"
    ).first
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@then(parsers.parse(
    'the "{label}" page should be displayed with an empty cart'
))
def empty_cart_page(page: Page, label: str) -> None:
    cart = CartPage(page)
    assert cart.is_on_your_cart_page(), f"Not on the {label!r} page"
    assert cart.is_empty_cart(timeout=15000), "Cart is not empty"
