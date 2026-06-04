from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


_DEFAULT_TIMEOUT_MS = 30000


class MainNav(BasePage):
    """Top-level navigation shared across authenticated pages (hamburger menu)."""

    def open_side_nav(self) -> None:
        self.click_any(self.selectors("main_nav", "hamburger_button"),
                       timeout=_DEFAULT_TIMEOUT_MS)

    def click_nav_users(self) -> None:
        self.click_any(self.selectors("main_nav", "nav_item_users"),
                       timeout=_DEFAULT_TIMEOUT_MS)


class UsersPage(BasePage):
    """Listing page at /users."""

    def wait_until_loaded(self) -> None:
        for sel in self.selectors("users_page", "page_title"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(
                    timeout=_DEFAULT_TIMEOUT_MS
                )
                return
            except Exception:
                continue
        raise AssertionError(
            f"Users page title not visible. Tried: "
            f"{self.selectors('users_page', 'page_title')}"
        )

    def page_title_text(self) -> str:
        for sel in self.selectors("users_page", "page_title"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return ""

    def user_count(self) -> int | None:
        for sel in self.selectors("users_page", "user_count_heading"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    raw = (loc.inner_text() or "").strip()
                    digits = "".join(ch for ch in raw if ch.isdigit())
                    return int(digits) if digits else None
            except Exception:
                continue
        return None

    def click_add_new(self) -> None:
        self.click_any(self.selectors("users_page", "add_new_button"),
                       timeout=_DEFAULT_TIMEOUT_MS)

    def click_add_new_user(self) -> None:
        self.click_any(self.selectors("users_page", "add_new_user_option"),
                       timeout=_DEFAULT_TIMEOUT_MS)

    def has_user_email(self, email: str) -> bool:
        # Restrict to descendants that actually look like user-list rows so a
        # stray copy of the email elsewhere on the page (e.g. an invite-tooltip
        # in a still-rendered modal, or a toast) does not produce a false
        # positive.
        scopes = [
            "div.users-list",
            "div.user-card",
            "div[class*='user-card']",
            "div[class*='user-list']",
        ]
        for scope in scopes:
            try:
                loc = self.page.locator(scope).locator(f"text={email}").first
                if loc.is_visible(timeout=2000):
                    return True
            except Exception:
                continue
        return False


class AddUserModal(BasePage):
    """Modal dialog opened by Users page → Add New → Add New User."""

    def wait_until_open(self) -> None:
        for sel in self.selectors("add_user_modal", "heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(
                    timeout=_DEFAULT_TIMEOUT_MS
                )
                return
            except Exception:
                continue
        raise AssertionError(
            f"Add User modal heading not visible. Tried: "
            f"{self.selectors('add_user_modal', 'heading')}"
        )

    def heading_text(self) -> str:
        for sel in self.selectors("add_user_modal", "heading"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return ""

    def is_open(self) -> bool:
        for sel in self.selectors("add_user_modal", "heading"):
            try:
                if self.page.locator(sel).first.is_visible(timeout=2000):
                    return True
            except Exception:
                continue
        return False

    def fill_email(self, email: str) -> None:
        self.fill_any(self.selectors("add_user_modal", "email_input"), email,
                      timeout=_DEFAULT_TIMEOUT_MS)

    def select_role(self, role: str) -> str:
        for sel in self.selectors("add_user_modal", "role_select"):
            loc = self.page.locator(sel).first
            try:
                expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
                loc.select_option(label=role, timeout=_DEFAULT_TIMEOUT_MS)
                return self._selected_text(loc)
            except Exception:
                continue
        raise AssertionError(
            f"Could not select role {role!r}. Tried: "
            f"{self.selectors('add_user_modal', 'role_select')}"
        )

    def fill_first_name(self, value: str) -> None:
        self.fill_any(self.selectors("add_user_modal", "first_name_input"),
                      value, timeout=_DEFAULT_TIMEOUT_MS)

    def fill_last_name(self, value: str) -> None:
        self.fill_any(self.selectors("add_user_modal", "last_name_input"),
                      value, timeout=_DEFAULT_TIMEOUT_MS)

    def select_organization_unit(self, ou: str) -> str:
        for sel in self.selectors("add_user_modal", "organization_unit_select"):
            loc = self.page.locator(sel).first
            try:
                expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
                try:
                    loc.select_option(label=ou, timeout=_DEFAULT_TIMEOUT_MS)
                except Exception:
                    # Try case-insensitive fallback by matching <option> texts
                    options = loc.locator("option").all_inner_texts()
                    match = next(
                        (o for o in options if o.strip().lower() == ou.strip().lower()),
                        None,
                    )
                    if not match:
                        raise
                    loc.select_option(label=match, timeout=_DEFAULT_TIMEOUT_MS)
                return self._selected_text(loc)
            except Exception:
                continue
        raise AssertionError(
            f"Could not select Organizational Unit {ou!r}. Tried: "
            f"{self.selectors('add_user_modal', 'organization_unit_select')}"
        )

    def click_add_user(self) -> None:
        selectors = self.selectors("add_user_modal", "add_user_submit")
        last_error: Exception | None = None
        for sel in selectors:
            loc = self.page.locator(sel).first
            try:
                expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
                try:
                    loc.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                try:
                    loc.click(timeout=5000)
                    return
                except Exception:
                    loc.click(timeout=5000, force=True)
                    return
            except Exception as exc:
                last_error = exc
                continue
        raise AssertionError(
            f"Could not click the Add User submit button. "
            f"Tried selectors {selectors}. Last error: {last_error!r}"
        )

    def latest_error_toast_text(self) -> str:
        for sel in self.selectors("add_user_modal", "error_toast"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=1500):
                    text = (loc.inner_text() or "").strip()
                    if text:
                        return text
            except Exception:
                continue
        return ""

    @staticmethod
    def _selected_text(select_locator) -> str:
        try:
            return (select_locator.locator("option:checked").first.inner_text()
                    or "").strip()
        except Exception:
            return ""
