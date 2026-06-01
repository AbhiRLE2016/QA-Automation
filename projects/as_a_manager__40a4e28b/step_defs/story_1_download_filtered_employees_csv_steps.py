from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, when, then, parsers

from pages.page_all_employees_csv import AllEmployeesCsvPage


# ---- fixture: hold state across steps in a single scenario --------------


@pytest.fixture()
def csv_state() -> dict:
    return {
        "downloaded_path": None,
        "csv_headers": [],
        "csv_rows": [],
        "filtered_dept": None,
        "ui_row_count_after_filter": None,
        "pagination_total_after_filter": None,
    }


# ---- Given --------------------------------------------------------------


@given("the user is a manager")
def given_user_is_manager(page: Page, test_data, captured_values):
    base_url = test_data.get("base_url") or "http://localhost:5173/"
    manager_id = test_data.get("manager_id") or "499"
    password = test_data.get("password") or "Mngr@101Pass!"
    expected_name = test_data.get("expected_manager_name") or "Nitin Kumar"

    pom = AllEmployeesCsvPage(page)
    pom.goto_login(base_url)
    pom.login_as_manager(manager_id, password)

    nav_text = pom.welcome_name(expected=expected_name)
    captured_values.add("Logged-in manager id (input)", manager_id)
    captured_values.add("Welcome banner text", nav_text)
    if expected_name not in nav_text:
        raise AssertionError(
            f"Expected to see manager name {expected_name!r} on the dashboard, "
            f"got nav text: {nav_text!r}"
        )
    captured_values.add("Dashboard URL", page.url)


# ---- When ---------------------------------------------------------------


@when(parsers.parse('the user opens the "{page_name}" page'))
def when_user_opens_page(page: Page, page_name: str, captured_values):
    pom = AllEmployeesCsvPage(page)
    if page_name.strip().lower() != "all employees":
        pytest.fail(
            f"Step 'user opens the {page_name!r} page' not implemented: this feature "
            f"only covers the 'All Employees' page."
        )
    pom.open_all_employees()
    captured_values.add("All Employees URL", pom.all_employees_url())
    captured_values.add("Page heading", pom.page_heading_text())


@when(parsers.parse('the user picks the "{department}" department from the filter dropdown'))
def when_user_picks_department(page: Page, department: str, captured_values, csv_state):
    pom = AllEmployeesCsvPage(page)
    banner = pom.pick_department(department)
    csv_state["filtered_dept"] = department
    csv_state["ui_row_count_after_filter"] = pom.visible_row_count()
    csv_state["pagination_total_after_filter"] = pom.pagination_total()
    captured_values.add("Selected department", department)
    captured_values.add("Filter banner after select", banner)
    captured_values.add(
        "Visible rows on filtered page (first page)",
        csv_state["ui_row_count_after_filter"],
    )
    captured_values.add(
        "Pagination total after filter",
        csv_state["pagination_total_after_filter"],
    )


@when(parsers.parse('the user clicks "{label}"'))
def when_user_clicks_label(page: Page, label: str, captured_values, csv_state):
    pom = AllEmployeesCsvPage(page)
    if label.strip().lower() != "download csv":
        pytest.fail(
            f"Step 'user clicks {label!r}' not implemented: this feature only "
            f"covers the 'Download CSV' button."
        )
    saved = pom.click_download_csv()
    csv_state["downloaded_path"] = saved
    captured_values.add("Downloaded file path", str(saved))
    captured_values.add("Downloaded file name", saved.name)


# ---- Then ---------------------------------------------------------------


@then("a CSV file of the filtered employee list is downloaded")
def then_csv_downloaded(captured_values, csv_state):
    path: Path | None = csv_state["downloaded_path"]
    if path is None or not path.exists():
        raise AssertionError(
            f"No CSV was saved. csv_state.downloaded_path = {path!r}"
        )
    size = path.stat().st_size
    captured_values.add("Downloaded CSV size (bytes)", size)
    if size <= 0:
        raise AssertionError(f"Downloaded CSV is empty: {path}")

    pom = AllEmployeesCsvPage  # static helpers
    headers, rows = pom.read_csv(path)
    csv_state["csv_headers"] = headers
    csv_state["csv_rows"] = rows
    captured_values.add("CSV headers", ",".join(headers))
    captured_values.add("CSV row count", len(rows))

    # Every Department cell in the CSV should equal the selected filter.
    dept = csv_state["filtered_dept"]
    for r in rows:
        captured_values.add_component(
            f"CSV row {r.get('Emp ID', '?')} dept",
            1 if (r.get("Department", "").strip() == dept) else 0,
            group="csv_dept_match",
        )

    # Assert: count of rows whose Department == filter == total rows in CSV
    matching = sum(1 for r in rows if r.get("Department", "").strip() == dept)
    captured_values.assert_match(
        f"All CSV rows belong to {dept}",
        expected=len(rows),
        actual=matching,
    )
    assert matching == len(rows), (
        f"CSV contains rows whose Department != {dept!r}. "
        f"matching={matching} total={len(rows)}"
    )


@then("the manager can quickly find a specific employee in the downloaded list")
def then_find_specific_employee(test_data, captured_values, csv_state):
    rows = csv_state["csv_rows"]
    target = (test_data.get("specific_employee") or {}) if isinstance(test_data, dict) else {}
    emp_id = target.get("emp_id") or "503"
    expected_name = target.get("name") or "Aarav Mehta"

    found = AllEmployeesCsvPage.find_employee_in_csv(rows, emp_id)
    captured_values.add("Looked-up employee id", emp_id)
    captured_values.add(
        "Looked-up employee row",
        "" if not found else f"{found.get('Emp ID')} / {found.get('Name')} / {found.get('Department')}",
    )
    if not found:
        raise AssertionError(
            f"Employee id {emp_id!r} not present in downloaded CSV "
            f"(rows={len(rows)})."
        )
    passed = captured_values.assert_match(
        f"Employee {emp_id} name in CSV",
        expected=expected_name,
        actual=found.get("Name"),
    )
    assert passed, (
        f"Employee {emp_id} name mismatch in CSV: "
        f"expected {expected_name!r}, got {found.get('Name')!r}"
    )


@then(
    "the downloaded list is clean and filtered for stakeholders without needing database access"
)
def then_csv_clean_and_filtered(test_data, captured_values, csv_state):
    headers = csv_state["csv_headers"]
    rows = csv_state["csv_rows"]
    dept = csv_state["filtered_dept"]

    # Clean = headers are human-readable business fields, no raw DB internals.
    has_db_internals = AllEmployeesCsvPage.has_db_columns(headers)
    captured_values.add("CSV exposes raw DB columns?", has_db_internals)
    passed_clean = captured_values.assert_match(
        "CSV is clean (no raw DB columns)",
        expected="False",
        actual=str(has_db_internals),
    )
    assert passed_clean, (
        f"CSV looks like a raw DB dump (headers={headers}). "
        f"Stakeholders should not see internal columns."
    )

    # Filtered = total row count == expected count for the selected department.
    expected_count = (
        test_data.get("expected_department_count")
        if isinstance(test_data, dict) and test_data.get("expected_department_count") is not None
        else csv_state.get("pagination_total_after_filter")
    )
    captured_values.add(f"CSV total rows for {dept}", len(rows))
    captured_values.add("Expected total rows from UI pagination", expected_count)
    passed_filtered = captured_values.assert_match(
        f"CSV row count matches UI total for {dept}",
        expected=expected_count,
        actual=len(rows),
    )
    assert passed_filtered, (
        f"CSV row count {len(rows)} does not match expected {expected_count} "
        f"for department {dept!r}."
    )
