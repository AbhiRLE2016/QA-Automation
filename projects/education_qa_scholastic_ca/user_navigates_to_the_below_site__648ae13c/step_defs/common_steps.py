"""Shared Background steps."""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Page
from pytest_bdd import given, parsers

from pages.home_page import HomePage


@given(parsers.parse('user navigates to "{url}"'))
def navigate(page: Page, story_context: dict, url: str) -> None:
    home = HomePage(page)
    home.navigate(url)
    parsed = urlparse(url)
    story_context["base_url"] = f"{parsed.scheme}://{parsed.netloc}"
    story_context["start_url"] = url


@given(parsers.parse(
    'the cookie banner is dismissed by clicking "{label}" if displayed'
))
def dismiss_cookies(page: Page, label: str) -> None:
    # `label` is informational ("Accept All Cookies"); HomePage knows the
    # actual button labels it accepts.
    HomePage(page).accept_cookies_if_present(timeout=8000)
