from __future__ import annotations

from playwright.sync_api import Page, expect

from .base_page import BasePage


class DeleteUserPage(BasePage):
    """Page Object for the Research Gateway admin flow that deletes a user
    from the Users page. All Playwright calls live here; step defs only call
    these methods."""

    DEFAULT_TIMEOUT = 15000

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---- Login page ----------------------------------------------------

    def goto_login(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Dismiss the "Session Expired" toast if present so it doesn't intercept clicks
        self._dismiss_toast_if_present()
        expect(self.first_visible(self.selectors("login_page", "email_input"),
                                  timeout=self.DEFAULT_TIMEOUT)).to_be_visible()

    def _dismiss_toast_if_present(self) -> None:
        try:
            for sel in self.selectors("login_page", "toast_close"):
                close = self.page.locator(sel).first
                if close.count() > 0 and close.is_visible():
                    close.click(timeout=2000)
                    break
        except Exception:
            pass

    def type_email(self, email: str) -> None:
        self.fill_any(self.selectors("login_page", "email_input"), email,
                      timeout=self.DEFAULT_TIMEOUT)

    def type_password(self, password: str) -> None:
        self.fill_any(self.selectors("login_page", "password_input"), password,
                      timeout=self.DEFAULT_TIMEOUT)

    def click_sign_in(self) -> None:
        self.click_any(self.selectors("login_page", "sign_in_button"),
                       timeout=self.DEFAULT_TIMEOUT)

    # ---- Organization (post-login landing) -----------------------------

    def wait_for_organization_page(self) -> str:
        """Wait until the post-login Organization page is rendered.
        Returns the heading text actually read."""
        self.page.wait_for_url("**/admin**", timeout=30000)
        self._dismiss_toast_if_present()
        heading = self.first_visible(
            self.selectors("organization_page", "heading_my_organizations"),
            timeout=self.DEFAULT_TIMEOUT,
        )
        return (heading.inner_text() or "").strip()

    def organization_page_url(self) -> str:
        return self.page.url

    # ---- Side navigation menu ------------------------------------------

    def click_menu_top_left(self) -> None:
        self._dismiss_toast_if_present()
        self.click_any(self.selectors("side_nav", "menu_toggle"),
                       timeout=self.DEFAULT_TIMEOUT)

    def click_nav_item(self, label: str) -> None:
        # Use a parameterized selector regardless of the label provided.
        sel = f"nav button.nav-btn:has-text('{label}')"
        target = self.page.locator(sel).first
        expect(target).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        target.click(timeout=self.DEFAULT_TIMEOUT)

    # ---- Users page ----------------------------------------------------

    def wait_for_users_page(self) -> str:
        self.page.wait_for_url("**/users**", timeout=self.DEFAULT_TIMEOUT)
        heading = self.first_visible(
            self.selectors("users_page", "heading_users"),
            timeout=self.DEFAULT_TIMEOUT,
        )
        # The user cards load asynchronously after the heading paints. Wait
        # until at least one user-name span is in the DOM AND visible, or
        # until the timeout — otherwise downstream "user_exists" returns
        # False on a still-empty list.
        try:
            first_name = self.page.locator(
                self.selectors("users_page", "all_user_name_texts")[0]
            ).first
            expect(first_name).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        except Exception:
            pass
        return (heading.inner_text() or "").strip()

    def users_page_url(self) -> str:
        return self.page.url

    def _resolve_displayed_name(self, name: str) -> str | None:
        """The story says 'Jon Kumar' but the UI may render 'Jon kumar' (or
        any case variant). Find a `.user-name-text` whose visible text matches
        case-insensitively and return the exact `title` attribute value used
        in the DOM — that's what our row selector needs."""
        names = self.page.locator(self.selectors("users_page", "all_user_name_texts")[0])
        try:
            count = names.count()
        except Exception:
            count = 0
        target = name.strip().lower()
        for i in range(count):
            n = names.nth(i)
            try:
                txt = (n.inner_text() or "").strip()
                title = (n.get_attribute("title") or "").strip()
            except Exception:
                continue
            if txt.lower() == target or title.lower() == target:
                return title or txt
        return None

    def user_exists(self, name: str) -> bool:
        return self._resolve_displayed_name(name) is not None

    def visible_user_names(self) -> list[str]:
        names = self.page.locator(self.selectors("users_page", "all_user_name_texts")[0])
        out: list[str] = []
        try:
            count = names.count()
        except Exception:
            count = 0
        for i in range(count):
            try:
                txt = (names.nth(i).inner_text() or "").strip()
                if txt:
                    out.append(txt)
            except Exception:
                continue
        return out

    def click_three_dots_for_user(self, name: str) -> str:
        """Click the three-dot Actions trigger on the row whose displayed name
        matches `name` (case-insensitive). Returns the DOM `title` value used."""
        resolved = self._resolve_displayed_name(name)
        if resolved is None:
            raise AssertionError(
                f"User row not found for name {name!r}. "
                f"Visible names: {self.visible_user_names()}"
            )
        tpl = self.selectors("users_page", "user_card_three_dots_tpl")[0]
        sel = tpl.replace("{name}", resolved)
        trigger = self.page.locator(sel).first
        expect(trigger).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        trigger.click(timeout=self.DEFAULT_TIMEOUT)
        return resolved

    def click_menu_delete_user(self, displayed_name: str) -> None:
        tpl = self.selectors("users_page", "menu_option_delete_user_tpl")[0]
        sel = tpl.replace("{name}", displayed_name)
        option = self.page.locator(sel).first
        expect(option).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        option.click(timeout=self.DEFAULT_TIMEOUT)

    # ---- Delete-user confirmation modal --------------------------------

    def wait_for_delete_modal(self) -> dict[str, str]:
        container = self.first_visible(
            self.selectors("delete_user_modal", "container"),
            timeout=self.DEFAULT_TIMEOUT,
        )
        header_text = ""
        body_text = ""
        try:
            header_text = (self.page.locator(
                self.selectors("delete_user_modal", "header")[0]
            ).first.inner_text() or "").strip()
        except Exception:
            pass
        for sel in self.selectors("delete_user_modal", "body_text"):
            try:
                el = self.page.locator(sel).first
                if el.count() > 0:
                    body_text = (el.inner_text() or "").strip()
                    if body_text:
                        break
            except Exception:
                continue
        return {"header": header_text, "body": body_text, "visible": "true"}

    def click_modal_delete_user(self) -> None:
        for sel in self.selectors("delete_user_modal", "confirm_button"):
            btn = self.page.locator(sel).first
            try:
                expect(btn).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
                btn.click(timeout=self.DEFAULT_TIMEOUT)
                return
            except Exception:
                continue
        raise AssertionError(
            "Could not find a visible 'Delete User' confirm button in the modal"
        )

    def wait_for_modal_to_close(self, timeout_ms: int = 10000) -> None:
        try:
            self.page.locator(self.selectors("delete_user_modal", "container")[0]).first.wait_for(
                state="hidden", timeout=timeout_ms
            )
        except Exception:
            pass

    def wait_for_user_to_disappear(self, name: str, timeout_ms: int = 15000) -> bool:
        """Poll the user list until the named row is no longer present."""
        import time
        deadline = time.monotonic() + (timeout_ms / 1000.0)
        while time.monotonic() < deadline:
            if not self.user_exists(name):
                return True
            self.page.wait_for_timeout(500)
        return not self.user_exists(name)
