from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class DeleteEmployeePage(BasePage):
    """Page object for the end-to-end delete-employee flow:
    login -> dashboard Manage Employees -> select row -> Bulk Delete (acts as
    the 'Delete Employee' button) -> confirm modal -> All Employees search to
    verify the row is gone."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def open(self, base_url: str) -> None:
        self.page.goto(base_url, wait_until="domcontentloaded", timeout=20000)

    def fill_manager_id(self, value: str) -> None:
        self.fill_any(self.selectors("login", "manager_id_input"), value, timeout=10000)

    def fill_password(self, value: str) -> None:
        self.fill_any(self.selectors("login", "password_input"), value, timeout=10000)

    def click_login(self) -> None:
        self.click_any(self.selectors("login", "submit_button"), timeout=10000)

    def current_url(self) -> str:
        return self.page.url

    def wait_for_url_contains(self, fragment: str, timeout: int = 15000) -> None:
        self.page.wait_for_url(re.compile(re.escape(fragment) + r"$"), timeout=timeout)

    def wait_for_url_endswith(self, suffix: str, timeout: int = 15000) -> None:
        self.page.wait_for_function(
            "([s]) => location.pathname.endsWith(s) || location.href.endsWith(s)",
            arg=[suffix],
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Dashboard / Manage Employees tab
    # ------------------------------------------------------------------
    def click_manage_employees_tab(self) -> None:
        self.click_any(self.selectors("dashboard", "manage_employees_tab"), timeout=10000)

    def manage_employees_tab_is_selected(self) -> bool:
        """Returns True when the Manage Employees tab is active. The dashboard
        renders the Add Employee / Bulk Upload / View All Employees / Bulk Delete
        toolbar AND an employees table only when this tab is active, so the
        most reliable signal is the visibility of that table + toolbar."""
        try:
            expect(self.page.locator(self.selectors("dashboard", "employees_table")[0]).first
                   ).to_be_visible(timeout=5000)
            expect(self.page.locator(self.selectors("dashboard", "bulk_delete_button")[0]).first
                   ).to_be_visible(timeout=5000)
            return True
        except Exception:
            return False

    def find_employee_row(self, name: str):
        """Return the <tr> locator on the dashboard whose Name cell equals `name`."""
        row = self.page.locator(
            f"table tbody tr:has(td:text-is('{name}'))"
        ).first
        expect(row).to_be_visible(timeout=10000)
        return row

    def employee_row_exists(self, name: str) -> bool:
        try:
            count = self.page.locator(
                f"table tbody tr:has(td:text-is('{name}'))"
            ).count()
            return count > 0
        except Exception:
            return False

    def select_employee_row(self, name: str) -> str:
        """Tick the row's selection checkbox. Returns the Emp ID from the row
        (Employee ID column is the second cell after the checkbox)."""
        row = self.find_employee_row(name)
        checkbox = row.locator("input[type=checkbox]").first
        checkbox.check(timeout=10000)
        # Pull the Emp ID from the row (column 2: idx 1 = Employee ID; cell 0 holds the checkbox)
        emp_id = row.locator("td").nth(1).inner_text().strip()
        return emp_id

    def bulk_delete_button_text(self) -> str:
        btn = self.first_visible(self.selectors("dashboard", "bulk_delete_button"), timeout=10000)
        return btn.inner_text().strip()

    def bulk_delete_is_enabled(self) -> bool:
        btn = self.page.locator(self.selectors("dashboard", "bulk_delete_button")[0]).first
        return btn.is_enabled()

    def click_delete_employee(self) -> None:
        """Click the toolbar 'Bulk Delete (N)' button — the dashboard's
        primary 'Delete Employee' button that becomes enabled once a row is
        selected. It opens the confirm modal."""
        self.click_any(self.selectors("dashboard", "bulk_delete_button"), timeout=10000)

    # ------------------------------------------------------------------
    # Confirm modal
    # ------------------------------------------------------------------
    def confirm_modal_is_open(self) -> bool:
        try:
            expect(self.page.locator(self.selectors("dashboard", "confirm_modal_heading")[0]).first
                   ).to_be_visible(timeout=5000)
            return True
        except Exception:
            return False

    def confirm_modal_message_text(self) -> str:
        loc = self.first_visible(self.selectors("dashboard", "confirm_modal_message"), timeout=5000)
        return loc.inner_text().strip()

    def confirm_delete(self) -> None:
        """Click the 'Delete N' button inside the confirm modal. The app also
        fires a JS alert ('Bulk delete complete: ...') which is auto-accepted
        by the dialog_recorder fixture."""
        self.click_any(self.selectors("dashboard", "confirm_delete_button"), timeout=10000)

    # ------------------------------------------------------------------
    # View All Employees navigation
    # ------------------------------------------------------------------
    def click_view_all_employees(self) -> None:
        self.click_any(self.selectors("dashboard", "view_all_employees"), timeout=10000)

    # ------------------------------------------------------------------
    # All Employees page
    # ------------------------------------------------------------------
    def expect_directory_loaded(self) -> None:
        header = self.first_visible(self.selectors("all_employees", "header"), timeout=15000)
        expect(header).to_be_visible(timeout=10000)

    def set_filter(self, label: str) -> str:
        """Set the department filter dropdown to the option whose visible text
        starts with `label` (e.g. 'All Employees' matches 'All Employees (99)')."""
        dropdown_sel = self.selectors("all_employees", "filter_dropdown")[0]
        self.first_visible(self.selectors("all_employees", "filter_dropdown"), timeout=10000)
        target = self.page.evaluate(
            """({sel, label}) => {
                const root = document.querySelector(sel);
                if (!root) return null;
                const opt = Array.from(root.options).find(o =>
                    (o.text || '').trim().toLowerCase().startsWith(label.toLowerCase())
                );
                return opt ? {value: opt.value, text: opt.text} : null;
            }""",
            {"sel": dropdown_sel, "label": label},
        )
        if not target:
            raise AssertionError(
                f"No option starting with {label!r} in filter dropdown {dropdown_sel}"
            )
        self.page.locator(dropdown_sel).first.select_option(value=target["value"])
        return target["text"]

    def type_search(self, value: str) -> None:
        box = self.first_visible(self.selectors("all_employees", "search_box"), timeout=10000)
        box.fill(value)

    def search_box_value(self) -> str:
        box = self.first_visible(self.selectors("all_employees", "search_box"), timeout=5000)
        return box.input_value()

    def empty_state_message(self) -> str:
        """Return the visible 'No employees match ...' text in the table body
        (or the whole tbody text if no message is shown)."""
        tbody = self.page.locator("table tbody").first
        expect(tbody).to_be_visible(timeout=10000)
        return tbody.inner_text().strip()

    def visible_row_count(self) -> int:
        # Only count rows that have a real <td> (not the empty-state row,
        # which the app renders without td/th cells in some implementations).
        rows = self.page.locator("table tbody tr").filter(has=self.page.locator("td"))
        return rows.count()

    def employee_appears_in_table(self, name: str) -> bool:
        try:
            count = self.page.locator(
                f"table tbody tr:has(td:text-is('{name}'))"
            ).count()
            return count > 0
        except Exception:
            return False
