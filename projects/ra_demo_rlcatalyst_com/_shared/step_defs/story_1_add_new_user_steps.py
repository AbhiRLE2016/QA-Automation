from __future__ import annotations

import re

from playwright.sync_api import Page
from pytest_bdd import parsers, step

from pages.page_create_organization_relevance_lab import (
    LoginPage,
    MyOrganizationsPage,
)
from pages.page_add_new_user import AddUserModal, MainNav, UsersPage


_LOGIN_URL_PATTERN = re.compile(r"/login", re.IGNORECASE)
_ADMIN_URL_PATTERN = re.compile(r"/admin", re.IGNORECASE)
_USERS_URL_PATTERN = re.compile(r"/users", re.IGNORECASE)
_NAV_TIMEOUT_MS = 30000


def _step(pattern):
    """Use pytest-bdd's universal `step` decorator (type_=None) so the step
    matches regardless of which Gherkin keyword (Given/When/Then/And/But)
    introduces it. `And` inherits the previous step's keyword, so an action
    step that follows a Then becomes a Then in the AST — registering it
    keyword-agnostic lets it resolve in every position the writer places
    it. stacklevel=2 makes the decorator inject the fixture into the caller
    (this module's namespace), not into the wrapper itself."""
    return step(pattern, type_=None)


# ---------------------------------------------------------------------------
# Navigate
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user navigates to "{url}"'))
def navigate_to_url(page: Page, story_context, captured_values, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
    story_context["start_url"] = url
    captured_values.add("Start URL", page.url)


# ---------------------------------------------------------------------------
# Type email and password
# ---------------------------------------------------------------------------

@_step(parsers.parse(
    'the user types the email "{email}" and the password "{password}"'
))
def type_email_and_password(page: Page, captured_values, story_context,
                            email: str, password: str) -> None:
    login = LoginPage(page)
    login.dismiss_session_expired_if_present()
    login.enter_email(email)
    login.enter_password(password)
    captured_values.add("Login email typed", email)
    captured_values.add("Login password typed", "*" * len(password))
    story_context["login_email"] = email


# ---------------------------------------------------------------------------
# Click on the Sign In link
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user clicks on the "{label}" link'))
def click_named_link(page: Page, captured_values, story_context,
                     label: str) -> None:
    if label.strip().lower() == "sign in":
        login = LoginPage(page)
        login.submit()
        try:
            page.wait_for_url(_ADMIN_URL_PATTERN, timeout=_NAV_TIMEOUT_MS)
        except Exception:
            pass
        captured_values.add("URL after Sign In click", page.url)
        captured_values.assert_prerequisite(
            "Sign In succeeded",
            condition=bool(_ADMIN_URL_PATTERN.search(page.url or "")),
            reason=f"expected URL containing '/admin' after Sign In, got {page.url!r}",
            evidence=f"login_email={story_context.get('login_email')!r}",
        )
        story_context["logged_in"] = True
    else:
        raise AssertionError(
            f"Step 'the user clicks on the {label!r} link' is not wired up. "
            f"Only 'Sign In' is supported by this feature's flow."
        )


# ---------------------------------------------------------------------------
# Organization page is displayed
# (The post-login landing page is the 'My Organizations' page.)
# ---------------------------------------------------------------------------

@_step("the Organization page is displayed")
def organization_page_displayed(page: Page, captured_values) -> None:
    my_orgs = MyOrganizationsPage(page)
    my_orgs.wait_until_loaded()
    captured_values.add("Organization page URL", page.url)
    captured_values.add("Organization page heading",
                        my_orgs.page_title_text())
    captured_values.assert_prerequisite(
        "Organization page displayed",
        condition=my_orgs.is_loaded(),
        reason="My Organizations heading was not visible after login",
        evidence=f"current_url={page.url!r}",
    )


# ---------------------------------------------------------------------------
# Click on Menu (top-left) and click "Users"
# ---------------------------------------------------------------------------

@_step(parsers.parse(
    'the user clicks on the Menu on the top left corner and clicks "{nav_label}"'
))
def open_side_nav_and_click(page: Page, captured_values, story_context,
                            nav_label: str) -> None:
    nav = MainNav(page)
    nav.open_side_nav()
    captured_values.add("Side nav opened", "true")
    if nav_label.strip().lower() == "users":
        nav.click_nav_users()
    else:
        raise AssertionError(
            f"Step 'clicks {nav_label!r}' in side nav is not wired up. "
            f"Only 'Users' is supported by this feature's flow."
        )
    try:
        page.wait_for_url(_USERS_URL_PATTERN, timeout=_NAV_TIMEOUT_MS)
    except Exception:
        pass
    captured_values.add(f"URL after clicking {nav_label!r}", page.url)
    story_context["nav_clicked"] = nav_label


# ---------------------------------------------------------------------------
# Lands on the Users page
# ---------------------------------------------------------------------------

@_step("the user lands on the Users page")
def lands_on_users_page(page: Page, captured_values, story_context) -> None:
    users = UsersPage(page)
    users.wait_until_loaded()
    title = users.page_title_text()
    count = users.user_count()
    captured_values.add("Users page URL", page.url)
    captured_values.add("Users page heading", title)
    captured_values.add("Users page count (before add)",
                        "" if count is None else str(count))
    matched = captured_values.assert_match(
        "Landed on Users page (heading contains 'Users')",
        expected="Users",
        actual="Users" if "users" in (title or "").lower() else title,
    )
    assert matched, (
        f"Expected to land on Users page, but heading was {title!r}. "
        f"URL={page.url!r}"
    )
    story_context["users_count_before"] = count


# ---------------------------------------------------------------------------
# Click "Add New" and select "Add New User"
# ---------------------------------------------------------------------------

@_step(parsers.parse(
    'the user clicks on "{trigger}" and the list appears and selects "{option}"'
))
def click_add_new_and_select(page: Page, captured_values, story_context,
                             trigger: str, option: str) -> None:
    if trigger.strip().lower() != "add new":
        raise AssertionError(
            f"Step trigger {trigger!r} is not wired up. "
            f"Only 'Add New' is supported."
        )
    if option.strip().lower() != "add new user":
        raise AssertionError(
            f"Step dropdown option {option!r} is not wired up. "
            f"Only 'Add New User' is supported."
        )
    users = UsersPage(page)
    users.click_add_new()
    captured_values.add("Add New clicked on Users page", "true")
    users.click_add_new_user()
    captured_values.add("Add New User option selected", "true")


# ---------------------------------------------------------------------------
# Add User modal is shown
# ---------------------------------------------------------------------------

@_step(parsers.parse('the "{modal_name}" modal is shown'))
def add_user_modal_shown(page: Page, captured_values, modal_name: str) -> None:
    modal = AddUserModal(page)
    modal.wait_until_open()
    actual = modal.heading_text()
    captured_values.add(f"{modal_name!r} modal heading", actual)
    matched = captured_values.assert_match(
        f"{modal_name!r} modal is shown",
        expected=modal_name,
        actual=actual,
    )
    assert matched, (
        f"Expected the {modal_name!r} modal heading to be {modal_name!r}, "
        f"got {actual!r}"
    )


# ---------------------------------------------------------------------------
# Provide email for new user
# ---------------------------------------------------------------------------

@_step(parsers.parse(
    'the user provides the email "{email}" for the new user'
))
def provide_new_user_email(page: Page, captured_values, story_context,
                           email: str) -> None:
    modal = AddUserModal(page)
    modal.fill_email(email)
    captured_values.add("New user email typed", email)
    story_context["new_user_email"] = email


# ---------------------------------------------------------------------------
# Select Role
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user selects the Role "{role}" from the Role list'))
def select_role(page: Page, captured_values, story_context,
                role: str) -> None:
    modal = AddUserModal(page)
    selected = modal.select_role(role)
    captured_values.add("Role selected", selected or role)
    matched = captured_values.assert_match(
        "Role selected matches expected",
        expected=role,
        actual=selected or role,
    )
    assert matched, (
        f"Expected role {role!r} to be selected, but selected option was "
        f"{selected!r}"
    )
    story_context["new_user_role"] = role


# ---------------------------------------------------------------------------
# Provide First name / Last name
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user provides the First name "{first_name}"'))
def provide_first_name(page: Page, captured_values, story_context,
                       first_name: str) -> None:
    modal = AddUserModal(page)
    modal.fill_first_name(first_name)
    captured_values.add("New user First name typed", first_name)
    story_context["new_user_first_name"] = first_name


@_step(parsers.parse('the user provides the Last name "{last_name}"'))
def provide_last_name(page: Page, captured_values, story_context,
                      last_name: str) -> None:
    modal = AddUserModal(page)
    modal.fill_last_name(last_name)
    captured_values.add("New user Last name typed", last_name)
    story_context["new_user_last_name"] = last_name


# ---------------------------------------------------------------------------
# Select Organization unit
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user selects the Organization unit "{ou}"'))
def select_organization_unit(page: Page, captured_values, story_context,
                             ou: str) -> None:
    modal = AddUserModal(page)
    selected = modal.select_organization_unit(ou)
    captured_values.add("Organizational Unit selected", selected or ou)
    matched = captured_values.assert_match(
        "Organizational Unit selected matches expected",
        expected=ou,
        actual=selected or ou,
    )
    assert matched, (
        f"Expected Organizational Unit {ou!r} to be selected, but selected "
        f"option was {selected!r}"
    )
    story_context["new_user_ou"] = ou


# ---------------------------------------------------------------------------
# Click "Add User" (submit)
# ---------------------------------------------------------------------------

@_step(parsers.parse('the user clicks on "{label}"'))
def click_add_user_submit(page: Page, captured_values, story_context,
                          label: str) -> None:
    if label.strip().lower() != "add user":
        raise AssertionError(
            f"Step 'the user clicks on {label!r}' is not wired up for "
            f"label {label!r}. Only 'Add User' is supported by this flow."
        )
    modal = AddUserModal(page)
    modal.click_add_user()
    captured_values.add("Add User submit clicked", "true")
    # Wait briefly for either the modal to close or an error toast to appear.
    try:
        page.wait_for_function(
            "() => !document.querySelector('div.add-user-dialog')",
            timeout=15000,
        )
    except Exception:
        pass
    server_response = modal.latest_error_toast_text()
    if server_response:
        captured_values.add("Add User — server response", server_response)
    else:
        captured_values.add("Add User — server response",
                            "<no error toast — assumed success>")
    story_context["add_user_server_response"] = server_response


# ---------------------------------------------------------------------------
# User is created and Users page is shown
# ---------------------------------------------------------------------------

@_step("the user is created and the Users page is shown")
def user_created_users_page_shown(page: Page, captured_values,
                                  story_context) -> None:
    modal = AddUserModal(page)
    if modal.is_open():
        captured_values.add(
            "Add User modal still open after submit",
            story_context.get("add_user_server_response") or "<no toast text>",
        )
    users = UsersPage(page)
    users.wait_until_loaded()
    captured_values.add("Users page URL (post-add)", page.url)
    count_after = users.user_count()
    count_before = story_context.get("users_count_before")
    captured_values.add("Users page count (after add)",
                        "" if count_after is None else str(count_after))

    email = story_context.get("new_user_email", "")
    email_present = users.has_user_email(email) if email else False
    captured_values.add(
        f"New user {email!r} found on Users page",
        "true" if email_present else "false",
    )

    count_incremented = (
        isinstance(count_before, int)
        and isinstance(count_after, int)
        and count_after >= count_before + 1
    )
    captured_values.add(
        "User count increased after add",
        f"before={count_before} after={count_after} -> "
        f"{'yes' if count_incremented else 'no'}",
    )

    on_users_page = bool(_USERS_URL_PATTERN.search(page.url or ""))

    # State-aware outcome — judge by the site's ACTUAL response this run. The
    # site reuses ONE toast for success AND error, so classify by content:
    #   • "…created successfully" / count rose by one → created this run → PASS
    #   • "…already exists" / row already in the list  → already present  → PASS
    #   • any other error toast                        → add rejected     → FAIL
    #   • no toast and not present                     → add didn't take  → FAIL
    toast = (story_context.get("add_user_server_response") or "").strip()
    tl = toast.lower()
    created_msg = "success" in tl
    already_msg = ("exist" in tl) or ("already" in tl)
    error_msg = bool(toast) and not created_msg and not already_msg

    # The story step is "the user IS CREATED" — so it PASSES only when the user
    # was genuinely created on THIS run. Any state where creation didn't happen
    # (already exists, other rejection, or no creation evidence) is a FAIL, with
    # the site's own message as the reason and the error-toast screenshot.
    if count_incremented or created_msg:
        captured_values.add(
            "Add User — outcome",
            f"created on this run ({toast or 'user count incremented'})",
        )
        captured_values.assert_match(
            "User created on this run", expected="created", actual="created",
        )
    elif already_msg:
        captured_values.add(
            "Add User — outcome",
            f"user already exists — NOT created on this run ({toast})",
        )
        matched = captured_values.assert_match(
            "User created on this run",
            expected="created",
            actual="already exists — not created this run",
        )
        assert matched, (
            f"User was NOT created — the site reports it already exists: {toast!r}"
        )
    elif error_msg:
        captured_values.add("Add User — outcome", f"add rejected: {toast}")
        matched = captured_values.assert_match(
            "User created on this run",
            expected="created",
            actual=f"rejected: {toast}",
        )
        assert matched, f"Add User was rejected by the backend: {toast!r}"
    else:
        matched = captured_values.assert_match(
            "User created on this run",
            expected="created",
            actual=("already present (not created this run)" if email_present
                    else "not created and not present"),
        )
        assert matched, (
            f"User was not created on this run (email_present={email_present}, "
            f"count_before={count_before}, count_after={count_after}, "
            f"server_response={toast or '<none>'})"
        )
