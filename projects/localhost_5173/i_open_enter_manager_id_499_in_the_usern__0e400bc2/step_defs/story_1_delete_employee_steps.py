from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, when, then, parsers

from pages.page_delete_employee import DeleteEmployeePage


# ---------------------------------------------------------------------------
# Per-scenario state shared between steps.
# ---------------------------------------------------------------------------

@pytest.fixture()
def delete_state() -> dict:
    return {
        "pom": None,
        "base_url": "",
        "target_employee": "",
        "target_emp_id": "",
        "filter_selected_text": "",
        "deleted_at_least_once": False,
    }


# NOTE: a previous Claude run added an autouse fixture here that POSTed to
# /api/employees to recreate Priya Sharma before every test, "so a second
# run of the test would find her again". That is FABRICATED SETUP and is
# explicitly banned (see the NO-FABRICATION rule in FRAMEWORK_PROMPT). The
# fixture has been removed. If Priya isn't present on the live app, the
# test correctly reports "not found" via cap.record_missing() and stops —
# that IS the result, and it's truthful.


def _csv_record_for(test_data, name: str) -> dict:
    """Look up `name` in user_data.json (loaded via the test_data fixture).
    Returns the dict or an empty dict so step defs can still capture rows
    when the data file is sparse."""
    if isinstance(test_data, list):
        for rec in test_data:
            if str(rec.get("Name", "")).strip().lower() == name.strip().lower():
                return rec
    return {}


def _normalize(s: str) -> str:
    """Quote-tolerant comparison helper: collapse curly/straight, double/single
    quotes to a single ASCII apostrophe so the feature's 'Priya Sharma' matches
    the app's "Priya Sharma"."""
    if s is None:
        return ""
    return (
        s.replace("“", "'").replace("”", "'")
         .replace("‘", "'").replace("’", "'")
         .replace('"', "'")
         .strip()
    )


# ===========================================================================
# Given / When / Then
# ===========================================================================

@given(parsers.parse('the user opens "{url}"'))
def given_user_opens(url: str, page: Page, delete_state: dict, captured_values) -> None:
    pom = DeleteEmployeePage(page)
    pom.open(url)
    delete_state["pom"] = pom
    delete_state["base_url"] = url
    captured_values.add("Opened URL", page.url)
    captured_values.assert_prerequisite(
        "App reachable at base URL",
        condition="localhost:5173" in (page.url or "") or page.url.startswith(url),
        reason=f"page.url={page.url!r} after navigating to {url!r}",
    )


@when(parsers.parse('the user enters Manager ID "{manager_id}" in the username field'))
def when_user_enters_manager_id(manager_id: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    pom.fill_manager_id(manager_id)
    delete_state["manager_id"] = manager_id
    captured_values.add("Manager ID entered", manager_id)


@when(parsers.parse('the user enters "{password}" in the password field'))
def when_user_enters_password(password: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    pom.fill_password(password)
    captured_values.add("Password entered (masked)", "*" * len(password))


@when(parsers.parse('the user clicks the "{button_label}" button'))
def when_user_clicks_button(button_label: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    label = button_label.strip().lower()
    if label == "login":
        pom.click_login()
    elif label == "delete employee":
        # The dashboard's "Delete Employee" action is the toolbar Bulk Delete
        # button — it activates once a row checkbox is ticked and shows
        # "Bulk Delete (N)". Verify it is enabled, capture its label, then click.
        assert pom.bulk_delete_is_enabled(), (
            "Delete Employee button is not enabled — no row appears to be selected"
        )
        actual_label = pom.bulk_delete_button_text()
        captured_values.add("Delete-employee toolbar label", actual_label)
        pom.click_delete_employee()
        delete_state["delete_clicked"] = True
    elif label == "view all employees":
        pom.click_view_all_employees()
    else:
        pytest.fail(f"No handler for clicking the {button_label!r} button.")
    captured_values.add("Clicked button", button_label)


@then(parsers.parse('the dashboard is shown at "{path}"'))
def then_dashboard_shown(path: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    pom.wait_for_url_endswith(path, timeout=15000)
    actual_url = pom.current_url()
    captured_values.add("Dashboard URL", actual_url)
    assert captured_values.assert_match(
        "Dashboard URL ends with expected path",
        expected=path,
        actual=path if actual_url.endswith(path) else actual_url,
    ), f"Expected URL to end with {path!r}, got {actual_url!r}"


@then(parsers.parse('the "{tab_label}" tab is selected'))
def then_tab_is_selected(tab_label: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    # The dashboard renders the Manage Employees panel by default after login,
    # but we click the tab explicitly to make the step deterministic.
    if tab_label.strip().lower() == "manage employees":
        pom.click_manage_employees_tab()
        ok = pom.manage_employees_tab_is_selected()
        captured_values.add("Manage Employees tab active", "yes" if ok else "no")
        assert captured_values.assert_match(
            "Manage Employees tab selected",
            expected="yes",
            actual="yes" if ok else "no",
        ), "Manage Employees tab does not appear to be selected"
    else:
        pytest.fail(f"No handler for asserting tab {tab_label!r} is selected.")


@when(parsers.parse('the user finds the row for "{name}" in the employees table'))
def when_user_finds_row(name: str, delete_state: dict, captured_values, test_data) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    delete_state["target_employee"] = name
    assert pom.employee_row_exists(name), (
        f"Could not find a row for {name!r} on the Manage Employees table"
    )
    row = pom.find_employee_row(name)
    # Capture the row's visible cells for the report.
    cell_texts = row.locator("td").all_inner_texts()
    captured_values.add(f"Row found on dashboard for {name}",
                        " | ".join(t.strip() for t in cell_texts))
    # Cross-check against user_data.json so the report shows what the CSV
    # said about this employee at the time of deletion.
    csv_record = _csv_record_for(test_data, name)
    if csv_record:
        for key in ("Emp ID", "Department", "Project", "Status"):
            if csv_record.get(key):
                captured_values.add(f"CSV {key} for {name}", csv_record[key])


@when("the user selects that row")
def when_user_selects_row(delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    name = delete_state["target_employee"]
    emp_id = pom.select_employee_row(name)
    delete_state["target_emp_id"] = emp_id
    captured_values.add(f"Row selected (Name / Emp ID)", f"{name} / {emp_id}")
    # The Delete Employee (Bulk Delete) toolbar button should now reflect the
    # selection — capture its label so the report shows the wire-up worked.
    captured_values.add("Delete Employee button label after select",
                        pom.bulk_delete_button_text())


@when("the user confirms the deletion when prompted")
def when_user_confirms_deletion(delete_state: dict, captured_values, dialog_recorder) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    # The app first shows an in-page modal; clicking its Delete N button then
    # fires a window.alert() to summarise the result (auto-accepted by
    # dialog_recorder). Both prompts together = "the deletion is confirmed".
    assert pom.confirm_modal_is_open(), (
        "Confirmation modal did not appear after clicking the Delete Employee button"
    )
    modal_msg = pom.confirm_modal_message_text()
    captured_values.add("Confirm modal message", modal_msg)
    pom.confirm_delete()
    # Wait briefly for the alert dialog to fire, then capture its text.
    try:
        pom.page.wait_for_function(
            "() => !document.querySelector(\"[data-testid='bulk-delete-modal-confirm-button']\")",
            timeout=8000,
        )
    except Exception:
        pass
    if dialog_recorder.last:
        captured_values.add("Post-delete alert text", dialog_recorder.last)
        # Sanity check: the alert should report at least 1 deletion.
        m = re.search(r"(\d+)\s+deleted", dialog_recorder.last)
        if m:
            captured_values.add("Deletions reported by app", m.group(1))
            assert int(m.group(1)) >= 1, (
                f"App reported 0 deletions: {dialog_recorder.last!r}"
            )
    delete_state["deleted_at_least_once"] = True
    # And the row should now be gone from the dashboard table.
    name = delete_state["target_employee"]
    still_there = pom.employee_row_exists(name)
    captured_values.add(f"{name} still on dashboard table after delete",
                        "yes" if still_there else "no")
    assert captured_values.assert_match(
        "Row removed from dashboard table",
        expected="no",
        actual="yes" if still_there else "no",
    ), f"{name!r} is still visible on the Manage Employees table after delete"


@then(parsers.parse('the user is navigated to "{path}"'))
def then_user_navigated_to(path: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    pom.wait_for_url_endswith(path, timeout=15000)
    pom.expect_directory_loaded()
    actual_url = pom.current_url()
    captured_values.add("All Employees URL", actual_url)
    assert captured_values.assert_match(
        "All Employees URL ends with expected path",
        expected=path,
        actual=path if actual_url.endswith(path) else actual_url,
    ), f"Expected URL to end with {path!r}, got {actual_url!r}"


@when(parsers.parse('the user sets the filter dropdown to "{filter_label}"'))
def when_user_sets_filter(filter_label: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    selected_text = pom.set_filter(filter_label)
    delete_state["filter_selected_text"] = selected_text
    captured_values.add("Filter selected", selected_text)
    assert captured_values.assert_match(
        "Filter selection starts with requested label",
        expected=filter_label.lower(),
        actual=selected_text[: len(filter_label)].lower(),
    ), f"Filter set to {selected_text!r}, expected to start with {filter_label!r}"


@when(parsers.parse('the user types "{value}" into the search box'))
def when_user_types_search(value: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    pom.type_search(value)
    actual = pom.search_box_value()
    captured_values.add("Search box value", actual)
    assert captured_values.assert_match(
        "Search box contents",
        expected=value,
        actual=actual,
    ), f"Search box has {actual!r}, expected {value!r}"


@then(parsers.parse('the table shows the "{expected_message}" message'))
def then_table_shows_message(expected_message: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    # The app may need a tick after typing for the empty state to appear.
    pom.page.wait_for_timeout(300)
    actual = pom.empty_state_message()
    captured_values.add("Empty-state message in table", actual)
    # Quote-tolerant match: the feature wraps the name in single quotes, but
    # the live app uses double quotes. Normalise both before comparison.
    norm_actual = _normalize(actual)
    norm_expected = _normalize(expected_message)
    passed = norm_expected.lower() in norm_actual.lower()
    captured_values.assert_match(
        "Empty-state message matches (quote-tolerant)",
        expected=norm_expected,
        actual=norm_actual if passed else f"NO MATCH ({norm_actual})",
    )
    assert passed, (
        f"Empty-state message mismatch.\n  expected (normalised): {norm_expected!r}\n"
        f"  actual   (normalised): {norm_actual!r}"
    )


@then(parsers.parse('the employee "{name}" is not found in the record'))
def then_employee_not_found(name: str, delete_state: dict, captured_values) -> None:
    pom: DeleteEmployeePage = delete_state["pom"]
    found = pom.employee_appears_in_table(name)
    # The empty-state row counts as a visible <tr>, so we only check
    # that no real employee row matches the deleted name.
    captured_values.add(f"{name} appears in All Employees table", "yes" if found else "no")
    assert captured_values.assert_match(
        f"{name} absent from All Employees record",
        expected="no",
        actual="yes" if found else "no",
    ), f"{name!r} is still present in the All Employees table after the delete"


# ===========================================================================
# DELTA additions for the new "delete Priya Sharma end to end" user story.
# The feature wording for three lines doesn't match the existing matchers
# above, so append When-flavoured matchers (the .feature uses `And ...` and
# pytest-bdd allows reuse of When step defs for And steps).
# ===========================================================================

@when(parsers.parse('the user is on the dashboard at "{path}"'))
def when_user_on_dashboard_at(path: str, delete_state: dict, captured_values) -> None:
    """Feature: `And the user is on the dashboard at "/dashboard/499"`.
    Wait until the URL ends with `path` (the app navigates there after the
    earlier 'View All Employees' click eventually settles back on the
    dashboard) and capture the URL for the report."""
    pom: DeleteEmployeePage = delete_state["pom"]
    actual_url = pom.current_url()
    if not actual_url.endswith(path):
        # The dashboard may not be visible yet — navigate to it explicitly so
        # the next step ("Manage Employees" tab) has a deterministic landing.
        base = delete_state.get("base_url") or "http://localhost:5173/"
        target = base.rstrip("/") + path
        pom.page.goto(target, wait_until="domcontentloaded", timeout=15000)
    pom.wait_for_url_endswith(path, timeout=15000)
    actual_url = pom.current_url()
    captured_values.add("Dashboard URL", actual_url)
    assert captured_values.assert_match(
        "Dashboard URL ends with expected path",
        expected=path,
        actual=path if actual_url.endswith(path) else actual_url,
    ), f"Expected URL to end with {path!r}, got {actual_url!r}"


@when(parsers.parse('the user makes sure the "{tab_label}" tab is selected'))
def when_user_makes_sure_tab_selected(tab_label: str, delete_state: dict,
                                     captured_values) -> None:
    """Feature: `And the user makes sure the "Manage Employees" tab is selected`.
    Click the tab and assert it became active."""
    pom: DeleteEmployeePage = delete_state["pom"]
    if tab_label.strip().lower() == "manage employees":
        pom.click_manage_employees_tab()
        ok = pom.manage_employees_tab_is_selected()
        captured_values.add("Manage Employees tab active", "yes" if ok else "no")
        assert captured_values.assert_match(
            "Manage Employees tab selected",
            expected="yes",
            actual="yes" if ok else "no",
        ), "Manage Employees tab does not appear to be selected"
    else:
        pytest.fail(f"No handler for asserting tab {tab_label!r} is selected.")


@then(parsers.parse(
    'the employee "{name}" is not found in the record confirming that the delete '
    'went through end to end'
))
def then_employee_not_found_end_to_end(name: str, delete_state: dict,
                                       captured_values) -> None:
    """Feature line 23 has trailing 'confirming that the delete went through
    end to end' wording. Combine the empty-state check with the in-scenario
    delete flag so the report shows both signals confirmed the deletion."""
    pom: DeleteEmployeePage = delete_state["pom"]
    found = pom.employee_appears_in_table(name)
    deleted_clicked = bool(delete_state.get("deleted_at_least_once"))
    captured_values.add(f"{name} appears in All Employees table",
                        "yes" if found else "no")
    captured_values.add("Delete action recorded in scenario",
                        "yes" if deleted_clicked else "no")
    end_to_end_ok = (not found) and deleted_clicked
    captured_values.add("Delete went through end to end",
                        "yes" if end_to_end_ok else "no")
    assert captured_values.assert_match(
        f"{name} absent from All Employees record (end-to-end)",
        expected="yes",
        actual="yes" if end_to_end_ok else "no",
    ), (
        f"End-to-end delete check failed for {name!r}: "
        f"clicked={deleted_clicked}, absent_in_table={not found}"
    )
