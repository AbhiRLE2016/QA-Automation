from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from .base_page import BasePage


_DEFAULT_TIMEOUT_MS = 30000


class LoginPage(BasePage):
    """Sign-in screen at /login on the RA Demo Research Gateway."""

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=_DEFAULT_TIMEOUT_MS)

    def dismiss_session_expired_if_present(self) -> bool:
        """Close the 'Session Expired. Please login.' alert if it is showing.
        Returns True if an alert was dismissed."""
        for sel in self.selectors("login_page", "session_expired_close"):
            locator = self.page.locator(sel).first
            try:
                if locator.is_visible(timeout=2000):
                    locator.click(timeout=2000)
                    return True
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return False

    def sign_in_form_visible(self) -> bool:
        for sel in self.selectors("login_page", "sign_in_heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(
                    timeout=_DEFAULT_TIMEOUT_MS
                )
                return True
            except Exception:
                continue
        return False

    def sign_in_heading_text(self) -> str:
        for sel in self.selectors("login_page", "sign_in_heading"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return ""

    def enter_email(self, email: str) -> None:
        self.fill_any(self.selectors("login_page", "email_input"), email,
                      timeout=_DEFAULT_TIMEOUT_MS)

    def enter_password(self, password: str) -> None:
        self.fill_any(self.selectors("login_page", "password_input"), password,
                      timeout=_DEFAULT_TIMEOUT_MS)

    def submit(self) -> None:
        self.click_any(self.selectors("login_page", "sign_in_button"),
                       timeout=_DEFAULT_TIMEOUT_MS)


class MyOrganizationsPage(BasePage):
    """Authenticated landing page (/admin) listing the user's organizations."""

    def wait_until_loaded(self) -> None:
        for sel in self.selectors("my_organizations_page", "page_title"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(
                    timeout=_DEFAULT_TIMEOUT_MS
                )
                return
            except Exception:
                continue
        raise AssertionError(
            f"My Organizations page title not visible. Tried: "
            f"{self.selectors('my_organizations_page', 'page_title')}"
        )

    def page_title_text(self) -> str:
        for sel in self.selectors("my_organizations_page", "page_title"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return ""

    def is_loaded(self) -> bool:
        for sel in self.selectors("my_organizations_page", "page_title"):
            try:
                if self.page.locator(sel).first.is_visible(timeout=2000):
                    return True
            except Exception:
                continue
        return False

    def click_add_new(self) -> None:
        self.click_any(self.selectors("my_organizations_page", "add_new_button"),
                       timeout=_DEFAULT_TIMEOUT_MS)

    def organization_names(self) -> list[str]:
        names: list[str] = []
        for sel in self.selectors("my_organizations_page", "organization_card_title"):
            cards = self.page.locator(sel)
            try:
                count = cards.count()
            except Exception:
                continue
            if count == 0:
                continue
            for i in range(count):
                try:
                    text = (cards.nth(i).inner_text() or "").strip()
                    if text:
                        names.append(text)
                except Exception:
                    continue
            if names:
                return names
        return names

    def find_organization_name(self, name: str) -> str | None:
        for sel in self.selectors("my_organizations_page", "organization_card_title"):
            loc = self.page.locator(f"{sel}", has_text=name).first
            try:
                if loc.is_visible(timeout=_DEFAULT_TIMEOUT_MS):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return None


class CreateOrganizationPage(BasePage):
    """Form page at /addOrganization/Org used to create a new organization."""

    def wait_until_loaded(self) -> None:
        for sel in self.selectors("create_organization_page", "heading"):
            try:
                expect(self.page.locator(sel).first).to_be_visible(
                    timeout=_DEFAULT_TIMEOUT_MS
                )
                return
            except Exception:
                continue
        raise AssertionError(
            f"Create Organization heading not visible. Tried: "
            f"{self.selectors('create_organization_page', 'heading')}"
        )

    def heading_text(self) -> str:
        for sel in self.selectors("create_organization_page", "heading"):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    return (loc.inner_text() or "").strip()
            except Exception:
                continue
        return ""

    def fill_name(self, value: str) -> None:
        self.fill_any(self.selectors("create_organization_page", "name_input"), value,
                      timeout=_DEFAULT_TIMEOUT_MS)

    def fill_description(self, value: str) -> None:
        self.fill_any(self.selectors("create_organization_page", "description_input"),
                      value, timeout=_DEFAULT_TIMEOUT_MS)

    def dismiss_blocking_toasts(self) -> int:
        """Close any ngx-toastr error popups that are intercepting pointer
        events on the Create Organization screen (e.g. a lingering 'Session
        Expired. Please login.' toast). Returns how many toasts were dismissed."""
        dismissed = 0
        for sel in self.selectors("create_organization_page", "toast_close"):
            for _ in range(5):
                loc = self.page.locator(sel).first
                try:
                    if not loc.is_visible(timeout=500):
                        break
                    loc.click(timeout=1500)
                    dismissed += 1
                except Exception:
                    break
        # As a final cleanup, remove any residual toast container via JS so it
        # cannot reappear during the click attempt.
        try:
            self.page.evaluate(
                "() => { document.querySelectorAll('[toast-component], "
                ".ngx-toastr').forEach(el => el.remove()); }"
            )
        except Exception:
            pass
        return dismissed

    def latest_error_toast_text(self) -> str:
        """Return the text of any visible ngx-toastr error popup on this page,
        or '' if none. Used to surface server-side rejections (e.g. 'name exist')
        so the assertion step can report them honestly."""
        for sel in (
            ".ngx-toastr.toast-error",
            "div[toast-component].toast-error",
            "div[toast-component]",
        ):
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=1000):
                    text = (loc.inner_text() or "").strip()
                    if text:
                        return text
            except Exception:
                continue
        return ""

    def click_create(self) -> None:
        self.dismiss_blocking_toasts()
        selectors = self.selectors("create_organization_page", "create_button")
        last_error: Exception | None = None
        for sel in selectors:
            locator = self.page.locator(sel).first
            try:
                expect(locator).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
                try:
                    locator.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                self.dismiss_blocking_toasts()
                try:
                    locator.click(timeout=5000)
                    return
                except Exception:
                    locator.click(timeout=5000, force=True)
                    return
            except Exception as exc:
                last_error = exc
                continue
        raise AssertionError(
            f"Could not click the Create Organization button. "
            f"Tried selectors {selectors}. Last error: {last_error!r}"
        )
