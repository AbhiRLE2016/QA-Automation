from __future__ import annotations

from playwright.sync_api import Page
from pytest_bdd import parsers, then, when

from pages.cart_page import CartPage
from pages.home_page import HomePage


@when("the user clicks the cart icon")
def click_cart_icon(page: Page) -> None:
    HomePage(page).go_to_cart()


@then(parsers.parse('the user is navigated to the "{label}" page'))
def navigated_to_named_page(page: Page, label: str) -> None:
    if label.strip().lower() == "your cart":
        cart = CartPage(page)
        cart.wait_for_cart()
        assert cart.is_on_your_cart_page(), f"Not on Your Cart page (url={page.url})"
        return
    assert (
        label.strip().lower() in (page.title() or "").lower()
        or label.lower() in (page.url or "").lower()
    ), f"Did not navigate to {label!r} page (url={page.url}, title={page.title()!r})"


@when(parsers.parse('the user clicks the "{symbol}" button to increase the item quantity'))
def increase_item_quantity(page: Page, symbol: str) -> None:
    CartPage(page).increase_quantity()


@then(parsers.parse('the "{label}" popup is displayed'))
def popup_displayed(page: Page, label: str) -> None:
    if "clear" in label.lower():
        assert CartPage(page).clear_cart_popup_visible(), f"{label!r} popup not displayed"
        return
    locator = page.locator(
        f"div[role='dialog']:has-text('{label}'), .modal:has-text('{label}')"
    ).first
    assert locator.count() and locator.is_visible(), f"{label!r} popup not displayed"


@when(parsers.parse('the user clicks the "{label}" button on the {popup_name} popup'))
def click_button_on_named_popup(page: Page, label: str, popup_name: str) -> None:
    cart = CartPage(page)
    if label.strip().lower() == "yes":
        cart.click_yes_in_popup()
        return
    btn = page.locator(
        f"div[role='dialog'] button:has-text('{label}'), .modal button:has-text('{label}')"
    ).first
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@then(parsers.parse('the "{label}" page is displayed with an empty cart'))
def cart_page_empty(page: Page, label: str) -> None:
    cart = CartPage(page)
    assert cart.is_on_your_cart_page(), f"Not on {label!r} page (url={page.url})"
    assert cart.is_empty_cart(), "Cart is not empty after clearing the order"
