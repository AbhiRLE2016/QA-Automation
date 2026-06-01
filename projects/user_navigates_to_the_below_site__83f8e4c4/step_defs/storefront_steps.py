"""Step definitions for the three storefront feature files in /features.

Covers the unique steps across:
  - story_1_invalid_login_validation.feature  (negative-login)
  - story_2_valid_login_and_add_first_item_to_cart.feature  (login + add)
  - story_3_cart_quantity_update_and_clear_cart.feature  (cart ops)

Shared steps (navigate, cookies, click-sign-in, log-in, lands-on-homepage)
live in `common_steps.py`.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect
from pytest_bdd import parsers, then, when

from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage


# ---------------------------------------------------------------------------
# Sign-in form interactions (split into discrete steps so Story 1 can assert
# inline-validation behaviour without auto-retrying the login like the
# combined `logs in with email...` helper does)
# ---------------------------------------------------------------------------

@when("the user clears the email and password fields")
def clear_email_and_password(page: Page) -> None:
    # `Locator.fill('')` replaces the value, so this is equivalent to clearing.
    # We do it defensively in case the modal pre-filled either input.
    for sel in (
        "#loginForm input[name='loginEmail']",
        "#loginForm input[name='loginPassword']",
    ):
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.fill("")
        except Exception:
            continue


@when(parsers.parse('the user enters email "{email}" and password "{password}"'))
def enter_email_and_password(page: Page, email: str, password: str) -> None:
    login = LoginPage(page)
    login._ensure_signin_tab()  # noqa: SLF001 — internal helper, reuse intentional
    login._fill_credentials(email, password)  # noqa: SLF001


@when("the user submits the sign in form")
def submit_sign_in_form(page: Page) -> None:
    login = LoginPage(page)
    submit = login._wait_for_enabled_submit()  # noqa: SLF001
    login._submit_and_wait(submit)  # noqa: SLF001


# ---------------------------------------------------------------------------
# Story 1: negative-login assertions
# ---------------------------------------------------------------------------

_LOGIN_SUCCESS_SELECTORS = (
    "a.user-logout",
    ".user-firstname",
    "a#myaccount",
    "header a:has-text('My Account')",
)


@then("the user is not logged in")
def user_is_not_logged_in(page: Page) -> None:
    for sel in _LOGIN_SUCCESS_SELECTORS:
        try:
            count = page.locator(sel).count()
        except Exception:
            count = 0
        assert count == 0, f"Expected no logged-in indicator, but '{sel}' is present"


@then(parsers.parse('the "{message}" validation message is displayed'))
def validation_message_displayed(page: Page, message: str) -> None:
    pattern = re.compile(re.escape(message), re.IGNORECASE)
    # The Scholastic sign-in modal renders the inline error inside the form;
    # common locations: .alert-danger, .form-error, .login-form-error, generic
    # text inside the modal. Search broadly and assert on visible body text.
    candidates = [
        ".modal.show .alert-danger",
        ".modal.show .login-form-error",
        ".modal.show .form-error",
        ".modal.show .invalid-feedback",
        "#loginForm .alert-danger",
        "#loginForm .text-danger",
        "#loginForm .error-message",
        "#loginForm .invalid-feedback",
        f":text-matches('{re.escape(message)}', 'i')",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            try:
                expect(loc).to_be_visible(timeout=8000)
            except Exception:
                continue
            text = (loc.inner_text(timeout=2000) or "").strip()
            if pattern.search(text):
                return
            # Visible element found, but text didn't match — still acceptable
            # if it contains *any* part of the expected phrase. Fall through
            # to the body-text fallback if not.
        except Exception:
            continue
    # Fallback: scan the full visible body text.
    try:
        body = page.locator("body").inner_text(timeout=4000) or ""
    except Exception:
        body = ""
    assert pattern.search(body), (
        f"Validation message '{message}' not visible anywhere on the page"
    )


# ---------------------------------------------------------------------------
# Story 2/3: search + add-to-cart
# ---------------------------------------------------------------------------

@when("the user clicks the search icon to view all items")
def click_search_icon_for_all_items(page: Page) -> None:
    # On the Scholastic Education CA storefront, submitting an empty search
    # routes to `/search?q=` which lists ALL items. Try clicking the search
    # submit button first; fall back to pressing Enter in the search box.
    home = HomePage(page)
    try:
        home.click_search(timeout=5000)
    except AssertionError:
        home.submit_empty_search_via_enter()
    SearchResultsPage(page).wait_for_results(timeout=25000)


@when("the user adds the first item to the cart and notes its dollar value")
def add_first_item_and_note_price(page: Page, story_context: dict) -> None:
    results = SearchResultsPage(page)
    results.wait_for_results(timeout=20000)
    try:
        story_context["first_item_name"] = results.first_item_name()
    except Exception:
        story_context["first_item_name"] = ""
    try:
        story_context["first_item_price"] = results.first_item_price()
    except Exception:
        story_context["first_item_price"] = ""
    cart_count_before = HomePage(page).cart_count()
    story_context["cart_count_before"] = cart_count_before
    results.add_first_item_to_cart(cart_count_before=cart_count_before)


@then("the item is added to the cart page")
def item_is_added_to_cart_page(page: Page, story_context: dict) -> None:
    # The add-to-cart on this storefront either (a) shows a green toast, OR
    # (b) increments the header cart count. Either signal is sufficient
    # confirmation. We avoid auto-navigating to the cart page here — that's
    # a separate Gherkin step (`the user clicks the cart icon`).
    home = HomePage(page)
    cart_count_before = story_context.get("cart_count_before", -1)

    # Signal 1: explicit added-confirmation banner/toast.
    cart = CartPage(page)
    if cart.added_to_cart_message_visible(timeout=4000):
        return

    # Signal 2: header cart count went up.
    try:
        page.wait_for_function(
            """(prev) => {
                const link = document.querySelector('header a.minicart-link, a.minicart-link, header a[href*=\"/cart\"]');
                if (!link) return false;
                const m = (link.innerText || '').match(/\\d+/);
                if (!m) return false;
                return parseInt(m[0], 10) > prev;
            }""",
            arg=cart_count_before,
            timeout=8000,
        )
        return
    except Exception:
        pass

    # Signal 3: body text mentions the success language.
    try:
        body = page.locator("body").inner_text(timeout=3000) or ""
    except Exception:
        body = ""
    assert re.search(r"added to (your )?cart", body, re.IGNORECASE), (
        "No add-to-cart confirmation detected (no toast, header count unchanged, "
        "no body text match)"
    )


# ---------------------------------------------------------------------------
# Story 3: cart navigation + quantity + clear flow
# ---------------------------------------------------------------------------

@when("the user clicks the cart icon")
def click_cart_icon(page: Page) -> None:
    HomePage(page).go_to_cart()


@then(parsers.parse('the user is navigated to the "{page_name}" page'))
def navigated_to_named_page(page: Page, page_name: str) -> None:
    name_low = page_name.strip().lower()
    if "cart" in name_low:
        cart = CartPage(page)
        cart.wait_for_cart(timeout=20000)
        assert cart.is_on_your_cart_page(), (
            f"Expected to be on the {page_name} page; URL is {page.url}"
        )
        return
    expect(
        page.get_by_role("heading", name=re.compile(re.escape(page_name), re.IGNORECASE)).first
    ).to_be_visible(timeout=15000)


@when(parsers.parse('the user clicks the "{label}" button to increase the item quantity'))
def click_plus_to_increase_quantity(page: Page, label: str) -> None:
    # Story 3 hard-codes label="+", but accept any label so the step is reusable.
    CartPage(page).increase_quantity()


@when(parsers.parse('the user clicks the "{label}" button'))
def click_named_button(page: Page, label: str) -> None:
    label_low = label.strip().lower()
    if label_low == "+":
        CartPage(page).increase_quantity()
        return
    if label_low == "clear my order":
        CartPage(page).click_clear_my_order()
        return
    if label_low == "yes":
        CartPage(page).click_yes_in_popup()
        return
    # Generic fallback — match any visible button or link with that label.
    btn = page.get_by_role("button", name=re.compile(re.escape(label), re.IGNORECASE)).first
    if btn.count() == 0:
        btn = page.locator(
            f"button:has-text('{label}'), a:has-text('{label}')"
        ).first
    expect(btn).to_be_visible(timeout=10000)
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@when(parsers.parse('the user clicks the "{label}" button on the Clear your Cart popup'))
def click_button_on_clear_cart_popup(page: Page, label: str) -> None:
    if label.strip().lower() == "yes":
        CartPage(page).click_yes_in_popup()
        return
    # Generic fallback for any other label inside the popup.
    btn = page.locator(
        f"div[role='dialog'] button:has-text('{label}'), "
        f"div[role='dialog'] a:has-text('{label}'), "
        f".modal.show button:has-text('{label}'), "
        f".modal.show a:has-text('{label}')"
    ).first
    expect(btn).to_be_visible(timeout=10000)
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@then(parsers.parse('the "{popup_name}" popup is displayed'))
def named_popup_displayed(page: Page, popup_name: str) -> None:
    name_low = popup_name.strip().lower()
    if "clear" in name_low and "cart" in name_low:
        assert CartPage(page).clear_cart_popup_visible(timeout=10000), (
            f"Expected the {popup_name} popup to be visible"
        )
        return
    # Generic fallback.
    pattern = re.compile(re.escape(popup_name), re.IGNORECASE)
    expect(
        page.locator(
            f"div[role='dialog']:has-text('{popup_name}'), "
            f".modal.show:has-text('{popup_name}')"
        ).first
    ).to_be_visible(timeout=10000)
    _ = pattern  # silence unused


@then(parsers.parse('the "{page_name}" page is displayed with an empty cart'))
def page_displayed_with_empty_cart(page: Page, page_name: str) -> None:
    cart = CartPage(page)
    assert cart.is_on_your_cart_page(timeout=15000), (
        f"Expected to be on the {page_name} page; URL is {page.url}"
    )
    assert cart.is_empty_cart(timeout=20000), (
        f"Expected the {page_name} to be empty, but cart still has items"
    )
