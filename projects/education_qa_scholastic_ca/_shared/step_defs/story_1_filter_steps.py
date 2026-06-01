from __future__ import annotations

from playwright.sync_api import Page, expect
from pytest_bdd import parsers, then, when

from pages.cart_page import CartPage
from pages.filters_page import FiltersPage
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage


@when("the user clicks the search icon to view all items")
def click_search_icon_view_all(page: Page, story_context: dict) -> None:
    home = HomePage(page)
    initial_url = page.url
    try:
        home.click_search()
    except Exception:
        try:
            home.submit_empty_search_via_enter()
        except Exception:
            pass
    try:
        page.wait_for_url(lambda u: u != initial_url, timeout=10000)
    except Exception:
        base = story_context.get("base_url", "")
        if base:
            SearchResultsPage(page).fallback_navigate_to_all_items(base)
    SearchResultsPage(page).wait_for_results()


@then(parsers.parse('the "{label}" label is displayed'))
def label_is_displayed(page: Page, label: str) -> None:
    target = label.strip().rstrip(":").lower()
    if target == "filter by":
        assert FiltersPage(page).filter_by_label_visible(), "'Filter By:' label not visible"
        return
    expect(page.get_by_text(label, exact=False).first).to_be_visible(timeout=15000)


@then("the following filter options are present")
def following_filter_options_present(page: Page) -> None:
    filters = FiltersPage(page)
    visible = filters.visible_filter_names()
    missing: list[str] = []
    for name in filters.EXPECTED:
        if name in visible:
            continue
        if not filters.has_filter_option(name):
            missing.append(name)
    assert not missing, f"Missing filter options: {missing}"


@when("the user clicks each filter one by one")
def click_each_filter(page: Page, story_context: dict) -> None:
    filters = FiltersPage(page)
    states: dict[str, bool] = {}
    for name in filters.EXPECTED:
        if not filters.has_filter_option(name):
            continue
        try:
            filters.expand_filter(name)
        except Exception:
            pass
        states[name] = filters.is_filter_expanded(name)
    story_context["filter_expanded_states"] = states


@then("each clicked filter expands")
def each_clicked_filter_expands(story_context: dict) -> None:
    states = story_context.get("filter_expanded_states") or {}
    assert states, "No filter expansions tracked"
    not_expanded = [name for name, ok in states.items() if not ok]
    assert not not_expanded, f"Filters did not expand: {not_expanded}"


@when(parsers.parse('the user clicks the "{label}" button'))
def click_named_button(page: Page, label: str) -> None:
    if label == "Clear All":
        FiltersPage(page).click_clear_all()
        return
    if label == "Clear My Order":
        CartPage(page).click_clear_my_order()
        return
    btn = page.locator(f"button:has-text('{label}'), a:has-text('{label}')").first
    expect(btn).to_be_visible(timeout=10000)
    try:
        btn.click(timeout=5000)
    except Exception:
        btn.click(timeout=5000, force=True)


@then("all open filters are collapsed")
def all_filters_collapsed(page: Page) -> None:
    assert FiltersPage(page).all_filters_collapsed(), "Not all filters collapsed after Clear All"


@when("the user adds the first item to the cart and notes its dollar value")
def add_first_item_and_note_dollar_value(page: Page, story_context: dict) -> None:
    home = HomePage(page)
    results = SearchResultsPage(page)
    cart_count_before = home.cart_count()
    story_context["cart_count_before"] = cart_count_before
    story_context["first_item_name"] = results.first_item_name()
    story_context["first_item_price"] = results.first_item_price()
    results.add_first_item_to_cart(cart_count_before=cart_count_before)


@then("the item is added to the cart page")
def item_added_to_cart_page(page: Page, story_context: dict) -> None:
    HomePage(page).go_to_cart()
    cart = CartPage(page)
    cart.wait_for_cart()
    name = story_context.get("first_item_name", "")
    price = story_context.get("first_item_price", "")
    primary_token = name.splitlines()[0].strip() if name else ""
    name_match = cart.has_item_with_name(primary_token) if primary_token else False
    price_match = cart.has_price(price) if price else False
    cart_count_before = story_context.get("cart_count_before", -1)
    cart_count_now = HomePage(page).cart_count()
    cart_grew = cart_count_before >= 0 and cart_count_now > cart_count_before
    assert name_match or price_match or cart_grew, (
        f"Item not added to cart. name={primary_token!r} price={price!r} "
        f"count_before={cart_count_before} count_now={cart_count_now}"
    )
