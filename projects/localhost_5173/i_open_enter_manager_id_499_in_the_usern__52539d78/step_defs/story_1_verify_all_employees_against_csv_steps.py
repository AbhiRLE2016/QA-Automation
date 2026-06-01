from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, when, then, parsers

from pages.page_all_employees_directory_walk import AllEmployeesDirectoryWalkPage

# Reuse the existing shared phrases from story_1_delete_employee_steps.py:
#   * Given the user opens "{url}"
#   * When the user enters "{password}" in the password field
#   * When the user clicks the "{button_label}" button   (handles "Login")
# Those step defs create a DeleteEmployeePage in delete_state["pom"]; the new
# steps below piggy-back on that POM where the actions are 1:1 (fill_manager_id,
# set_filter, search box ops, view_all_employees click) and ALSO lazily build
# an AllEmployeesDirectoryWalkPage on the same Playwright `page` so the
# pagination + row-reading helpers (read_visible_rows, parse_page_indicator,
# click_next_page, click_prev_page, dashboard_is_displayed,
# employees_table_is_displayed) are available without duplicating logic.


@pytest.fixture()
def verify_state() -> dict:
    return {
        "directory_pom": None,         # AllEmployeesDirectoryWalkPage
        "manager_id": "",
        "filter_selected_text": "",
        "csv_index_by_id": {},
        "csv_index_by_name": {},
        "csv_total": 0,
        "ticked_ids": set(),
        "page_history": [],            # list[list[row_dict]] one entry per page walked
        "pages_walked": [],
        "missing_csv_names": [],
        "extras_on_screen": [],
    }


def _build_csv_index(test_data, state: dict) -> None:
    records = test_data if isinstance(test_data, list) else []
    by_id, by_name = {}, {}
    for rec in records:
        emp_id = str(rec.get("Emp ID", "")).strip()
        name = str(rec.get("Name", "")).strip()
        if emp_id:
            by_id[emp_id] = rec
        if name:
            by_name.setdefault(name.lower(), []).append(rec)
    state["csv_index_by_id"] = by_id
    state["csv_index_by_name"] = by_name
    state["csv_total"] = len(records)


def _directory_pom(page: Page, verify_state: dict) -> AllEmployeesDirectoryWalkPage:
    pom = verify_state.get("directory_pom")
    if pom is None:
        pom = AllEmployeesDirectoryWalkPage(page)
        verify_state["directory_pom"] = pom
    return pom


def _reconcile_current_page(pom: AllEmployeesDirectoryWalkPage,
                            verify_state: dict, cap) -> list[dict]:
    rows = pom.read_visible_rows()
    verify_state["page_history"].append(rows)
    page_no, _ = pom.parse_page_indicator()
    for idx, row in enumerate(rows, start=1):
        emp_id = (row.get("Emp ID") or "").strip()
        name = (row.get("Name") or "").strip()
        csv_record = verify_state["csv_index_by_id"].get(emp_id)
        in_csv = bool(csv_record) and (
            (csv_record.get("Name") or "").strip().lower() == name.lower()
        )
        cap.add(
            f"P{page_no} row {idx}: {name} ({emp_id})",
            "in CSV" if in_csv else "NOT in CSV",
        )
        if in_csv and emp_id:
            verify_state["ticked_ids"].add(emp_id)
        elif name:
            verify_state["extras_on_screen"].append(f"{name} ({emp_id})")
    return rows


# ===========================================================================
# Only NEW phrases — anything already defined in story_1_delete_employee_steps
# (e.g. Given the user opens "...", password fill, click "Login" button) is
# intentionally NOT redefined here so pytest-bdd reuses the existing handler.
# ===========================================================================


@when(parsers.parse('the user enters "{value}" in the username field'))
def when_enters_value_in_username(value: str, page: Page, verify_state: dict,
                                  delete_state: dict, captured_values) -> None:
    # The shared `given_user_opens` step put a DeleteEmployeePage into
    # delete_state["pom"]; that POM already has fill_manager_id.
    pom = delete_state.get("pom")
    assert pom is not None, (
        "No POM in delete_state — did `Given the user opens \"...\"` run?"
    )
    pom.fill_manager_id(value)
    verify_state["manager_id"] = value
    captured_values.add("Username (Manager ID) entered", value)


@then("the manager is logged in and the dashboard is displayed")
def then_logged_in_dashboard(page: Page, verify_state: dict, captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    visible = pom.dashboard_is_displayed(timeout=15000)
    captured_values.add("Post-login URL", page.url)
    captured_values.add("Dashboard 'View All Employees' visible",
                        "yes" if visible else "no")
    assert captured_values.assert_match(
        "Dashboard is displayed after login",
        expected="yes",
        actual="yes" if visible else "no",
    ), f"Dashboard not displayed after login. URL={page.url!r}"


@when(parsers.parse('the user clicks the "{label}" button on the dashboard'))
def when_clicks_dashboard_button(label: str, page: Page, verify_state: dict,
                                 captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    if label.strip().lower() == "view all employees":
        pom.click_view_all_employees()
    else:
        pytest.fail(
            f"No handler for clicking dashboard button {label!r}."
        )
    captured_values.add("Dashboard button clicked", label)


@then(parsers.parse('the page navigates to "{path}"'))
def then_page_navigates_to(path: str, page: Page, verify_state: dict,
                           captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    pom.page.wait_for_function(
        "([s]) => location.pathname.endsWith(s) || location.href.endsWith(s)",
        arg=[path],
        timeout=15000,
    )
    actual = page.url
    captured_values.add("URL after navigation", actual)
    assert captured_values.assert_match(
        "URL ends with expected path",
        expected=path,
        actual=path if actual.endswith(path) else actual,
    ), f"Expected URL to end with {path!r}, got {actual!r}"


@when(parsers.parse('the user selects "{filter_label}" in the filter dropdown'))
def when_selects_filter(filter_label: str, page: Page, verify_state: dict,
                        captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    pom.expect_directory_loaded()
    selected = pom.set_filter(filter_label)
    verify_state["filter_selected_text"] = selected
    captured_values.add("Filter selected", selected)
    assert captured_values.assert_match(
        "Filter dropdown selection starts with requested label",
        expected=filter_label.lower(),
        actual=selected[: len(filter_label)].lower(),
    ), f"Filter set to {selected!r}, expected to start with {filter_label!r}"


@when("the user leaves the search box empty")
def when_leaves_search_empty(page: Page, verify_state: dict, captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    # The search box defaults to empty after navigation; if anything has typed
    # into it earlier in the scenario, clear it. Either way we confirm empty.
    if not pom.search_box_is_empty():
        pom.clear_search_box()
    actual = pom.search_box_value()
    captured_values.add("Search box value", actual or "(empty)")
    assert captured_values.assert_match(
        "Search box is empty",
        expected="",
        actual=actual,
    ), f"Search box not empty: {actual!r}"


@then("the employees table is displayed")
def then_employees_table_displayed(page: Page, verify_state: dict,
                                   captured_values, test_data) -> None:
    pom = _directory_pom(page, verify_state)
    visible = pom.employees_table_is_displayed(timeout=15000)
    row_count = pom.visible_row_count()
    captured_values.add("Employees table visible", "yes" if visible else "no")
    captured_values.add("Visible row count on first page", row_count)
    # Build the CSV index now that we're about to start ticking off rows.
    _build_csv_index(test_data, verify_state)
    captured_values.add("CSV total rows (from user_data.json)", verify_state["csv_total"])
    assert captured_values.assert_match(
        "Employees table is displayed",
        expected="yes",
        actual="yes" if visible else "no",
    ), "Employees table not displayed after navigating to /all-employees/{manager_id}"
    assert row_count > 0, f"Employees table has no rows (count={row_count})"


@when(parsers.parse(
    'the user reads the names in the table and ticks each one off against the CSV, '
    'clicking the ">" next page button in the pagination footer until the last page '
    'is reached, using the "<" previous page button if needed to go back'
))
def when_walk_all_pages(page: Page, verify_state: dict, captured_values) -> None:
    pom = _directory_pom(page, verify_state)
    current, total = pom.parse_page_indicator()
    verify_state["pages_walked"].append(current)
    captured_values.add("Pagination total pages", total)
    # Reconcile page 1 first.
    _reconcile_current_page(pom, verify_state, captured_values)
    # Walk forward to the last page.
    while current < total:
        expected_next = current + 1
        pom.click_next_page()
        expect(pom.page.locator(f"text=Page {expected_next} of {total}")
               ).to_be_visible(timeout=10000)
        current, _ = pom.parse_page_indicator()
        verify_state["pages_walked"].append(current)
        _reconcile_current_page(pom, verify_state, captured_values)
    # Demonstrate that "<" still works to go back, then forward again — the
    # story explicitly allows using it if needed to go back.
    if total > 1:
        pom.click_prev_page()
        expect(pom.page.locator(f"text=Page {total - 1} of {total}")
               ).to_be_visible(timeout=10000)
        back_page, _ = pom.parse_page_indicator()
        captured_values.add("Backtracked one page via '<' button",
                            f"{total} -> {back_page}")
        pom.click_next_page()
        expect(pom.page.locator(f"text=Page {total} of {total}")
               ).to_be_visible(timeout=10000)
    captured_values.add("Pages walked",
                        ",".join(str(p) for p in verify_state["pages_walked"]))


@then("every name from the CSV appears somewhere in the UI employees table across all pages")
def then_every_csv_name_appears(verify_state: dict, captured_values) -> None:
    seen_ids = verify_state["ticked_ids"]
    csv_ids = set(verify_state["csv_index_by_id"].keys())
    csv_total = verify_state["csv_total"]
    missing_ids = sorted(csv_ids - seen_ids)
    missing_names = [
        f"{verify_state['csv_index_by_id'][i].get('Name', '')} ({i})"
        for i in missing_ids
    ]
    verify_state["missing_csv_names"] = missing_names
    captured_values.add("CSV total rows", csv_total)
    captured_values.add("Unique Emp IDs seen on screen", len(seen_ids))
    captured_values.add("CSV rows missing from UI (count)", len(missing_names))
    if missing_names:
        captured_values.add("CSV rows missing from UI (sample)",
                            ", ".join(missing_names[:10]))
    assert captured_values.assert_match(
        "Every CSV name appears on the UI",
        expected=str(csv_total),
        actual=str(len(seen_ids)),
    ), (
        f"UI is missing {len(missing_names)} employee(s) present in CSV: "
        f"{missing_names[:10]}"
    )


@then("any CSV name that is not found in the UI is reported as a missing employee")
def then_report_missing(verify_state: dict, captured_values) -> None:
    missing = verify_state.get("missing_csv_names") or []
    captured_values.add("Missing-employee report (count)", len(missing))
    if missing:
        # Record every missing entry individually for the auditor report.
        for entry in missing:
            captured_values.add("Missing from UI", entry, kind="missing")
    else:
        captured_values.add("Missing-employee report",
                            "No missing employees — UI matches CSV completely")
    # No assertion here: if there ARE missing rows, the preceding Then step
    # already failed. This step exists to make the "report" explicit in the
    # captured-values log even on the happy path.
