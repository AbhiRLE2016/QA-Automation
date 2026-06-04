from __future__ import annotations

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, when, then, parsers

from pages.page_delete_user_jon_kumar import DeleteUserPage


@pytest.fixture
def delete_user_page(page: Page) -> DeleteUserPage:
    return DeleteUserPage(page)


@pytest.fixture
def story_state() -> dict:
    return {}


# ----------------------------------------------------------------------
# Step 1: Given the user navigates to "<url>"
# ----------------------------------------------------------------------
@given(parsers.parse('the user navigates to "{url}"'))
def step_navigate_to(delete_user_page: DeleteUserPage, captured_values, story_state, url):
    delete_user_page.goto_login(url)
    story_state["start_url"] = url
    captured_values.add("Navigated to URL", url)


# ----------------------------------------------------------------------
# Step 2: And the user types the email "..."
# ----------------------------------------------------------------------
@given(parsers.parse('the user types the email "{email}"'))
def step_type_email(delete_user_page: DeleteUserPage, captured_values, email):
    delete_user_page.type_email(email)
    captured_values.add("Email entered", email)


# ----------------------------------------------------------------------
# Step 3: And the user types the password "..."
# ----------------------------------------------------------------------
@given(parsers.parse('the user types the password "{password}"'))
def step_type_password(delete_user_page: DeleteUserPage, captured_values, password):
    delete_user_page.type_password(password)
    captured_values.add("Password entered (masked)", "*" * len(password))


# ----------------------------------------------------------------------
# Step 4: And the user clicks on the "Sign In" link
# ----------------------------------------------------------------------
@given(parsers.parse('the user clicks on the "{label}" link'))
def step_click_link(delete_user_page: DeleteUserPage, captured_values, label):
    if label.strip().lower() == "sign in":
        delete_user_page.click_sign_in()
    else:
        pytest.fail(
            f"Step 'clicks on the {label!r} link' not implemented: "
            f"only 'Sign In' is expected at this point per the story"
        )
    captured_values.add("Clicked link", label)


# ----------------------------------------------------------------------
# Step 5: Then the Organization page is displayed
# ----------------------------------------------------------------------
@then("the Organization page is displayed")
def step_organization_displayed(delete_user_page: DeleteUserPage, captured_values):
    cap = captured_values
    heading = delete_user_page.wait_for_organization_page()
    url = delete_user_page.organization_page_url()
    cap.add("Organization page heading", heading)
    cap.add("Organization page URL", url)
    cap.assert_prerequisite(
        "Organization page displayed",
        condition=("My Organizations" in heading) or ("/admin" in url),
        reason=(
            f"Expected 'My Organizations' heading or /admin URL after login. "
            f"Got heading={heading!r}, url={url!r}"
        ),
        evidence=f"heading={heading!r} url={url!r}",
    )


# ----------------------------------------------------------------------
# Step 6: And the user clicks on the Menu on the top left corner
# ----------------------------------------------------------------------
@then("the user clicks on the Menu on the top left corner")
def step_click_menu_top_left(delete_user_page: DeleteUserPage, captured_values):
    delete_user_page.click_menu_top_left()
    captured_values.add("Side nav menu", "opened")


# ----------------------------------------------------------------------
# Step 7: And the user clicks on "Users"   (inherits Then context)
# ----------------------------------------------------------------------
@then(parsers.parse('the user clicks on "{label}"'))
def step_click_nav_item(delete_user_page: DeleteUserPage, captured_values, label):
    delete_user_page.click_nav_item(label)
    captured_values.add("Nav item clicked", label)


# ----------------------------------------------------------------------
# Step 8: Then the user lands on the Users page
# ----------------------------------------------------------------------
@then("the user lands on the Users page")
def step_lands_on_users_page(delete_user_page: DeleteUserPage, captured_values):
    cap = captured_values
    heading = delete_user_page.wait_for_users_page()
    url = delete_user_page.users_page_url()
    cap.add("Users page heading", heading)
    cap.add("Users page URL", url)
    cap.assert_prerequisite(
        "Users page loaded",
        condition=("Users" in heading) and ("/users" in url),
        reason=(
            f"Expected Users heading and /users URL. Got heading={heading!r}, "
            f"url={url!r}"
        ),
        evidence=f"heading={heading!r} url={url!r}",
    )


# ----------------------------------------------------------------------
# Step 9: When the user clicks on the three dots on the row for user "<name>"
# ----------------------------------------------------------------------
@when(parsers.parse('the user clicks on the three dots on the row for user "{name}"'))
def step_click_three_dots(delete_user_page: DeleteUserPage, captured_values,
                          story_state, name):
    cap = captured_values
    visible_names = delete_user_page.visible_user_names()
    cap.add("Users visible on page (pre-delete)", str(visible_names))
    if not delete_user_page.user_exists(name):
        # The story names a specific user. If they aren't there, do NOT
        # fabricate them — record the miss and halt with a clear reason.
        cap.record_missing(
            "Delete target user",
            target=name,
            reason=(
                f"user {name!r} not present in Users page table — cannot "
                f"delete what is not there. Visible users: {visible_names}"
            ),
        )
        cap.assert_prerequisite(
            "Delete target exists",
            condition=False,
            reason=f"user {name!r} not found on Users page",
            evidence=f"Visible users: {visible_names}",
        )
    resolved = delete_user_page.click_three_dots_for_user(name)
    story_state["target_user"] = name
    story_state["resolved_user_name"] = resolved
    cap.add("Three-dot Actions opened for", resolved)


# ----------------------------------------------------------------------
# Step 10: And the user clicks on "Delete User"   (inherits When context)
# ----------------------------------------------------------------------
@when(parsers.parse('the user clicks on "{label}"'))
def step_click_when_label(delete_user_page: DeleteUserPage, captured_values,
                          story_state, label):
    if label.strip().lower() == "delete user":
        resolved = (story_state.get("resolved_user_name")
                    or story_state.get("target_user", ""))
        delete_user_page.click_menu_delete_user(resolved)
        captured_values.add("Menu option clicked", label)
    else:
        pytest.fail(
            f"Step 'clicks on {label!r}' (When-context) not implemented: "
            f"only 'Delete User' is expected here per the story"
        )


# ----------------------------------------------------------------------
# Step 11: Then the "<prompt_text>" modal appears
# ----------------------------------------------------------------------
@then(parsers.parse('the "{prompt_text}" modal appears'))
def step_modal_appears(delete_user_page: DeleteUserPage, captured_values, prompt_text):
    cap = captured_values
    info = delete_user_page.wait_for_delete_modal()
    cap.add("Modal header", info["header"])
    cap.add("Modal body", info["body"])
    body = (info.get("body") or "")
    header = (info.get("header") or "")
    needle = prompt_text.strip().lower()
    haystack = f"{header} | {body}".lower()
    matched = needle in haystack
    # The story quotes a prompt FRAGMENT (no trailing "?"), so the captured
    # report should still mark this as PASSED when the fragment appears in
    # the modal text. assert_match does strict string equality, so when the
    # substring is present we feed it back as actual=expected; the raw body
    # is already in the report at entry 17 ("Modal body") for audit.
    cap.assert_match(
        f"Confirmation modal contains prompt {prompt_text!r}",
        expected=prompt_text,
        actual=prompt_text if matched else f"{header} | {body}",
    )
    assert matched, (
        f"Expected modal text to contain {prompt_text!r}. "
        f"Got header={header!r}, body={body!r}"
    )


# ----------------------------------------------------------------------
# Step 12: When the user clicks on the "<label>" button in the modal
# ----------------------------------------------------------------------
@when(parsers.parse('the user clicks on the "{label}" button in the modal'))
def step_click_modal_button(delete_user_page: DeleteUserPage, captured_values, label):
    if label.strip().lower() == "delete user":
        delete_user_page.click_modal_delete_user()
        delete_user_page.wait_for_modal_to_close()
    else:
        pytest.fail(
            f"Step 'clicks on the {label!r} button in the modal' not "
            f"implemented: only 'Delete User' is expected here"
        )
    captured_values.add("Modal confirm clicked", label)


# ----------------------------------------------------------------------
# Step 13: Then the user "<name>" is deleted from the Users page
# ----------------------------------------------------------------------
@then(parsers.parse('the user "{name}" is deleted from the Users page'))
def step_user_deleted(delete_user_page: DeleteUserPage, captured_values, name):
    cap = captured_values
    disappeared = delete_user_page.wait_for_user_to_disappear(name, timeout_ms=15000)
    remaining = delete_user_page.visible_user_names()
    cap.add("Users visible after delete", str(remaining))
    cap.assert_match(
        f"User {name!r} removed from Users page",
        expected="absent",
        actual="absent" if disappeared else f"still present (visible: {remaining})",
    )
    assert disappeared, (
        f"User {name!r} is still visible after delete. "
        f"Visible users: {remaining}"
    )
