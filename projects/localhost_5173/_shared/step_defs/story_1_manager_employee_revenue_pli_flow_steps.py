from __future__ import annotations

import re
from typing import Any

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, then, when

from pages.page_manager_employee_revenue_pli_flow import ManagerFlowPage


_PAGE_KEY = "manager_flow_page"


# ---- shared fixture ------------------------------------------------------

@pytest.fixture()
def manager_flow_page(page: Page) -> ManagerFlowPage:
    return ManagerFlowPage(page)


# ============================================================
# Givens
# ============================================================

@given(parsers.parse('the user opens "{url}"'))
def given_open(manager_flow_page: ManagerFlowPage, url: str, captured_values) -> None:
    manager_flow_page.open(url)
    captured_values.assert_prerequisite(
        "Open application URL",
        condition=manager_flow_page.current_url().startswith(url.rstrip("/")),
        reason=f"failed to load {url}",
        evidence=manager_flow_page.current_url(),
    )
    captured_values.add("Application URL", manager_flow_page.current_url())


# ============================================================
# Login + dashboard
# ============================================================

@when(parsers.parse('the user types "{value}" into the "{label}" input'))
def when_type_into_input(manager_flow_page: ManagerFlowPage, value: str, label: str,
                         captured_values) -> None:
    norm = label.strip().lower()
    page = manager_flow_page.page
    # The label-to-input mapping spans several pages, so resolve per page.
    if norm == "manager id":
        page.locator("#manager-id").first.fill(value)
    elif norm == "password":
        page.locator("#password").first.fill(value)
    elif norm == "employee name":
        page.locator("#employee-name").first.fill(value)
    elif norm == "employee id":
        page.locator("#employee-id").first.fill(value)
    elif norm == "grade":
        page.locator("#grade").first.fill(value)
    elif norm == "employment type":
        page.locator("#employment-type").first.fill(value)
    elif norm == "ctc":
        page.locator("#ctc").first.fill(value)
    elif norm == "fixed pay":
        page.locator("#fixed-pay").first.fill(value)
    elif norm == "variable pay":
        page.locator("#variable-pay").first.fill(value)
    elif norm == "employee status":
        page.locator("#employee-status").first.fill(value)
    elif norm == "email":
        page.locator("#email").first.fill(value)
    elif norm == "revenue id":
        page.locator("#revenue-id").first.fill(value)
    elif norm == "cost":
        page.locator("#cost").first.fill(value)
    elif norm == "cost_currency":
        page.locator("#cost-currency").first.fill(value)
    elif norm == "revenue":
        page.locator("#revenue").first.fill(value)
    elif norm == "revenue currency":
        page.locator("#revenue-currency").first.fill(value)
    else:
        # KPI fields: 'KPI #N <Field>'.
        m = re.match(r"kpi\s*#(\d+)\s+(name|threshold|target|achieved|weightage)", norm)
        if m:
            idx = int(m.group(1)) - 1
            field = m.group(2)
            selector = {
                "name":      f"#kpi-name-{idx}",
                "threshold": f"#threshold-{idx}",
                "target":    f"#target-{idx}",
                "achieved":  f"#achieved-{idx}",
                "weightage": f"#weightage-{idx}",
            }[field]
            page.locator(selector).first.fill(value)
        else:
            raise AssertionError(f"No mapping for input label: {label!r}")
    captured_values.add(f"Typed into '{label}'", value)


@when(parsers.parse('the user clicks the "{label}" button'))
def when_click_named_button(manager_flow_page: ManagerFlowPage, label: str,
                            dialog_recorder, captured_values) -> None:
    # The story explicitly calls out the Login button under this exact phrasing.
    manager_flow_page.click_button(label)
    captured_values.add(f"Clicked button", label)


@then(parsers.parse('the URL changes to "{url}"'))
def then_url_changes_to(manager_flow_page: ManagerFlowPage, url: str, captured_values) -> None:
    manager_flow_page.expect_url(url)
    assert captured_values.assert_match("URL after action", expected=url,
                                        actual=manager_flow_page.current_url())


@then(parsers.parse('the URL changes back to "{url}"'))
def then_url_changes_back_to(manager_flow_page: ManagerFlowPage, url: str,
                             captured_values) -> None:
    manager_flow_page.expect_url(url)
    assert captured_values.assert_match("URL after action", expected=url,
                                        actual=manager_flow_page.current_url())


@then(parsers.parse('the navigation bar displays "{label}" with the manager name "{name}"'))
def then_nav_shows_welcome_and_name(manager_flow_page: ManagerFlowPage, label: str,
                                    name: str, captured_values) -> None:
    welcome_actual = manager_flow_page.welcome_text()
    name_actual = manager_flow_page.manager_name_text()
    captured_values.add("Navigation welcome label", welcome_actual)
    captured_values.add("Navigation manager name", name_actual)
    assert captured_values.assert_match("Navigation welcome label",
                                        expected=label, actual=welcome_actual)
    assert captured_values.assert_match("Navigation manager name",
                                        expected=name, actual=name_actual)


@then(parsers.parse('four tiles are visible: "{a}", "{b}", "{c}", and "{d}"'))
def then_four_tiles_visible(manager_flow_page: ManagerFlowPage, a: str, b: str,
                            c: str, d: str, captured_values) -> None:
    labels = [a, b, c, d]
    visibility = manager_flow_page.tile_labels_visible(labels)
    captured_values.add("Dashboard tiles seen", ", ".join(labels))
    all_visible_str = "all visible" if all(visibility.values()) else \
        f"missing: {[l for l, v in visibility.items() if not v]}"
    assert captured_values.assert_match(
        "Four dashboard tiles visible",
        expected="all visible",
        actual=all_visible_str,
    )


@then(parsers.parse('the "{tab_label}" tab is selected by default'))
def then_tab_selected_by_default(manager_flow_page: ManagerFlowPage, tab_label: str,
                                 captured_values) -> None:
    # The default-selected tab on the dashboard is Manage Employees — confirmed
    # because the employee table is rendered.
    actual = "Manage Employees" if manager_flow_page.manage_employees_tab_active() else "(unknown)"
    assert captured_values.assert_match(
        f"Selected tab on dashboard",
        expected=tab_label, actual=actual,
    )


# ============================================================
# Add Employee
# ============================================================

@when(parsers.parse('the user clicks the green "Add Employee" button on the Manage Employees tab'))
def when_click_add_employee_top(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.click_add_employee_top()
    captured_values.add("Clicked", "Add Employee (Manage Employees tab)")


@then(parsers.parse('the "{form_label}" form is displayed'))
def then_form_displayed(manager_flow_page: ManagerFlowPage, form_label: str,
                        captured_values) -> None:
    label = form_label.strip().lower()
    if label == "add new employee":
        visible = manager_flow_page.add_employee_form_visible()
    elif label == "set performance":
        visible = manager_flow_page.set_performance_form_visible()
    elif label == "add revenue":
        visible = manager_flow_page.add_revenue_form_visible()
    else:
        raise AssertionError(f"Unknown form label: {form_label!r}")
    assert captured_values.assert_match(
        f"Form displayed: {form_label}",
        expected="visible",
        actual="visible" if visible else "not visible",
    )


@when(parsers.parse('the user selects "{value}" from the "{label}" dropdown'))
def when_select_dropdown(manager_flow_page: ManagerFlowPage, value: str, label: str,
                        captured_values) -> None:
    norm = label.strip().lower()
    page = manager_flow_page.page
    if norm == "department":
        page.locator("#department").first.select_option(value=value)
    elif norm == "project":
        page.locator("#project").first.select_option(value=value)
    elif norm == "quarter":
        page.locator("#quarter").first.select_option(value=value)
    elif norm == "emp_id":
        page.locator("#empId").first.select_option(value=value)
    elif norm == "employee":
        # Story sends "7777 — Priya Sharma"; the option value is the emp id.
        head = value.strip().split()[0]
        try:
            page.locator("#employee").first.select_option(value=head)
        except Exception:
            page.locator("#employee").first.select_option(label=value)
    else:
        raise AssertionError(f"No mapping for dropdown label: {label!r}")
    captured_values.add(f"Selected from '{label}' dropdown", value)


@when(parsers.parse('the user clicks the blue "Add Employee" button at the bottom of the form'))
def when_click_submit_add_employee(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.submit_add_employee()
    captured_values.add("Clicked", "Add Employee (form submit)")


@then(parsers.parse('a browser alert is displayed with the text "{text}"'))
def then_alert_displayed(dialog_recorder, manager_flow_page: ManagerFlowPage,
                         text: str, captured_values) -> None:
    # `dialog_recorder` auto-accepts every dialog and stores the message text.
    # Playwright dispatches dialog events asynchronously, so the recorder may
    # not yet hold the message by the time this assertion step starts —
    # poll briefly until either the expected message appears, or we time out.
    import time as _time
    deadline = _time.monotonic() + 5.0
    while _time.monotonic() < deadline:
        if dialog_recorder.last == text or text in (dialog_recorder.messages or []):
            break
        manager_flow_page.page.wait_for_timeout(100)
    actual = dialog_recorder.last or ""
    assert captured_values.assert_match(
        "Browser alert text",
        expected=text,
        actual=actual,
    ), f"Expected alert {text!r}, got {actual!r}"


@when(parsers.parse('the user clicks "OK" on the alert'))
def when_click_ok_on_alert(captured_values) -> None:
    # The dialog_recorder already accepted the alert when it fired (page.on
    # 'dialog'). This step is just acknowledgement in the test narrative.
    captured_values.add("Acknowledged alert", "OK")


@when(parsers.parse('the user clicks "OK"'))
def when_click_ok(captured_values) -> None:
    captured_values.add("Acknowledged alert", "OK")


@then(parsers.parse('a row with Emp ID "{emp_id}" and Name "{name}" appears in the Manage Employees table'))
def then_row_appears(manager_flow_page: ManagerFlowPage, emp_id: str, name: str,
                     captured_values) -> None:
    # Make sure we're on the Manage Employees tab.
    try:
        manager_flow_page.page.locator("button:has-text('Manage Employees')").first.click()
    except Exception:
        pass
    row_text = manager_flow_page.employee_row_text(emp_id)
    captured_values.add("Employee row text", row_text or "(not found)")
    found = bool(row_text and emp_id in row_text and name in row_text)
    assert captured_values.assert_match(
        f"Row with Emp ID {emp_id} / {name} present in Manage Employees table",
        expected=f"row contains '{emp_id}' and '{name}'",
        actual=f"row contains '{emp_id}' and '{name}'" if found else f"row text: {row_text!r}",
    )


# ============================================================
# Manage Revenue tab + buttons
# ============================================================

@when(parsers.parse('the user clicks the "Manage Revenue" tab at the top of the dashboard'))
def when_click_manage_revenue_tab(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.click_manage_revenue_tab()
    captured_values.add("Clicked tab", "Manage Revenue")


@when(parsers.parse('the user clicks the "Manage Revenue" tab'))
def when_click_manage_revenue_tab_alt(manager_flow_page: ManagerFlowPage,
                                      captured_values) -> None:
    manager_flow_page.click_manage_revenue_tab()
    captured_values.add("Clicked tab", "Manage Revenue")


@then(parsers.parse('the Manage Revenue panel is displayed'))
def then_manage_revenue_panel_displayed(manager_flow_page: ManagerFlowPage,
                                        captured_values) -> None:
    visible = manager_flow_page.manage_revenue_panel_visible()
    assert captured_values.assert_match(
        "Manage Revenue panel displayed",
        expected="visible",
        actual="visible" if visible else "not visible",
    )


@then(parsers.parse('the buttons "{b1}", "{b2}", "{b3}", "{b4}", and "{b5}" are visible'))
def then_revenue_buttons_visible(manager_flow_page: ManagerFlowPage, b1: str, b2: str,
                                 b3: str, b4: str, b5: str, captured_values) -> None:
    labels = [b1, b2, b3, b4, b5]
    visibility = manager_flow_page.revenue_panel_buttons_visible(labels)
    captured_values.add("Manage Revenue buttons seen", ", ".join(labels))
    all_visible_str = "all visible" if all(visibility.values()) else \
        f"missing: {[l for l, v in visibility.items() if not v]}"
    assert captured_values.assert_match(
        "Manage Revenue panel buttons visible",
        expected="all visible",
        actual=all_visible_str,
    )


# ---- Set Performance entry point ----

@when(parsers.parse('the user clicks the red "Set Performance" button'))
def when_click_set_performance(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.page.locator("button:has-text('Set Performance')").first.click()
    captured_values.add("Clicked button", "Set Performance")


@when(parsers.parse('the user clicks the dark "Add More KPI" button'))
def when_click_add_more_kpi(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.click_add_more_kpi()
    captured_values.add("Clicked button", "Add More KPI")


@when(parsers.parse('the user clicks the blue "Save All KPIs" button'))
def when_click_save_all_kpis(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.click_save_all_kpis()
    captured_values.add("Clicked button", "Save All KPIs")


# ---- Add Revenue entry point ----

@when(parsers.parse('the user clicks the blue "Add Revenue" button'))
def when_click_add_revenue(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.page.locator("button:has-text('Add Revenue')").first.click()
    captured_values.add("Clicked button", "Add Revenue")


@then(parsers.parse('the "Employee Name" field is auto-filled with "{name}" and is read-only'))
def then_employee_name_auto_filled(manager_flow_page: ManagerFlowPage, name: str,
                                   captured_values) -> None:
    actual = manager_flow_page.employee_name_readonly_value()
    captured_values.add("Add-Revenue Employee Name field value", actual)
    assert captured_values.assert_match(
        "Add-Revenue Employee Name auto-filled value",
        expected=name, actual=actual,
    )
    readonly = manager_flow_page.employee_name_readonly_is_readonly()
    assert captured_values.assert_match(
        "Add-Revenue Employee Name read-only flag",
        expected="True", actual=str(readonly),
    )


@when(parsers.parse('the user picks "{value}" in the "{label}" month-picker'))
def when_pick_month(manager_flow_page: ManagerFlowPage, value: str, label: str,
                   captured_values) -> None:
    if label.strip().lower() != "month":
        raise AssertionError(f"Unknown month picker label: {label!r}")
    manager_flow_page.page.locator("#month").first.fill(value)
    captured_values.add(f"Picked month for '{label}'", value)


@when(parsers.parse('the user clicks the blue "Add Revenue" button at the bottom of the form'))
def when_click_submit_add_revenue(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.submit_add_revenue()
    captured_values.add("Clicked", "Add Revenue (form submit)")


# ---- Show PLI entry point ----

@when(parsers.parse('the user clicks the blue "Show PLI" button'))
def when_click_show_pli(manager_flow_page: ManagerFlowPage, captured_values) -> None:
    manager_flow_page.page.locator("button:has-text('Show PLI')").first.click()
    captured_values.add("Clicked button", "Show PLI")


@then(parsers.parse('the "PLI Data" table is displayed'))
def then_pli_data_table_displayed(manager_flow_page: ManagerFlowPage,
                                  captured_values) -> None:
    visible = manager_flow_page.show_pli_table_visible()
    assert captured_values.assert_match(
        "PLI Data table displayed",
        expected="visible",
        actual="visible" if visible else "not visible",
    )


@then(parsers.parse('the "PLI Data" table contains a row with the following values:'))
def then_pli_table_row(manager_flow_page: ManagerFlowPage, datatable,
                       captured_values) -> None:
    # The Gherkin data-table passes through pytest-bdd as a list-of-rows.
    rows = datatable
    if len(rows) < 2:
        raise AssertionError(f"Expected header + 1 row, got: {rows!r}")
    headers = [h.strip() for h in rows[0]]
    values = [v.strip() for v in rows[1]]
    expected = dict(zip(headers, values))
    emp_id = expected.get("Emp ID")
    actual = manager_flow_page.pli_row_values(emp_id)
    if actual is None:
        captured_values.assert_prerequisite(
            "PLI row presence",
            condition=False,
            reason=f"no PLI row for Emp ID {emp_id} in the PLI Data table",
        )
    captured_values.add("PLI row actual", str(actual))
    captured_values.add("PLI row expected", str(expected))
    assert captured_values.assert_match(
        f"PLI row Emp ID {emp_id} — Emp ID cell",
        expected=expected["Emp ID"], actual=actual["Emp ID"],
    )
    assert captured_values.assert_match(
        f"PLI row Emp ID {emp_id} — Eligible Amount (USD)",
        expected=expected["Eligible Amount (USD)"],
        actual=actual["Eligible Amount (USD)"],
    )
    assert captured_values.assert_match(
        f"PLI row Emp ID {emp_id} — Payable Amount (USD)",
        expected=expected["Payable Amount (USD)"],
        actual=actual["Payable Amount (USD)"],
    )


@when(parsers.parse('the user clicks the "{emp_id}" link in the Emp ID column'))
def when_click_emp_id_link(manager_flow_page: ManagerFlowPage, emp_id: str,
                           captured_values) -> None:
    manager_flow_page.click_pli_emp_link(emp_id)
    captured_values.add("Clicked Emp ID link", emp_id)


@then(parsers.parse('the page header shows:'))
def then_page_header_shows(manager_flow_page: ManagerFlowPage, datatable,
                           captured_values) -> None:
    rows = datatable
    if len(rows) < 2:
        raise AssertionError("page-header datatable too short")
    # Wait for the async-loaded data to be present by anchoring on the
    # Name row, which is the last to populate.
    name_value = None
    for field, expected in rows[1:]:
        if field.strip().lower() == "name":
            name_value = expected.strip()
            break
    must_contain = f"Name: {name_value}" if name_value else None
    header_text = manager_flow_page.employee_pli_header_text(must_contain=must_contain)
    flat = " ".join(header_text.split())
    captured_values.add("Show-Employee-PLI header text", flat)
    # Skip the first row (the table header: 'Field | Value').
    failures: list[str] = []
    for field, expected in rows[1:]:
        f = field.strip()
        e = expected.strip()
        # The header renders as "<Field>: <Value>". Look for the literal pair.
        needle = f"{f}: {e}"
        passed = needle in flat
        captured_values.assert_match(
            f"Page header field '{f}'",
            expected=needle,
            actual=(needle if passed else f"header was: {flat}"),
        )
        if not passed:
            failures.append(needle)
    assert not failures, f"Show-Employee-PLI header missing: {failures}; header was: {flat}"


@then(parsers.parse('the KPI breakdown table contains exactly two rows:'))
def then_kpi_table(manager_flow_page: ManagerFlowPage, datatable,
                   captured_values) -> None:
    rows = datatable
    if len(rows) < 2:
        raise AssertionError("KPI datatable too short")
    headers = [h.strip() for h in rows[0]]
    expected_rows = [dict(zip(headers, [c.strip() for c in r])) for r in rows[1:]]

    actual_table = manager_flow_page.kpi_rows()
    assert captured_values.assert_match(
        "KPI breakdown row count",
        expected=str(len(expected_rows)),
        actual=str(len(actual_table)),
    )
    # Map actual rows by KPI name so order independence is OK; the story
    # specifies exact text per row, which we then assert cell-by-cell.
    actual_by_kpi: dict[str, list[str]] = {}
    for row in actual_table:
        if row:
            actual_by_kpi[row[0]] = row
    failures: list[str] = []
    for exp in expected_rows:
        kpi = exp["KPI"]
        actual_cells = actual_by_kpi.get(kpi)
        if actual_cells is None:
            captured_values.assert_match(
                f"KPI row present for '{kpi}'",
                expected="present", actual="missing",
            )
            failures.append(f"row {kpi} missing")
            continue
        actual_dict = dict(zip(headers, actual_cells))
        for col in headers:
            passed = captured_values.assert_match(
                f"KPI row '{kpi}' — column '{col}'",
                expected=exp[col],
                actual=actual_dict.get(col, "(missing)"),
            )
            if not passed:
                failures.append(f"row {kpi} column {col}: {exp[col]!r} vs {actual_dict.get(col)!r}")
    assert not failures, f"KPI breakdown mismatches: {failures}"


@then(parsers.parse('the Total row at the bottom shows:'))
def then_total_row(manager_flow_page: ManagerFlowPage, datatable,
                   captured_values) -> None:
    rows = datatable
    if len(rows) < 2:
        raise AssertionError("Total datatable too short")
    headers = [h.strip() for h in rows[0]]
    values = [v.strip() for v in rows[1]]
    expected = dict(zip(headers, values))

    actual = manager_flow_page.total_row_values()
    if actual is None:
        captured_values.assert_prerequisite(
            "Total row presence",
            condition=False,
            reason="no Total row found in the KPI breakdown table",
        )
    captured_values.add("KPI-breakdown Total row", str(actual))
    assert captured_values.assert_match(
        "KPI breakdown Total — Eligible",
        expected=expected["Eligible"], actual=actual["Eligible"],
    )
    assert captured_values.assert_match(
        "KPI breakdown Total — Payable",
        expected=expected["Payable"], actual=actual["Payable"],
    )
