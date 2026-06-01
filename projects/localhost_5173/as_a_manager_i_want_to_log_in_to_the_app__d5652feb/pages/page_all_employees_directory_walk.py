from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class AllEmployeesDirectoryWalkPage(BasePage):
    """Page object covering login, dashboard hop, and the All Employees
    directory walk (filter/search/pagination) used by the
    story_1_all_employees_directory_walk feature."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation / login
    # ------------------------------------------------------------------
    def open(self, base_url: str) -> None:
        self.page.goto(base_url, wait_until="domcontentloaded", timeout=20000)

    def expect_login_screen(self) -> str:
        heading = self.first_visible(self.selectors("login", "heading"), timeout=10000)
        return heading.inner_text().strip()

    def fill_manager_id(self, value: str) -> None:
        self.fill_any(self.selectors("login", "manager_id_input"), value, timeout=10000)

    def fill_password(self, value: str) -> None:
        self.fill_any(self.selectors("login", "password_input"), value, timeout=10000)

    def click_login(self) -> None:
        self.click_any(self.selectors("login", "submit_button"), timeout=10000)

    def current_url(self) -> str:
        return self.page.url

    def wait_for_url_exact(self, url: str, timeout: int = 15000) -> None:
        self.page.wait_for_url(url, timeout=timeout)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def click_view_all_employees(self) -> None:
        self.click_any(self.selectors("dashboard", "view_all_employees"), timeout=10000)

    # ------------------------------------------------------------------
    # All-Employees directory
    # ------------------------------------------------------------------
    def expect_directory_loaded(self) -> None:
        header = self.first_visible(self.selectors("all_employees", "header"), timeout=15000)
        expect(header).to_be_visible(timeout=10000)

    def set_filter(self, label: str) -> str:
        """Set the department filter dropdown to the option whose visible text
        starts with `label` (e.g. 'All Employees' matches 'All Employees (100)')."""
        dropdown = self.first_visible(self.selectors("all_employees", "filter_dropdown"), timeout=10000)
        target_text = self.page.evaluate(
            """({sel, label}) => {
                const root = document.querySelector(sel);
                if (!root) return null;
                const match = Array.from(root.options).find(o => (o.text || '').trim().toLowerCase().startsWith(label.toLowerCase()));
                return match ? match.text : null;
            }""",
            {"sel": self.selectors("all_employees", "filter_dropdown")[0], "label": label},
        )
        if not target_text:
            raise AssertionError(
                f"No option starting with {label!r} in filter dropdown {self.selectors('all_employees', 'filter_dropdown')}"
            )
        dropdown.select_option(label=target_text)
        return target_text

    def current_filter_label(self) -> str:
        dropdown = self.first_visible(self.selectors("all_employees", "filter_dropdown"), timeout=5000)
        return self.page.evaluate(
            "(sel) => { const r = document.querySelector(sel); return r ? r.options[r.selectedIndex].text : ''; }",
            self.selectors("all_employees", "filter_dropdown")[0],
        )

    def clear_search_box(self) -> None:
        box = self.first_visible(self.selectors("all_employees", "search_box"), timeout=10000)
        box.fill("")

    def search_box_value(self) -> str:
        box = self.first_visible(self.selectors("all_employees", "search_box"), timeout=5000)
        return box.input_value()

    def visible_row_count(self) -> int:
        rows = self.page.locator(self.selectors("all_employees", "rows")[0])
        return rows.count()

    def read_visible_rows(self) -> list[dict[str, str]]:
        """Return one dict per visible row keyed by column header."""
        return self.page.evaluate(
            """() => {
                const headers = Array.from(document.querySelectorAll('table thead th')).map(th => th.textContent.trim());
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                return rows.map(tr => {
                    const cells = Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
                    const out = {};
                    headers.forEach((h, i) => { out[h] = cells[i] || ''; });
                    return out;
                });
            }"""
        )

    def page_indicator_text(self) -> str:
        loc = self.first_visible(self.selectors("all_employees", "page_indicator"), timeout=10000)
        return loc.inner_text().strip()

    def parse_page_indicator(self) -> tuple[int, int]:
        import re
        m = re.search(r"Page\s+(\d+)\s+of\s+(\d+)", self.page_indicator_text())
        if not m:
            raise AssertionError(f"Could not parse page indicator from {self.page_indicator_text()!r}")
        return int(m.group(1)), int(m.group(2))

    def click_next_page(self) -> None:
        self.click_any(self.selectors("all_employees", "next_page"), timeout=10000)

    def click_prev_page(self) -> None:
        self.click_any(self.selectors("all_employees", "prev_page"), timeout=10000)

    def next_page_is_disabled(self) -> bool:
        return self.page.locator(self.selectors("all_employees", "next_page")[0]).first.is_disabled()

    def prev_page_is_disabled(self) -> bool:
        return self.page.locator(self.selectors("all_employees", "prev_page")[0]).first.is_disabled()
