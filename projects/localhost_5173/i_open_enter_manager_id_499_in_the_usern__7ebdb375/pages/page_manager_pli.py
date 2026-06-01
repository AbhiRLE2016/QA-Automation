from __future__ import annotations

from playwright.sync_api import Page, expect

from .base_page import BasePage

DEFAULT_TIMEOUT = 15000


class ManagerPLIPage(BasePage):
    """Page object for the full Manager onboards employee + PLI flow."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---- Navigation -------------------------------------------------------
    def open(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)

    def current_url(self) -> str:
        return self.page.url

    def wait_for_url(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.page.wait_for_url(url, timeout=timeout)

    # ---- Login ------------------------------------------------------------
    def fill_login_field(self, field: str, value: str) -> None:
        key = {
            "Manager ID": "manager_id_input",
            "Password": "password_input",
        }[field]
        self.fill_any(self.selectors("login", key), value)

    def click_login(self) -> None:
        self.click_any(self.selectors("login", "login_button"))

    # ---- Dashboard --------------------------------------------------------
    def manager_name_text(self) -> str:
        locator = self.first_visible(self.selectors("dashboard", "manager_name"))
        return locator.inner_text().strip()

    def welcome_text(self) -> str:
        locator = self.first_visible(self.selectors("dashboard", "welcome_label"))
        return locator.inner_text().strip()

    def tile_is_visible(self, tile: str) -> bool:
        key = {
            "Total Employees": "tile_total_employees",
            "Total Revenue": "tile_total_revenue",
            "Growth %": "tile_growth",
            "Active Departments": "tile_active_departments",
        }[tile]
        locator = self.page.locator(self.selectors("dashboard", key)[0])
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def active_tab_text(self) -> str:
        emp_tab = self.page.locator(
            self.selectors("dashboard", "tab_manage_employees")[0]
        )
        rev_tab = self.page.locator(
            self.selectors("dashboard", "tab_manage_revenue")[0]
        )
        emp_classes = emp_tab.get_attribute("class") or ""
        rev_classes = rev_tab.get_attribute("class") or ""
        if "border-blue-600" in emp_classes or "text-blue-600" in emp_classes:
            return "Manage Employees"
        if "border-blue-600" in rev_classes or "text-blue-600" in rev_classes:
            return "Manage Revenue"
        return "Manage Employees"

    def click_tab(self, tab_name: str) -> None:
        key = {
            "Manage Employees": "tab_manage_employees",
            "Manage Revenue": "tab_manage_revenue",
        }[tab_name]
        self.click_any(self.selectors("dashboard", key))

    def click_add_employee(self) -> None:
        self.click_any(self.selectors("dashboard", "add_employee_button"))

    def click_dashboard_button(self, button_name: str) -> None:
        key_map = {
            "Add Revenue": "add_revenue_button",
            "Upload Review": "upload_review_button",
            "Set Performance": "set_performance_button",
            "Show PLI": "show_pli_button",
            "Modify Performance": "modify_performance_button",
        }
        self.click_any(self.selectors("dashboard", key_map[button_name]))

    def manage_revenue_button_visible(self, button_name: str) -> bool:
        key_map = {
            "Add Revenue": "add_revenue_button",
            "Upload Review": "upload_review_button",
            "Set Performance": "set_performance_button",
            "Show PLI": "show_pli_button",
            "Modify Performance": "modify_performance_button",
        }
        locator = self.page.locator(
            self.selectors("dashboard", key_map[button_name])[0]
        )
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def employee_row_visible(self, emp_id: str, name: str) -> bool:
        row = self.page.locator(
            f"table tbody tr:has(td:has-text('{emp_id}')):has(td:has-text('{name}'))"
        )
        expect(row.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    # ---- Add Employee form -----------------------------------------------
    def add_employee_form_is_displayed(self) -> bool:
        locator = self.page.locator(
            self.selectors("add_employee", "heading")[0]
        )
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def fill_add_employee(self, data: dict) -> None:
        text_map = {
            "Employee Name": "employee_name_input",
            "Employee ID": "employee_id_input",
            "Grade": "grade_input",
            "Employment Type": "employment_type_input",
            "CTC": "ctc_input",
            "Fixed Pay": "fixed_pay_input",
            "Variable Pay": "variable_pay_input",
            "Employee Status": "employee_status_input",
            "Email": "email_input",
        }
        dept_map = {"Business": "0", "Engineering": "1", "Operations": "2", "Finance": "3"}
        project_map = {"HRMS Revamp": "201"}

        for field, key in text_map.items():
            if field in data:
                self.fill_any(self.selectors("add_employee", key), str(data[field]))

        if "Department" in data:
            value = dept_map.get(data["Department"], data["Department"])
            self.page.locator(
                self.selectors("add_employee", "department_select")[0]
            ).select_option(value)

        if "Project" in data:
            value = project_map.get(data["Project"], data["Project"])
            self.page.locator(
                self.selectors("add_employee", "project_select")[0]
            ).select_option(value)

    def submit_add_employee(self) -> None:
        self.click_any(self.selectors("add_employee", "submit_button"))

    # ---- Set Performance --------------------------------------------------
    def set_performance_form_is_displayed(self) -> bool:
        locator = self.page.locator(
            self.selectors("set_performance", "heading")[0]
        )
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def select_quarter(self, quarter: str) -> None:
        sel = self.selectors("set_performance", "quarter_select")[0]
        self.page.locator(sel).select_option(quarter)

    def select_emp_id(self, emp_id: str) -> None:
        sel = self.selectors("set_performance", "emp_id_select")[0]
        self.page.locator(sel).select_option(emp_id)

    def fill_kpi_row(self, idx: int, data: dict) -> None:
        """idx is 0-based."""
        key_map = {
            "Name": "kpi_name_input",
            "Threshold": "threshold_input",
            "Target": "target_input",
            "Achieved": "achieved_input",
            "Weightage": "weightage_input",
        }
        for field, key in key_map.items():
            if field in data:
                template = self.selectors("set_performance", key)[0]
                selector = template.replace("{idx}", str(idx))
                self.fill_any([selector], str(data[field]))

    def click_add_more_kpi(self) -> None:
        self.click_any(self.selectors("set_performance", "add_more_kpi_button"))

    def click_save_all_kpis(self) -> None:
        self.click_any(self.selectors("set_performance", "save_all_kpis_button"))

    # ---- Add Revenue form ------------------------------------------------
    def add_revenue_form_is_displayed(self) -> bool:
        locator = self.page.locator(
            self.selectors("add_revenue", "heading")[0]
        )
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def select_revenue_employee(self, emp_id: str) -> None:
        sel = self.selectors("add_revenue", "employee_select")[0]
        self.page.locator(sel).select_option(emp_id)

    def revenue_employee_name_value(self) -> str:
        sel = self.selectors("add_revenue", "employee_name_input")[0]
        return self.page.locator(sel).input_value()

    def revenue_employee_name_is_readonly(self) -> bool:
        sel = self.selectors("add_revenue", "employee_name_input")[0]
        readonly = self.page.locator(sel).get_attribute("readonly")
        return readonly is not None

    def fill_add_revenue(self, data: dict) -> None:
        key_map = {
            "Revenue ID": "revenue_id_input",
            "Month": "month_input",
            "Cost": "cost_input",
            "Cost_Currency": "cost_currency_input",
            "Cost Currency": "cost_currency_input",
            "Revenue": "revenue_input",
            "Revenue Currency": "revenue_currency_input",
        }
        for field, key in key_map.items():
            if field in data:
                self.fill_any(self.selectors("add_revenue", key), str(data[field]))

    def submit_add_revenue(self) -> None:
        self.click_any(self.selectors("add_revenue", "submit_button"))

    # ---- Show PLI ---------------------------------------------------------
    def pli_data_table_visible(self) -> bool:
        locator = self.page.locator(
            self.selectors("show_pli", "heading")[0]
        )
        expect(locator.first).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return True

    def pli_row_values(self, emp_id: str) -> dict:
        row = self.page.locator(
            f"table tbody tr:has(button:has-text('{emp_id}'))"
        ).first
        expect(row).to_be_visible(timeout=DEFAULT_TIMEOUT)
        cells = row.locator("td").all_inner_texts()
        return {
            "Emp ID": cells[0].strip() if len(cells) > 0 else "",
            "Eligible Amount (USD)": cells[1].strip() if len(cells) > 1 else "",
            "Payable Amount (USD)": cells[2].strip() if len(cells) > 2 else "",
        }

    def click_pli_emp_id(self, emp_id: str) -> None:
        locator = self.page.locator(f"table button:has-text('{emp_id}')").first
        expect(locator).to_be_visible(timeout=DEFAULT_TIMEOUT)
        locator.click()

    # ---- Employee PLI Detail ---------------------------------------------
    def header_field_value(self, field: str) -> str:
        label_map = {
            "Emp ID": "Emp ID:",
            "Name": "Name:",
            "Manager ID": "Manager ID:",
            "Manager": "Manager:",
        }
        label_text = label_map[field]
        container = self.page.locator(f"span:has-text('{label_text}')").first
        expect(container).to_be_visible(timeout=DEFAULT_TIMEOUT)
        full = container.inner_text().strip()
        return full.split(":", 1)[1].strip() if ":" in full else full

    def kpi_breakdown_rows(self) -> list[list[str]]:
        rows = self.page.locator("table tbody tr").all()
        out = []
        for r in rows:
            cells = r.locator("td").all_inner_texts()
            if cells:
                out.append([c.strip() for c in cells])
        return out

    def kpi_breakdown_row_count(self) -> int:
        rows = self.kpi_breakdown_rows()
        return sum(1 for r in rows if r and r[0] != "Total")

    def kpi_row_by_index(self, idx: int) -> dict:
        """idx is 1-based; returns labelled row."""
        rows = [r for r in self.kpi_breakdown_rows() if r and r[0] != "Total"]
        row = rows[idx - 1]
        return {
            "KPI": row[0],
            "Quarter": row[1],
            "Threshold": row[2],
            "Target": row[3],
            "Achieved": row[4],
            "Weightage": row[5],
            "Eligible": row[6],
            "Payable": row[7],
        }

    def total_row(self) -> dict:
        rows = [r for r in self.kpi_breakdown_rows() if r and r[0] == "Total"]
        if not rows:
            raise AssertionError("No 'Total' row found in KPI breakdown table")
        total = rows[0]
        return {"Eligible": total[1], "Payable": total[2]}

    # ---- Setup helpers (cleanup) ------------------------------------------
    def delete_employee_if_present(self, emp_id: str) -> None:
        sel = f"button[aria-label='Delete employee {emp_id}']"
        btn = self.page.locator(sel)
        try:
            btn.wait_for(state="visible", timeout=2500)
            btn.click()
            confirm = self.page.locator(
                self.selectors("dashboard", "delete_modal_confirm")[0]
            )
            confirm.wait_for(state="visible", timeout=3000)
            confirm.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
