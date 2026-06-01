from __future__ import annotations

from typing import Iterable

from playwright.sync_api import Locator

from pages.base_page import BasePage


class ManagerPLIEndToEnd(BasePage):
    BASE_URL = "http://localhost:5173"
    DEFAULT_TIMEOUT = 10000

    def _sel(self, page_key: str, key: str) -> list[str]:
        return self.selectors(page_key, key)

    def _format_template(self, page_key: str, key: str, **kwargs) -> list[str]:
        raw = self._sel(page_key, key)
        return [s.format(**kwargs) for s in raw]

    # ---------- Generic ----------
    def open_url(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=15000)

    def current_url(self) -> str:
        return self.page.url

    def wait_for_url(self, url: str, timeout: int = 10000) -> None:
        self.page.wait_for_url(url, timeout=timeout)

    # ---------- Login ----------
    def type_manager_id(self, value: str) -> None:
        loc = self.first_visible(self._sel("login", "manager_id"))
        loc.fill(value)

    def type_password(self, value: str) -> None:
        loc = self.first_visible(self._sel("login", "password"))
        loc.fill(value)

    def click_login(self) -> None:
        self.click_any(self._sel("login", "login_btn"))

    # ---------- Dashboard ----------
    def manager_name_in_nav(self) -> str:
        loc = self.first_visible(self._sel("dashboard", "nav_manager_name"))
        return (loc.inner_text() or "").strip()

    def welcome_word_in_nav(self) -> str:
        loc = self.first_visible(self._sel("dashboard", "nav_welcome"))
        return (loc.inner_text() or "").strip()

    def tile_is_visible(self, tile_key: str) -> bool:
        try:
            loc = self.first_visible(self._sel("dashboard", tile_key), timeout=4000)
            return loc.is_visible()
        except AssertionError:
            return False

    def visible_tile_labels(self) -> list[str]:
        labels: list[str] = []
        for key, label in [
            ("tile_total_employees", "Total Employees"),
            ("tile_total_revenue", "Total Revenue"),
            ("tile_growth_pct", "Growth %"),
            ("tile_active_departments", "Active Departments"),
        ]:
            if self.tile_is_visible(key):
                labels.append(label)
        return labels

    def manage_employees_tab_is_selected(self) -> bool:
        tab = self.page.locator("button:has-text('Manage Employees')").first
        cls = tab.get_attribute("class") or ""
        return "text-blue-600" in cls or "border-blue-600" in cls

    def click_manage_employees_tab(self) -> None:
        self.click_any(self._sel("dashboard", "tab_manage_employees"))

    def click_manage_revenue_tab(self) -> None:
        self.click_any(self._sel("dashboard", "tab_manage_revenue"))

    def click_green_add_employee(self) -> None:
        self.click_any(self._sel("dashboard", "btn_add_employee_green"))

    def manage_revenue_panel_visible(self) -> bool:
        try:
            self.page.locator("button:has-text('Add Revenue')").first.wait_for(state="visible", timeout=5000)
            return True
        except Exception:
            return False

    def manage_revenue_buttons_visible(self) -> list[str]:
        found: list[str] = []
        mapping = {
            "Add Revenue": "btn_add_revenue",
            "Upload Review": "btn_upload_review",
            "Set Performance": "btn_set_performance",
            "Show PLI": "btn_show_pli",
            "Modify Performance": "btn_modify_performance",
        }
        for label, key in mapping.items():
            try:
                loc = self.first_visible(self._sel("dashboard", key), timeout=3000)
                if loc.is_visible():
                    found.append(label)
            except AssertionError:
                continue
        return found

    def click_set_performance(self) -> None:
        self.click_any(self._sel("dashboard", "btn_set_performance"))

    def click_blue_add_revenue(self) -> None:
        self.click_any(self._sel("dashboard", "btn_add_revenue"))

    def click_blue_show_pli(self) -> None:
        self.click_any(self._sel("dashboard", "btn_show_pli"))

    def employee_row_cells(self, emp_id: str) -> list[str]:
        sels = self._format_template("dashboard", "employee_row_tpl", emp_id=emp_id)
        for s in sels:
            row = self.page.locator(s).first
            try:
                row.wait_for(state="visible", timeout=8000)
                cells = row.locator("td")
                return [(cells.nth(i).inner_text() or "").strip() for i in range(cells.count())]
            except Exception:
                continue
        return []

    # ---------- Add Employee form ----------
    def add_employee_form_header_text(self) -> str:
        loc = self.first_visible(self._sel("add_employee", "form_header"))
        return (loc.inner_text() or "").strip()

    def add_employee_fill(self, field_key: str, value: str) -> None:
        loc = self.first_visible(self._sel("add_employee", field_key))
        loc.fill(value)

    def add_employee_select(self, field_key: str, label: str) -> None:
        loc = self.first_visible(self._sel("add_employee", field_key))
        loc.select_option(label=label)

    def click_blue_add_employee_submit(self) -> None:
        self.click_any(self._sel("add_employee", "submit_btn"))

    # ---------- Set Performance form ----------
    def set_performance_form_header_text(self) -> str:
        loc = self.first_visible(self._sel("set_performance", "form_header"))
        return (loc.inner_text() or "").strip()

    def select_quarter(self, value: str) -> None:
        loc = self.first_visible(self._sel("set_performance", "quarter"))
        loc.select_option(value=value)

    def select_emp_id_for_kpi(self, value: str) -> None:
        loc = self.first_visible(self._sel("set_performance", "emp_id"))
        loc.select_option(value=value)

    def kpi_fill(self, field_key: str, idx: int, value: str) -> None:
        sels = self._format_template("set_performance", field_key, idx=idx)
        loc = self.first_visible(sels)
        loc.fill(value)

    def click_add_more_kpi(self) -> None:
        self.click_any(self._sel("set_performance", "btn_add_more_kpi"))

    def click_save_all_kpis(self) -> None:
        self.click_any(self._sel("set_performance", "btn_save_all"))

    # ---------- Add Revenue form ----------
    def add_revenue_form_header_text(self) -> str:
        loc = self.first_visible(self._sel("add_revenue", "form_header"))
        return (loc.inner_text() or "").strip()

    def select_employee_for_revenue(self, label: str) -> None:
        loc = self.first_visible(self._sel("add_revenue", "employee_dropdown"))
        loc.select_option(label=label)

    def revenue_employee_name_value(self) -> str:
        loc = self.first_visible(self._sel("add_revenue", "employee_name_readonly"))
        return (loc.input_value() or "").strip()

    def revenue_employee_name_is_readonly(self) -> bool:
        loc = self.first_visible(self._sel("add_revenue", "employee_name_readonly"))
        ro = loc.get_attribute("readonly")
        return ro is not None

    def add_revenue_fill(self, field_key: str, value: str) -> None:
        loc = self.first_visible(self._sel("add_revenue", field_key))
        loc.fill(value)

    def click_blue_add_revenue_submit(self) -> None:
        self.click_any(self._sel("add_revenue", "submit_btn"))

    # ---------- Show PLI ----------
    def show_pli_header_text(self) -> str:
        loc = self.first_visible(self._sel("show_pli", "header"))
        return (loc.inner_text() or "").strip()

    def show_pli_table_visible(self) -> bool:
        try:
            self.first_visible(self._sel("show_pli", "table"), timeout=8000)
            return True
        except AssertionError:
            return False

    def show_pli_row_for_emp_id(self, emp_id: str) -> list[str]:
        rows = self.page.locator("tbody tr")
        for i in range(rows.count()):
            r = rows.nth(i)
            first_cell = r.locator("td").first
            txt = (first_cell.inner_text() or "").strip()
            if txt == emp_id:
                cells = r.locator("td")
                return [(cells.nth(j).inner_text() or "").strip() for j in range(cells.count())]
        return []

    def click_pli_row_emp_link(self, emp_id: str) -> None:
        self.page.locator(f"tbody tr td button:text-is(\"{emp_id}\")").first.click()

    # ---------- Show Employee PLI detail ----------
    def emp_pli_header_field(self, label: str) -> str:
        # Header pills appear in either <span> or <div>; the leaf element has
        # exactly "Label: value" as its text. We walk the candidates and pick
        # the deepest one (no child element re-introducing the label) so e.g.
        # "Manager:" does not return "Manager ID: ...".
        for tag in ("span", "div", "p"):
            selector = f"{tag}:has-text('{label}:')"
            candidates = self.page.locator(selector)
            n = candidates.count()
            for i in range(n):
                el = candidates.nth(i)
                try:
                    text = (el.inner_text() or "").strip()
                except Exception:
                    continue
                # Skip parents that wrap multiple pills (would include newlines)
                if "\n" in text:
                    continue
                if text.startswith(f"{label}:"):
                    return text[len(label) + 1:].strip()
        return ""

    def emp_pli_kpi_rows(self) -> list[list[str]]:
        result: list[list[str]] = []
        rows = self.page.locator("tbody tr")
        n = rows.count()
        for i in range(n):
            r = rows.nth(i)
            cells = r.locator("td")
            cn = cells.count()
            row_texts = [(cells.nth(j).inner_text() or "").strip() for j in range(cn)]
            if not row_texts:
                continue
            if cn >= 8 and row_texts[0].lower() != "total":
                result.append(row_texts)
        return result

    def emp_pli_total_row(self) -> list[str]:
        rows = self.page.locator("tbody tr, tfoot tr")
        n = rows.count()
        for i in range(n):
            r = rows.nth(i)
            cells = r.locator("td")
            cn = cells.count()
            row_texts = [(cells.nth(j).inner_text() or "").strip() for j in range(cn)]
            if row_texts and row_texts[0].lower() == "total":
                return row_texts
        return []
