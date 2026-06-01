from __future__ import annotations

from typing import Iterable

from playwright.sync_api import Page, expect

from .base_page import BasePage


_DEFAULT_TIMEOUT_MS = 15000


class ManagerFlowPage(BasePage):
    """Single page object covering every screen the story exercises:
    login, dashboard, add-employee, set-performance, add-revenue, show-pli,
    show-employee-pli. Every Playwright call lives here; step defs only
    invoke these methods."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---- generic helpers -------------------------------------------------

    def _sel(self, group: str, key: str) -> str:
        items = self.selectors(group, key)
        if not items:
            raise AssertionError(f"No selector configured for {group}.{key}")
        return items[0]

    def _all_sels(self, group: str, key: str) -> list[str]:
        return self.selectors(group, key) or []

    def open(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=20000)

    def current_url(self) -> str:
        return self.page.url

    def expect_url(self, expected: str, timeout: int = _DEFAULT_TIMEOUT_MS) -> None:
        expect(self.page).to_have_url(expected, timeout=timeout)

    # ---- login -----------------------------------------------------------

    def fill_input_by_label(self, label: str, value: str) -> None:
        """Generic 'type X into the Y input'. Maps the human label to the
        locators captured during discovery."""
        key = self._label_to_key(label)
        sel = self._sel(key["group"], key["key"])
        loc = self.page.locator(sel).first
        expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        loc.fill(value)

    def click_button(self, label: str) -> None:
        """Generic 'click the X button'. Uses a text-based locator scoped
        to <button>."""
        button = self.page.get_by_role("button", name=label, exact=False).first
        expect(button).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        button.click()

    def select_dropdown_by_label(self, label: str, value: str) -> None:
        key = self._label_to_key(label, kind="select")
        sel = self._sel(key["group"], key["key"])
        loc = self.page.locator(sel).first
        expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        try:
            loc.select_option(value=value)
        except Exception:
            loc.select_option(label=value)

    # ---- dashboard reads -------------------------------------------------

    def welcome_text(self) -> str:
        return self.page.locator(self._sel("dashboard", "welcome_label")).first.inner_text().strip()

    def manager_name_text(self) -> str:
        return self.page.locator(self._sel("dashboard", "manager_name")).first.inner_text().strip()

    def tile_labels_visible(self, labels: Iterable[str]) -> dict[str, bool]:
        out = {}
        for lab in labels:
            loc = self.page.locator(f"main p:has-text('{lab}')").first
            out[lab] = loc.is_visible()
        return out

    def selected_tab_label(self) -> str:
        for tab_label in ("Manage Employees", "Manage Revenue"):
            btn = self.page.locator(f"button:has-text('{tab_label}')").first
            try:
                aria = btn.get_attribute("aria-selected")
                klass = (btn.get_attribute("class") or "")
            except Exception:
                aria, klass = None, ""
            if aria == "true" or "active" in klass.lower() or "bg-" in klass and "white" in klass:
                return tab_label
        return ""

    def manage_employees_tab_active(self) -> bool:
        # On first load the Manage Employees tab is active; we detect it via
        # the table that is rendered only in that tab.
        try:
            return self.page.locator("button:has-text('Manage Employees')").first.is_visible() and \
                   self.page.locator("table thead").first.is_visible()
        except Exception:
            return False

    def manage_revenue_panel_visible(self) -> bool:
        # The Manage Revenue panel exposes the Add Revenue button.
        try:
            return self.page.locator("button:has-text('Add Revenue')").first.is_visible()
        except Exception:
            return False

    def revenue_panel_buttons_visible(self, labels: Iterable[str]) -> dict[str, bool]:
        out = {}
        for lab in labels:
            loc = self.page.locator(f"button:has-text('{lab}')").first
            out[lab] = loc.is_visible()
        return out

    def employee_row_text(self, emp_id: str) -> str | None:
        rows = self.page.locator("tbody tr").all()
        for r in rows:
            try:
                txt = r.inner_text()
            except Exception:
                continue
            if emp_id in txt:
                return " ".join(txt.split())
        return None

    def click_manage_revenue_tab(self) -> None:
        self.page.locator("button:has-text('Manage Revenue')").first.click()
        expect(self.page.locator("button:has-text('Add Revenue')").first).to_be_visible(
            timeout=_DEFAULT_TIMEOUT_MS
        )

    def click_add_employee_top(self) -> None:
        self.page.locator("button:has(span:has-text('Add Employee')), button:has-text('Add Employee')").first.click()

    # ---- add employee ----------------------------------------------------

    def add_employee_form_visible(self) -> bool:
        loc = self.page.locator(self._sel("add_employee", "heading")).first
        try:
            expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
            return True
        except Exception:
            return False

    def fill_add_employee(self, **fields) -> None:
        mapping = {
            "Employee Name": "employee_name",
            "Employee ID": "employee_id",
            "Grade": "grade",
            "Employment Type": "employment_type",
            "CTC": "ctc",
            "Fixed Pay": "fixed_pay",
            "Variable Pay": "variable_pay",
            "Employee Status": "employee_status",
            "Email": "email",
        }
        for label, value in fields.items():
            key = mapping.get(label)
            if key is None:
                continue
            self.page.locator(self._sel("add_employee", key)).first.fill(str(value))

    def select_add_employee_dropdown(self, label: str, value: str) -> None:
        key = {"Department": "department", "Project": "project"}.get(label)
        if key is None:
            raise AssertionError(f"Unknown add-employee dropdown: {label}")
        loc = self.page.locator(self._sel("add_employee", key)).first
        expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        loc.select_option(value=value)

    def submit_add_employee(self) -> None:
        self.page.locator(self._sel("add_employee", "submit_button")).first.click()

    # ---- set performance -------------------------------------------------

    def set_performance_form_visible(self) -> bool:
        loc = self.page.locator(self._sel("set_performance", "heading")).first
        try:
            expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
            return True
        except Exception:
            return False

    def select_quarter(self, value: str) -> None:
        loc = self.page.locator(self._sel("set_performance", "quarter")).first
        loc.select_option(value=value)

    def select_emp_id(self, value: str) -> None:
        loc = self.page.locator(self._sel("set_performance", "emp_id")).first
        loc.select_option(value=value)

    def fill_kpi(self, index: int, *, name: str | None = None, threshold: str | None = None,
                 target: str | None = None, achieved: str | None = None,
                 weightage: str | None = None) -> None:
        if name is not None:
            self.page.locator(f"#kpi-name-{index}").first.fill(str(name))
        if threshold is not None:
            self.page.locator(f"#threshold-{index}").first.fill(str(threshold))
        if target is not None:
            self.page.locator(f"#target-{index}").first.fill(str(target))
        if achieved is not None:
            self.page.locator(f"#achieved-{index}").first.fill(str(achieved))
        if weightage is not None:
            self.page.locator(f"#weightage-{index}").first.fill(str(weightage))

    def click_add_more_kpi(self) -> None:
        self.page.locator(self._sel("set_performance", "add_more_kpi")).first.click()

    def click_save_all_kpis(self) -> None:
        self.page.locator(self._sel("set_performance", "save_all_kpis")).first.click()

    # ---- add revenue -----------------------------------------------------

    def add_revenue_form_visible(self) -> bool:
        loc = self.page.locator(self._sel("add_revenue", "heading")).first
        try:
            expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
            return True
        except Exception:
            return False

    def select_revenue_employee(self, label_text: str) -> None:
        loc = self.page.locator(self._sel("add_revenue", "employee_dropdown")).first
        expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        # `label_text` may be "7777 — Priya Sharma"; the <option> value is just
        # the emp id ("7777"). Use the leading numeric token if present.
        head = label_text.strip().split()[0]
        try:
            loc.select_option(value=head)
        except Exception:
            loc.select_option(label=label_text)

    def employee_name_readonly_value(self) -> str:
        loc = self.page.locator(self._sel("add_revenue", "employee_name_readonly")).first
        return loc.input_value()

    def employee_name_readonly_is_readonly(self) -> bool:
        loc = self.page.locator(self._sel("add_revenue", "employee_name_readonly")).first
        return bool(loc.evaluate("e => !!e.readOnly"))

    def fill_add_revenue(self, **fields) -> None:
        mapping = {
            "Revenue ID": "revenue_id",
            "Month": "month",
            "Cost": "cost",
            "Cost_Currency": "cost_currency",
            "Revenue": "revenue",
            "Revenue Currency": "revenue_currency",
        }
        for label, value in fields.items():
            key = mapping.get(label)
            if key is None:
                continue
            self.page.locator(self._sel("add_revenue", key)).first.fill(str(value))

    def submit_add_revenue(self) -> None:
        self.page.locator(self._sel("add_revenue", "submit_button")).first.click()

    # ---- show PLI --------------------------------------------------------

    def show_pli_table_visible(self) -> bool:
        loc = self.page.locator(self._sel("show_pli", "table_title")).first
        try:
            expect(loc).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
            return True
        except Exception:
            return False

    def pli_row_values(self, emp_id: str) -> dict[str, str] | None:
        """Return the values of the row whose Emp ID button matches `emp_id`."""
        row_sel = f"tbody tr:has(button:has-text('{emp_id}'))"
        row = self.page.locator(row_sel).first
        try:
            expect(row).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        except Exception:
            return None
        cells = row.locator("td").all()
        if len(cells) < 3:
            return None
        return {
            "Emp ID": cells[0].inner_text().strip(),
            "Eligible Amount (USD)": cells[1].inner_text().strip(),
            "Payable Amount (USD)": cells[2].inner_text().strip(),
        }

    def click_pli_emp_link(self, emp_id: str) -> None:
        link = self.page.locator(f"tbody tr:has(button:has-text('{emp_id}')) button").first
        expect(link).to_be_visible(timeout=_DEFAULT_TIMEOUT_MS)
        link.click()

    # ---- show-employee-pli ----------------------------------------------

    def employee_pli_header_text(self, must_contain: str | None = None,
                                 timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> str:
        """Return the header h1 text once `must_contain` (e.g. 'Name: Priya
        Sharma') appears, since the page renders the header asynchronously
        after fetching the employee detail."""
        if must_contain:
            try:
                expect(self.page.locator("h1", has_text=must_contain).first).to_be_visible(
                    timeout=timeout_ms
                )
            except Exception:
                pass
        return self.page.locator("h1").first.inner_text()

    def kpi_rows(self) -> list[list[str]]:
        """All KPI rows except the final 'Total' row (which has only 3 cells)."""
        rows = self.page.locator("table tbody tr").all()
        out: list[list[str]] = []
        for r in rows:
            cells = r.locator("td").all()
            values = [c.inner_text().strip() for c in cells]
            if values and values[0].lower() == "total":
                continue
            out.append(values)
        return out

    def total_row_values(self) -> dict[str, str] | None:
        rows = self.page.locator("table tbody tr").all()
        for r in rows:
            cells = r.locator("td").all()
            values = [c.inner_text().strip() for c in cells]
            if values and values[0].lower() == "total":
                if len(values) >= 3:
                    return {"Eligible": values[1], "Payable": values[2]}
        return None

    # ---- label mapping ---------------------------------------------------

    _LOGIN_LABELS = {"manager id": ("login", "manager_id_input"),
                     "password": ("login", "password_input")}

    def _label_to_key(self, label: str, kind: str = "input") -> dict:
        norm = label.strip().lower()
        if norm in self._LOGIN_LABELS:
            grp, key = self._LOGIN_LABELS[norm]
            return {"group": grp, "key": key}
        # Fallback: treat as add-employee field (only used by the generic
        # step). The dedicated `fill_add_employee` path is preferred.
        raise AssertionError(
            f"No locator mapping for label {label!r}; add it to ManagerFlowPage._LOGIN_LABELS"
        )
