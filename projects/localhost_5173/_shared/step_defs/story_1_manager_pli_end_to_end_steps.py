from __future__ import annotations

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, parsers, then, when

from pages.page_manager_pli import ManagerPLIPage

DEFAULT_TIMEOUT = 15000


# ---------- Helpers --------------------------------------------------------

def _kv_table(datatable: list[list[str]]) -> dict[str, str]:
    """Convert a `| Field | Value |` data table into a dict.
    First row is treated as the header."""
    if not datatable:
        return {}
    rows = datatable[1:] if len(datatable) > 1 else []
    out: dict[str, str] = {}
    for row in rows:
        if len(row) >= 2:
            out[row[0].strip()] = row[1].strip()
    return out


def _single_col(datatable: list[list[str]]) -> list[str]:
    """Convert a single-column data table into a list (skips header)."""
    if not datatable:
        return []
    rows = datatable[1:] if len(datatable) > 1 else []
    return [r[0].strip() for r in rows if r]


# ---------- Fixtures -------------------------------------------------------

@pytest.fixture()
def manager_page(page: Page) -> ManagerPLIPage:
    return ManagerPLIPage(page)


# ---------- Given ----------------------------------------------------------

@given(parsers.parse('the user opens "{url}"'))
def step_open_url(manager_page: ManagerPLIPage, url: str) -> None:
    manager_page.open(url)


# ---------- When: typing / clicking / selecting ---------------------------

@when(parsers.parse('the user types "{value}" into the "{field}" input'))
def step_type_into_input(manager_page: ManagerPLIPage, value: str, field: str) -> None:
    manager_page.fill_login_field(field, value)


@when(parsers.parse('the user clicks the "{button}" button'))
def step_click_button(manager_page: ManagerPLIPage, button: str) -> None:
    if button == "Login":
        manager_page.click_login()
    elif button in ("Manage Employees", "Manage Revenue"):
        manager_page.click_tab(button)
    else:
        manager_page.click_dashboard_button(button)


@when('the user clicks the green "Add Employee" button on the Manage Employees tab')
def step_click_green_add_employee(manager_page: ManagerPLIPage) -> None:
    manager_page.click_add_employee()


@when('the user clicks the blue "Add Employee" button at the bottom of the form')
def step_click_blue_add_employee_submit(manager_page: ManagerPLIPage) -> None:
    manager_page.submit_add_employee()


@when(parsers.parse('the user clicks "OK" on the alert'))
def step_click_ok_on_alert(dialog_recorder, manager_page: ManagerPLIPage) -> None:
    # Dialogs auto-accept via the DialogRecorder fixture installed in tests/conftest.py.
    # This step is a no-op confirmation; the dialog has already been handled.
    if dialog_recorder.last is None:
        pytest.fail(
            "Step clicks OK on alert: expected a recorded dialog but DialogRecorder.last is None"
        )


@when(parsers.parse('the user clicks the "{tab}" tab at the top of the dashboard'))
def step_click_tab_top(manager_page: ManagerPLIPage, tab: str) -> None:
    manager_page.click_tab(tab)


@when(parsers.parse('the user clicks the "{tab}" tab'))
def step_click_tab(manager_page: ManagerPLIPage, tab: str) -> None:
    manager_page.click_tab(tab)


@when(parsers.parse('the user clicks the red "{button}" button'))
def step_click_red_button(manager_page: ManagerPLIPage, button: str) -> None:
    manager_page.click_dashboard_button(button)


@when(parsers.parse('the user clicks the blue "{button}" button'))
def step_click_blue_button(manager_page: ManagerPLIPage, button: str) -> None:
    if button == "Save All KPIs":
        manager_page.click_save_all_kpis()
    elif button == "Add Revenue":
        manager_page.click_dashboard_button("Add Revenue")
    elif button == "Show PLI":
        manager_page.click_dashboard_button("Show PLI")
    elif button == "Add Revenue (submit)":
        manager_page.submit_add_revenue()
    else:
        manager_page.click_dashboard_button(button)


@when('the user clicks the blue "Add Revenue" button at the bottom of the form')
def step_click_blue_add_revenue_submit(manager_page: ManagerPLIPage) -> None:
    manager_page.submit_add_revenue()


@when(parsers.parse('the user clicks the dark "{button}" button'))
def step_click_dark_button(manager_page: ManagerPLIPage, button: str) -> None:
    if button == "Add More KPI":
        manager_page.click_add_more_kpi()
    else:
        pytest.fail(f"Step click dark '{button}' not implemented: unknown dark button")


@when(parsers.parse('the user fills the "{form_name}" form with the following details:'))
def step_fill_form(manager_page: ManagerPLIPage, form_name: str, datatable) -> None:
    data = _kv_table(datatable)
    if form_name == "Add New Employee":
        manager_page.fill_add_employee(data)
    elif form_name == "Add Revenue":
        manager_page.fill_add_revenue(data)
    else:
        pytest.fail(f"Step fill form '{form_name}' not implemented: unknown form")


@when(parsers.parse('the user selects "{value}" from the "{field}" dropdown'))
def step_select_dropdown(manager_page: ManagerPLIPage, value: str, field: str) -> None:
    if field == "Quarter":
        manager_page.select_quarter(value)
    elif field == "Emp_ID":
        manager_page.select_emp_id(value)
    elif field == "Employee":
        # Story says "7777 — Priya Sharma" — extract the emp id
        emp_id = value.split(" ")[0].strip()
        manager_page.select_revenue_employee(emp_id)
    else:
        pytest.fail(f"Step select '{value}' from '{field}' dropdown not implemented")


@when(parsers.parse('the user fills KPI row #{idx:d} with the following details:'))
def step_fill_kpi_row(manager_page: ManagerPLIPage, idx: int, datatable) -> None:
    raw = _kv_table(datatable)
    # Strip the "KPI #N " prefix from each key
    cleaned: dict[str, str] = {}
    prefix = f"KPI #{idx} "
    for k, v in raw.items():
        if k.startswith(prefix):
            cleaned[k[len(prefix):]] = v
        else:
            cleaned[k] = v
    manager_page.fill_kpi_row(idx - 1, cleaned)


@when(parsers.parse('the user clicks the "{emp_id}" link in the Emp ID column'))
def step_click_emp_id_link(manager_page: ManagerPLIPage, emp_id: str) -> None:
    manager_page.click_pli_emp_id(emp_id)


# ---------- Then -----------------------------------------------------------

@then(parsers.parse('the URL changes to "{url}"'))
def step_url_changes_to(
    manager_page: ManagerPLIPage, captured_values, url: str
) -> None:
    manager_page.wait_for_url(url, timeout=DEFAULT_TIMEOUT)
    actual = manager_page.current_url()
    assert captured_values.assert_match(
        f"URL changes to {url}", expected=url, actual=actual
    ), f"URL mismatch: expected {url!r}, got {actual!r}"


@then(parsers.parse('the URL changes back to "{url}"'))
def step_url_changes_back_to(
    manager_page: ManagerPLIPage, captured_values, url: str
) -> None:
    manager_page.wait_for_url(url, timeout=DEFAULT_TIMEOUT)
    actual = manager_page.current_url()
    assert captured_values.assert_match(
        f"URL changes back to {url}", expected=url, actual=actual
    ), f"URL mismatch: expected {url!r}, got {actual!r}"


@then(parsers.parse(
    'the navigation bar displays "{label}" with the manager name "{name}"'
))
def step_nav_welcome(
    manager_page: ManagerPLIPage, captured_values, label: str, name: str
) -> None:
    welcome = manager_page.welcome_text()
    mgr = manager_page.manager_name_text()
    captured_values.add("Welcome label text", welcome)
    captured_values.add("Manager name displayed", mgr)
    assert captured_values.assert_match(
        "Navigation welcome + manager name",
        expected=f"{label} | {name}",
        actual=f"{welcome} | {mgr}",
    ), f"Expected '{label} | {name}', got '{welcome} | {mgr}'"


@then('the following four tiles are visible on the dashboard:')
def step_four_tiles_visible(
    manager_page: ManagerPLIPage, captured_values, datatable
) -> None:
    tiles = _single_col(datatable)
    for tile in tiles:
        ok = manager_page.tile_is_visible(tile)
        captured_values.add_component(f"Tile visible: {tile}", 1 if ok else 0, group="dashboard_tiles")
    assert captured_values.assert_count(
        "Dashboard tiles visible count", group="dashboard_tiles", actual=len(tiles)
    ), f"Expected {len(tiles)} tiles, captured fewer"


@then(parsers.parse('the "{tab}" tab is selected by default'))
def step_tab_selected_default(
    manager_page: ManagerPLIPage, captured_values, tab: str
) -> None:
    actual = manager_page.active_tab_text()
    assert captured_values.assert_match(
        f"Default active tab is {tab}", expected=tab, actual=actual
    ), f"Expected default tab {tab!r}, got {actual!r}"


@then(parsers.parse('the "{form_name}" form is displayed'))
def step_form_displayed(
    manager_page: ManagerPLIPage, captured_values, form_name: str
) -> None:
    if form_name == "Add New Employee":
        actual = manager_page.add_employee_form_is_displayed()
    elif form_name == "Set Performance":
        actual = manager_page.set_performance_form_is_displayed()
    elif form_name == "Add Revenue":
        actual = manager_page.add_revenue_form_is_displayed()
    else:
        pytest.fail(f"Step form displayed '{form_name}' not implemented")
        return
    assert captured_values.assert_match(
        f"{form_name} form is displayed",
        expected="displayed",
        actual="displayed" if actual else "not displayed",
    )


@then(parsers.parse('a browser alert is displayed with the text "{message}"'))
def step_alert_displayed(
    manager_page: ManagerPLIPage, dialog_recorder, captured_values, message: str
) -> None:
    # The dialog from the React submit handler fires on a microtask after the
    # click returns. Poll briefly for the expected message before asserting.
    deadline_ms = 8000
    elapsed = 0
    while elapsed < deadline_ms and dialog_recorder.last != message:
        manager_page.page.wait_for_timeout(100)
        elapsed += 100
    actual = dialog_recorder.last or ""
    assert captured_values.assert_match(
        "Browser alert text", expected=message, actual=actual
    ), f"Expected alert text {message!r}, got {actual!r}"


@then(parsers.parse(
    'a row with Emp ID "{emp_id}" and Name "{name}" appears in the Manage Employees table'
))
def step_employee_row_appears(
    manager_page: ManagerPLIPage, captured_values, emp_id: str, name: str
) -> None:
    found = manager_page.employee_row_visible(emp_id, name)
    captured_values.add("New employee Emp ID in table", emp_id)
    captured_values.add("New employee Name in table", name)
    assert captured_values.assert_match(
        f"Employee row appears for {emp_id} {name}",
        expected="visible",
        actual="visible" if found else "missing",
    )


@then('the Manage Revenue panel is displayed')
def step_manage_revenue_panel(
    manager_page: ManagerPLIPage, captured_values
) -> None:
    # Asserting visibility of one of the Manage Revenue buttons confirms the panel
    actual = manager_page.manage_revenue_button_visible("Add Revenue")
    assert captured_values.assert_match(
        "Manage Revenue panel is displayed",
        expected="displayed",
        actual="displayed" if actual else "not displayed",
    )


@then('the following buttons are visible on the panel:')
def step_panel_buttons_visible(
    manager_page: ManagerPLIPage, captured_values, datatable
) -> None:
    buttons = _single_col(datatable)
    for b in buttons:
        ok = manager_page.manage_revenue_button_visible(b)
        captured_values.add_component(
            f"Panel button visible: {b}", 1 if ok else 0, group="panel_buttons"
        )
    assert captured_values.assert_count(
        "Manage Revenue panel buttons count",
        group="panel_buttons",
        actual=len(buttons),
    ), f"Expected {len(buttons)} buttons visible"


@then(parsers.parse(
    'the "{field}" field is auto-filled with "{value}" and is read-only'
))
def step_field_auto_filled_readonly(
    manager_page: ManagerPLIPage, captured_values, field: str, value: str
) -> None:
    if field != "Employee Name":
        pytest.fail(f"Step auto-filled readonly for field '{field}' not implemented")
    actual_value = manager_page.revenue_employee_name_value()
    is_readonly = manager_page.revenue_employee_name_is_readonly()
    captured_values.add("Auto-filled Employee Name value", actual_value)
    captured_values.add("Auto-filled Employee Name read-only", str(is_readonly))
    composite_actual = f"{actual_value}|{is_readonly}"
    composite_expected = f"{value}|True"
    assert captured_values.assert_match(
        f"{field} auto-filled with {value} and read-only",
        expected=composite_expected,
        actual=composite_actual,
    ), f"Expected {composite_expected}, got {composite_actual}"


@then('the PLI Data table contains a row with the following values:')
def step_pli_row_values(
    manager_page: ManagerPLIPage, captured_values, datatable
) -> None:
    expected = _kv_table(datatable)
    emp_id = expected.get("Emp ID", "")
    actual = manager_page.pli_row_values(emp_id)
    for k, v in actual.items():
        captured_values.add(f"PLI Data row {k}", v)
    assert captured_values.assert_match(
        f"PLI Data row for Emp ID {emp_id}",
        expected=str(expected),
        actual=str(actual),
    ), f"Expected {expected}, got {actual}"


@then('the "PLI Data" table is displayed')
def step_pli_data_table_displayed(
    manager_page: ManagerPLIPage, captured_values
) -> None:
    ok = manager_page.pli_data_table_visible()
    assert captured_values.assert_match(
        "PLI Data table is displayed",
        expected="displayed",
        actual="displayed" if ok else "not displayed",
    )


@then('the page header shows the following values:')
def step_page_header_values(
    manager_page: ManagerPLIPage, captured_values, datatable
) -> None:
    expected = _kv_table(datatable)
    actual = {}
    for field in expected.keys():
        actual[field] = manager_page.header_field_value(field)
        captured_values.add(f"PLI Detail header {field}", actual[field])
    assert captured_values.assert_match(
        "PLI Detail header fields",
        expected=str(expected),
        actual=str(actual),
    ), f"Expected {expected}, got {actual}"


@then('the KPI breakdown table contains exactly two rows')
def step_kpi_table_two_rows(
    manager_page: ManagerPLIPage, captured_values
) -> None:
    count = manager_page.kpi_breakdown_row_count()
    assert captured_values.assert_match(
        "KPI breakdown row count",
        expected="2",
        actual=str(count),
    ), f"Expected 2 KPI rows, got {count}"


@then(parsers.parse('KPI breakdown row {idx:d} has the following values:'))
def step_kpi_row_values(
    manager_page: ManagerPLIPage, captured_values, idx: int, datatable
) -> None:
    expected = _kv_table(datatable)
    actual = manager_page.kpi_row_by_index(idx)
    for k, v in actual.items():
        captured_values.add(f"KPI row {idx} {k}", v)
    # also record components for the cross-row aggregate later
    try:
        elig = actual.get("Eligible", "0").replace(",", "")
        captured_values.add_component(
            f"KPI row {idx} Eligible", elig, group="kpi_eligible"
        )
        pay = actual.get("Payable", "0").replace(",", "")
        captured_values.add_component(
            f"KPI row {idx} Payable", pay, group="kpi_payable"
        )
    except Exception:
        pass
    assert captured_values.assert_match(
        f"KPI breakdown row {idx} matches",
        expected=str(expected),
        actual=str(actual),
    ), f"Expected row {idx}={expected}, got {actual}"


@then('the Total row at the bottom of the KPI breakdown table shows:')
def step_kpi_total_row(
    manager_page: ManagerPLIPage, captured_values, datatable
) -> None:
    expected = _kv_table(datatable)
    actual = manager_page.total_row()
    for k, v in actual.items():
        captured_values.add(f"KPI Total row {k}", v)
    assert captured_values.assert_match(
        "KPI breakdown Total row",
        expected=str(expected),
        actual=str(actual),
    ), f"Expected total row {expected}, got {actual}"


@then(parsers.parse(
    'the Total Eligible value "{total}" equals the sum of the two row '
    'Eligible values "{a}" and "{b}"'
))
def step_total_eligible_sum(
    captured_values, total: str, a: str, b: str
) -> None:
    assert captured_values.assert_sum(
        f"Total Eligible {total} = {a} + {b}",
        group="kpi_eligible",
        actual=total.replace(",", ""),
    ), f"Sum mismatch: expected total={total} from {a} + {b}"


@then(parsers.parse(
    'the Total Payable value "{total}" equals the sum of the two row '
    'Payable values "{a}" and "{b}"'
))
def step_total_payable_sum(
    captured_values, total: str, a: str, b: str
) -> None:
    assert captured_values.assert_sum(
        f"Total Payable {total} = {a} + {b}",
        group="kpi_payable",
        actual=total.replace(",", ""),
    ), f"Sum mismatch: expected total={total} from {a} + {b}"
