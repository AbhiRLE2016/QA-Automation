from __future__ import annotations

import re

from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, then, when


@given(parsers.parse('the user opens "{url}"'))
def open_url(page: Page, url: str, story_context: dict) -> None:
    page.goto(url, wait_until="domcontentloaded")
    story_context["url"] = url


@when(parsers.parse('the user logs in with username "{username}" and password "{password}"'))
def login(page: Page, username: str, password: str) -> None:
    page.locator("#user-name").fill(username)
    page.locator("#password").fill(password)
    page.locator("#login-button").click()
    expect(page.locator(".inventory_list")).to_be_visible()


@when("the user adds the red t-shirt to the cart")
def add_red_tshirt_to_cart(page: Page) -> None:
    item = page.locator(".inventory_item", has_text="T-Shirt (Red)")
    expect(item).to_be_visible()
    item.get_by_role("button", name="Add to cart").click()
    expect(item.get_by_role("button", name="Remove")).to_be_visible()


@when("the user opens the cart page")
def open_cart(page: Page) -> None:
    page.locator(".shopping_cart_link").click()
    expect(page).to_have_url(re.compile(r"cart\.html"))


@when("the user presses the checkout button on the cart page")
def press_checkout_on_cart(page: Page) -> None:
    page.locator("#checkout").click()


@then(parsers.parse('the user is taken to the "{page_title}" page'))
def assert_information_page(page: Page, page_title: str) -> None:
    expect(page.locator(".title")).to_contain_text(page_title)
    expect(page).to_have_url(re.compile(r"checkout-step-one\.html"))


@when(parsers.parse('the user enters first name "{first_name}"'))
def enter_first_name(page: Page, first_name: str) -> None:
    page.locator("#first-name").fill(first_name)


@when(parsers.parse('the user enters last name "{last_name}"'))
def enter_last_name(page: Page, last_name: str) -> None:
    page.locator("#last-name").fill(last_name)


@when(parsers.parse('the user enters postal code "{postal_code}"'))
def enter_postal_code(page: Page, postal_code: str) -> None:
    page.locator("#postal-code").fill(postal_code)


@when("the user presses continue")
def press_continue(page: Page) -> None:
    page.locator("#continue").click()
    expect(page.locator(".title")).to_contain_text("Checkout: Overview")


@when("the user notes the total price and clicks finish")
def note_total_and_finish(page: Page, story_context: dict) -> None:
    total_locator = page.locator(".summary_total_label")
    expect(total_locator).to_be_visible()
    story_context["total_price"] = total_locator.inner_text().strip()
    page.locator("#finish").click()


@then(parsers.parse('the user sees the "{confirmation_text}" page'))
def assert_confirmation(page: Page, confirmation_text: str) -> None:
    expect(page.locator(".complete-header")).to_contain_text(
        confirmation_text.rstrip("!")
    )
