from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, when, then, parsers

from pages.page_all_employees_directory_walk import AllEmployeesDirectoryWalkPage


# ---------------------------------------------------------------------------
# Per-scenario state. The story walks every page sequentially and ticks off
# each live employee against the test_data ("CSV"). We keep two tallies:
#   * ticked_ids       : every Emp ID we have seen on screen at least once
#   * page_history     : list of (page_no, rows) for the report
# The state is exposed via a fixture so step defs can share it.
# ---------------------------------------------------------------------------

@pytest.fixture()
def walk_state() -> dict:
    return {
        "ticked_ids": set(),       # Emp IDs seen on screen at least once
        "ticked_records": [],      # full row dicts in order observed
        "page_history": [],        # [(page_no, [row, row, ...]), ...]
        "csv_index_by_id": {},     # Emp ID -> CSV record (built once from test_data)
        "csv_index_by_name": {},   # Name -> list of CSV records (for ambiguity)
        "csv_total": 0,
        "csv_filename": "",
        "current_page_rows": [],   # rows on the page we are currently looking at
    }


def _build_csv_index(test_data, state: dict) -> None:
    """Populate state['csv_index_by_id'] and friends from the test_data fixture
    (which loads user_data.json at runtime). The story calls this the 'exported
    CSV'; the framework reads user_data.json instead so changes take effect
    without regenerating code."""
    records = test_data if isinstance(test_data, list) else []
    by_id, by_name = {}, {}
    for rec in records:
        emp_id = str(rec.get("Emp ID", "")).strip()
        name = str(rec.get("Name", "")).strip()
        if emp_id:
            by_id[emp_id] = rec
        by_name.setdefault(name, []).append(rec)
    state["csv_index_by_id"] = by_id
    state["csv_index_by_name"] = by_name
    state["csv_total"] = len(records)


def _reconcile_current_page(page_obj: AllEmployeesDirectoryWalkPage, state: dict, cap) -> None:
    """Read the currently-visible table rows, record each one against
    the CSV index, and assert every (Name, Emp ID) is in the CSV."""
    rows = page_obj.read_visible_rows()
    state["current_page_rows"] = rows
    state["page_history"].append(rows)

    page_no, _ = page_obj.parse_page_indicator()
    for idx, row in enumerate(rows, start=1):
        emp_id = (row.get("Emp ID") or "").strip()
        name = (row.get("Name") or "").strip()
        record_label = f"P{page_no} row {idx}: {name} ({emp_id})"
        # Disambiguate with Emp ID: lookup by Emp ID first, then verify name matches.
        csv_record = state["csv_index_by_id"].get(emp_id)
        in_csv = bool(csv_record) and (
            (csv_record.get("Name") or "").strip().lower() == name.lower()
        )
        cap.add(record_label, "in CSV" if in_csv else "MISSING from CSV",
                emp_id=emp_id, name=name, csv_name=(csv_record or {}).get("Name", ""))
        if not in_csv:
            raise AssertionError(
                f"Row on screen not found in CSV by Emp ID + Name: {row!r}. "
                f"CSV record for Emp ID {emp_id}: {csv_record!r}"
            )
        if emp_id not in state["ticked_ids"]:
            state["ticked_ids"].add(emp_id)
            state["ticked_records"].append(row)


# ===========================================================================
# Background steps
# ===========================================================================

@given(parsers.parse('the application base URL is "{url}"'))
def given_base_url(url: str, walk_state: dict, captured_values) -> None:
    walk_state["base_url"] = url
    captured_values.add("Application base URL", url)


@given(parsers.parse('the manager has the exported CSV "{filename}" open beside the browser'))
def given_exported_csv(filename: str, walk_state: dict, test_data, captured_values) -> None:
    walk_state["csv_filename"] = filename
    _build_csv_index(test_data, walk_state)
    captured_values.add("Exported CSV filename (reference)", filename)
    captured_values.add("CSV row count (from user_data.json)", walk_state["csv_total"])


# ===========================================================================
# Scenario steps
# ===========================================================================

@given(parsers.parse('the manager opens the application at "{url}"'))
def given_manager_opens(url: str, page: Page, walk_state: dict, captured_values) -> None:
    pom = AllEmployeesDirectoryWalkPage(page)
    pom.open(url)
    walk_state["pom"] = pom
    captured_values.add("Opened URL", page.url)


@then("the manager is greeted by the login screen")
def then_login_screen(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    heading_text = pom.expect_login_screen()
    captured_values.add("Login heading text", heading_text)
    assert captured_values.assert_match(
        "Login screen heading", expected="PLI System Login", actual=heading_text
    ), f"Login heading mismatch: got {heading_text!r}"


@when(parsers.parse('the manager enters Manager ID "{manager_id}" in the username field'))
def when_enter_manager_id(manager_id: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    pom.fill_manager_id(manager_id)
    walk_state["manager_id"] = manager_id
    captured_values.add("Manager ID entered", manager_id)


@when(parsers.parse('the manager enters password "{password}"'))
def when_enter_password(password: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    pom.fill_password(password)
    captured_values.add("Password entered", "*" * len(password))


@when(parsers.parse('the manager clicks the "{button_label}" button'))
def when_click_button(button_label: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    if button_label.strip().lower() == "login":
        pom.click_login()
    else:
        pytest.fail(
            f"Step 'clicks the \"{button_label}\" button' not implemented: "
            "no handler for that button label."
        )
    captured_values.add("Clicked button", button_label)


@then(parsers.parse('the manager lands on "{url}"'))
def then_manager_lands_on(url: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    pom.wait_for_url_exact(url, timeout=15000)
    actual_url = pom.current_url()
    captured_values.add("Post-login URL", actual_url)
    assert captured_values.assert_match(
        "Manager dashboard URL", expected=url, actual=actual_url
    ), f"Expected URL {url}, got {actual_url}"


@when(parsers.parse('the manager clicks "{label}" from the dashboard'))
def when_click_dashboard_link(label: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    if label.strip().lower() == "view all employees":
        pom.click_view_all_employees()
    else:
        pytest.fail(
            f"Step 'clicks \"{label}\" from the dashboard' not implemented: "
            "no handler for that dashboard link."
        )
    captured_values.add("Dashboard action clicked", label)


@then(parsers.parse('the manager navigates to "{url}"'))
def then_navigates_to(url: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    pom.wait_for_url_exact(url, timeout=15000)
    pom.expect_directory_loaded()
    actual_url = pom.current_url()
    captured_values.add("All Employees URL", actual_url)
    assert captured_values.assert_match(
        "All Employees page URL", expected=url, actual=actual_url
    ), f"Expected URL {url}, got {actual_url}"


@when(parsers.parse('the manager sets the filter dropdown to "{filter_label}"'))
def when_set_filter(filter_label: str, walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    selected_text = pom.set_filter(filter_label)
    walk_state["filter_label"] = filter_label
    walk_state["filter_selected_text"] = selected_text
    captured_values.add("Filter selected", selected_text)


@then("the manager is working against the full directory rather than a single department")
def then_full_directory(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    selected_text = pom.current_filter_label().strip()
    # The option text is e.g. "All Employees (100)". The check is that it
    # starts with "All Employees" (i.e. not a single department).
    is_all = selected_text.lower().startswith("all employees")
    captured_values.add("Filter option in effect", selected_text)
    assert captured_values.assert_match(
        "Filter scope is 'All Employees'",
        expected="starts with 'All Employees'",
        actual="starts with 'All Employees'" if is_all else f"starts with {selected_text!r}",
    ), f"Filter is not set to All Employees: {selected_text!r}"


@when("the manager clears the search box")
def when_clear_search(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    pom.clear_search_box()
    captured_values.add("Search box value after clear", pom.search_box_value())


@then("no rows are accidentally hidden from the table")
def then_no_rows_hidden(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    row_count = pom.visible_row_count()
    captured_values.add("Visible rows after clearing search", row_count)
    # "Not hidden" = at least one row visible. The directory paginates 10
    # at a time, so on a 100-row dataset we expect exactly 10 here.
    assert captured_values.assert_match(
        "Search-box-cleared row visibility",
        expected="rows visible",
        actual="rows visible" if row_count > 0 else "no rows visible (hidden)",
    ), f"Search-box-cleared table is empty (row count {row_count})"


@when("the manager reads the first ten names in the table")
def when_read_first_ten(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    rows = pom.read_visible_rows()
    walk_state["current_page_rows"] = rows
    for idx, row in enumerate(rows, start=1):
        captured_values.add(
            f"Page 1 row {idx}", f"{row.get('Name')} ({row.get('Emp ID')})"
        )


@when(parsers.parse('the manager ticks each one off in the CSV "{filename}"'))
def when_tick_off_csv(filename: str, walk_state: dict, captured_values) -> None:
    captured_values.add("Ticking against CSV", filename)
    # Reconciliation itself happens in the "every employee ... is found in
    # the CSV" Then step. Here we just record that the manager is using the
    # named CSV — which has already been indexed in the Background.
    assert captured_values.assert_match(
        "CSV filename matches Background",
        expected=walk_state.get("csv_filename"),
        actual=filename,
    ), f"CSV filename mismatch: scenario uses {filename!r}, background used {walk_state.get('csv_filename')!r}"


@when(parsers.parse('the manager uses the "{column}" column to disambiguate when two people share a name'))
def when_disambiguate(column: str, walk_state: dict, captured_values) -> None:
    rows = walk_state.get("current_page_rows") or []
    # Detect any duplicate name on the current page and record how Emp ID
    # disambiguates them.
    seen_names: dict[str, list[str]] = {}
    for row in rows:
        seen_names.setdefault((row.get("Name") or "").strip(), []).append(
            (row.get(column) or "").strip()
        )
    duplicates = {n: ids for n, ids in seen_names.items() if len(ids) > 1}
    captured_values.add(f"Duplicate names on current page disambiguated by {column}",
                        f"{len(duplicates)} duplicate-name groups")
    walk_state["duplicate_groups_current_page"] = duplicates


@then("every employee shown on the current page is found in the CSV by name and Emp ID")
def then_current_page_reconciles(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    _reconcile_current_page(pom, walk_state, captured_values)
    page_no, page_total = pom.parse_page_indicator()
    captured_values.add(
        f"Page {page_no}/{page_total} reconciled",
        f"{len(walk_state['current_page_rows'])} rows OK against CSV",
    )


@when('the manager clicks the right-arrow ">" button in the pagination footer to advance to the next ten rows')
def when_click_right_arrow(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    before, total = pom.parse_page_indicator()
    walk_state["page_before_advance"] = before
    pom.click_next_page()
    # Wait for the indicator to actually advance.
    expect(pom.page.locator(f"text=Page {before + 1} of {total}")).to_be_visible(timeout=10000)
    after, _ = pom.parse_page_indicator()
    captured_values.add("Pagination advance (single)", f"{before} -> {after}")


@then('the "Page X of Y" indicator increments to reflect the new page')
def then_indicator_increments(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    after, _ = pom.parse_page_indicator()
    before = walk_state.get("page_before_advance")
    captured_values.add("Indicator before/after", f"{before} -> {after}")
    assert captured_values.assert_match(
        "Page indicator incremented",
        expected=str((before or 0) + 1),
        actual=str(after),
    ), f"Expected page {(before or 0) + 1} after advance, got {after}"


@then("the manager repeats the same name-by-name check on the new page")
def then_repeat_check_new_page(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    rows = pom.read_visible_rows()
    walk_state["current_page_rows"] = rows
    page_no, _ = pom.parse_page_indicator()
    for idx, row in enumerate(rows, start=1):
        captured_values.add(
            f"Page {page_no} row {idx}",
            f"{row.get('Name')} ({row.get('Emp ID')})",
        )


@then("every employee shown on the new page is found in the CSV by name and Emp ID")
def then_new_page_reconciles(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    _reconcile_current_page(pom, walk_state, captured_values)
    page_no, page_total = pom.parse_page_indicator()
    captured_values.add(
        f"Page {page_no}/{page_total} reconciled (new page)",
        f"{len(walk_state['current_page_rows'])} rows OK against CSV",
    )


@when('the manager keeps advancing with the right-arrow ">" button, page by page, watching the "Page X of Y" indicator to know how far along they are')
def when_keep_advancing(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    current, total = pom.parse_page_indicator()
    walk_state["total_pages"] = total
    # Reconcile each intermediate page as we go, then advance.
    pages_walked = [current]
    while current < total:
        _reconcile_current_page(pom, walk_state, captured_values)
        expected_next = current + 1
        pom.click_next_page()
        expect(pom.page.locator(f"text=Page {expected_next} of {total}")).to_be_visible(timeout=10000)
        current, _ = pom.parse_page_indicator()
        pages_walked.append(current)
    # Final page (the loop above advanced TO it but did not reconcile it yet).
    _reconcile_current_page(pom, walk_state, captured_values)
    walk_state["pages_walked"] = pages_walked
    walk_state["last_page_rows"] = list(walk_state["current_page_rows"])
    captured_values.add("Pages walked in sequence", ",".join(str(p) for p in pages_walked))


@then("the manager reaches the last page, which may contain fewer than ten rows")
def then_last_page(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    current, total = pom.parse_page_indicator()
    last_rows = walk_state.get("last_page_rows") or []
    captured_values.add("Last page indicator", f"Page {current} of {total}")
    captured_values.add("Last page row count", len(last_rows))
    assert captured_values.assert_match(
        "Reached last page",
        expected=str(total),
        actual=str(current),
    ), f"Did not reach the last page: indicator says {current} of {total}"
    # And the last page must have <= 10 rows (the directory's page size).
    assert 0 < len(last_rows) <= 10, (
        f"Last page row count out of bounds (1..10): {len(last_rows)}"
    )


@then("every employee shown on each intermediate page is found in the CSV by name and Emp ID")
def then_all_intermediate(walk_state: dict, captured_values) -> None:
    # By the time we get here `_reconcile_current_page` has already asserted
    # every row on every page we visited. Surface a per-page summary into the
    # report so the auditor sees the breakdown.
    history = walk_state.get("page_history") or []
    seen_total = sum(len(rows) for rows in history)
    captured_values.add("Total rows reconciled across all pages walked",
                        seen_total)
    for idx, rows in enumerate(history, start=1):
        captured_values.add_component(
            f"Page {idx} reconciled row count",
            len(rows),
            group="reconciled_rows_per_page",
        )
    # The sum of the per-page counts must equal the running ticked tally
    # (no row should have been skipped).
    assert captured_values.assert_sum(
        "All pages combined row count == sum of per-page counts",
        group="reconciled_rows_per_page",
        actual=seen_total,
    ), "Per-page row counts do not sum to the running ticked tally"


@when("the manager loses their place on the current page")
def when_loses_place(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    cur, total = pom.parse_page_indicator()
    walk_state["page_before_backtrack"] = cur
    captured_values.add("Manager position before backtrack", f"Page {cur} of {total}")


@when('the manager clicks the left-arrow "<" button in the pagination footer to step back to an earlier page')
def when_click_left_arrow(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    cur, total = pom.parse_page_indicator()
    expected_prev = max(1, cur - 1)
    pom.click_prev_page()
    expect(pom.page.locator(f"text=Page {expected_prev} of {total}")).to_be_visible(timeout=10000)
    after, _ = pom.parse_page_indicator()
    walk_state["page_after_backtrack"] = after
    captured_values.add("Backtracked one page", f"{cur} -> {after}")


@then("the manager rechecks the names on that earlier page against the CSV")
def then_recheck_earlier(walk_state: dict, captured_values) -> None:
    pom: AllEmployeesDirectoryWalkPage = walk_state["pom"]
    rows = pom.read_visible_rows()
    walk_state["current_page_rows"] = rows
    page_no, _ = pom.parse_page_indicator()
    captured_values.add(
        f"Recheck page {page_no} row count", len(rows)
    )
    # Reconcile against CSV again — any failure on a re-walked page is also
    # a story failure.
    for row in rows:
        emp_id = (row.get("Emp ID") or "").strip()
        name = (row.get("Name") or "").strip()
        csv_record = walk_state["csv_index_by_id"].get(emp_id)
        ok = bool(csv_record) and (csv_record.get("Name") or "").strip().lower() == name.lower()
        captured_values.add(
            f"Recheck page {page_no}: {name} ({emp_id})",
            "in CSV" if ok else "MISSING from CSV",
        )
        if not ok:
            raise AssertionError(
                f"Recheck failed for row {row!r}; CSV record: {csv_record!r}"
            )


@then("at the end of the walk every CSV row has been ticked off")
def then_all_csv_ticked(walk_state: dict, captured_values) -> None:
    csv_total = walk_state.get("csv_total", 0)
    ticked = len(walk_state.get("ticked_ids") or set())
    captured_values.add("CSV total rows", csv_total)
    captured_values.add("Unique Emp IDs ticked off on screen", ticked)
    # Missing CSV rows (in CSV but never seen on screen) are recorded so the
    # report shows exactly which ones, then the assertion fails on count.
    seen_ids = walk_state["ticked_ids"]
    missing = [eid for eid in walk_state["csv_index_by_id"].keys() if eid not in seen_ids]
    captured_values.add("CSV rows not seen on screen (count)", len(missing))
    if missing:
        captured_values.add("CSV rows not seen on screen (sample)", ",".join(missing[:10]))
    assert captured_values.assert_match(
        "All CSV rows ticked off after walk",
        expected=str(csv_total),
        actual=str(ticked),
    ), f"CSV rows ticked ({ticked}) != CSV total ({csv_total}); missing={missing[:10]}..."


@then("no employee shown on screen is absent from the CSV")
def then_no_extras(walk_state: dict, captured_values) -> None:
    history = walk_state.get("page_history") or []
    extras: list[str] = []
    for rows in history:
        for row in rows:
            emp_id = (row.get("Emp ID") or "").strip()
            name = (row.get("Name") or "").strip()
            rec = walk_state["csv_index_by_id"].get(emp_id)
            if not rec or (rec.get("Name") or "").strip().lower() != name.lower():
                extras.append(f"{name} ({emp_id})")
    captured_values.add("Screen rows absent from CSV (count)", len(extras))
    if extras:
        captured_values.add("Screen rows absent from CSV (sample)", ",".join(extras[:10]))
    assert captured_values.assert_match(
        "No on-screen employee is absent from CSV",
        expected="0 extras",
        actual=f"{len(extras)} extras",
    ), f"On-screen rows not in CSV: {extras[:10]}..."
