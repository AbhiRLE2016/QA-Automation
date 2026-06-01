from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from playwright.sync_api import Page, expect

from .base_page import BasePage


class AllEmployeesCsvPage(BasePage):
    """POM covering: login -> manager dashboard -> All Employees -> filter -> Download CSV."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # --- login ---------------------------------------------------------

    def goto_login(self, base_url: str, timeout_ms: int = 20000) -> None:
        self.page.goto(base_url, wait_until="domcontentloaded", timeout=timeout_ms)
        expect(self.first_visible(self.selectors("login", "manager_id_input"))).to_be_visible(timeout=timeout_ms)

    def login_as_manager(self, manager_id: str, password: str, timeout_ms: int = 15000) -> None:
        self.fill_any(self.selectors("login", "manager_id_input"), manager_id, timeout=timeout_ms)
        self.fill_any(self.selectors("login", "password_input"), password, timeout=timeout_ms)
        self.click_any(self.selectors("login", "submit"), timeout=timeout_ms)
        self.page.wait_for_url("**/dashboard/**", timeout=timeout_ms)

    def welcome_name(self, expected: str | None = None, timeout_ms: int = 15000) -> str:
        """Return the name shown in the nav 'Welcome' block.
        If `expected` is given, wait until that text appears before returning."""
        if expected:
            try:
                self.page.locator(f"nav :text-is('{expected}')").first.wait_for(
                    state="visible", timeout=timeout_ms
                )
            except Exception:
                # Fall back to waiting for any nav paragraph that isn't 'Welcome'.
                try:
                    self.page.wait_for_function(
                        """() => {
                            const ps = document.querySelectorAll('nav p');
                            for (const p of ps) {
                                const t = (p.textContent || '').trim();
                                if (t && t.toLowerCase() !== 'welcome') return true;
                            }
                            return false;
                        }""",
                        timeout=timeout_ms,
                    )
                except Exception:
                    pass
        return self.page.locator("nav").inner_text(timeout=5000)

    # --- navigate to All Employees ------------------------------------

    def open_all_employees(self, timeout_ms: int = 15000) -> None:
        self.click_any(self.selectors("dashboard", "view_all_employees"), timeout=timeout_ms)
        self.page.wait_for_url("**/all-employees/**", timeout=timeout_ms)
        expect(self.first_visible(self.selectors("all_employees", "page_heading"))).to_be_visible(timeout=timeout_ms)

    def all_employees_url(self) -> str:
        return self.page.url

    def page_heading_text(self) -> str:
        return self.first_visible(self.selectors("all_employees", "page_heading")).inner_text(timeout=5000)

    # --- filter --------------------------------------------------------

    def pick_department(self, department: str, timeout_ms: int = 10000) -> str:
        select = self.first_visible(self.selectors("all_employees", "dept_filter"), timeout=timeout_ms)
        select.select_option(department, timeout=timeout_ms)
        self.page.wait_for_function(
            "(value) => document.querySelector('#dept-filter') && document.querySelector('#dept-filter').value === value",
            arg=department,
            timeout=timeout_ms,
        )
        return self.banner_text()

    def banner_text(self) -> str:
        loc = self.page.locator("main").locator("text=/Showing/")
        loc.first.wait_for(state="visible", timeout=5000)
        return loc.first.inner_text(timeout=5000).strip()

    def visible_row_count(self) -> int:
        return self.page.locator("main table tbody tr").count()

    def pagination_total(self) -> int | None:
        """Parse 'Showing 1-10 of 25' -> 25. None when not present."""
        try:
            txt = self.page.locator("main").locator("text=/of\\s+\\d+/").first.inner_text(timeout=2000)
        except Exception:
            return None
        m = re.search(r"of\s+(\d+)", txt)
        return int(m.group(1)) if m else None

    # --- download ------------------------------------------------------

    def click_download_csv(self, timeout_ms: int = 20000) -> Path:
        """Click the Download CSV button and return the saved file path.

        conftest.py configures Chromium (via CDP `Browser.setDownloadBehavior`)
        to save downloads NATIVELY to `~/Downloads` (or PLAYWRIGHT_DOWNLOADS_DIR)
        with the server's suggested filename — same as a real user clicking the
        link. So we just trigger the click and wait for the file to appear."""
        import os
        import time as _time

        downloads_dir = Path(
            os.environ.get(
                "PLAYWRIGHT_DOWNLOADS_DIR",
                str(Path.home() / "Downloads"),
            )
        )
        try:
            downloads_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            downloads_dir = Path("reports") / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

        before = {p.name for p in downloads_dir.glob("*") if p.is_file()}

        try:
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self.click_any(
                    self.selectors("all_employees", "download_csv"),
                    timeout=timeout_ms,
                )
            download = dl_info.value
            suggested = download.suggested_filename or ""
        except Exception:
            self.click_any(
                self.selectors("all_employees", "download_csv"),
                timeout=timeout_ms,
            )
            suggested = ""

        deadline = _time.time() + max(timeout_ms / 1000, 10)
        target: Path | None = None
        while _time.time() < deadline:
            current = list(downloads_dir.glob("*"))
            if suggested:
                guess = downloads_dir / suggested
                if guess.exists() and guess.stat().st_size > 0:
                    target = guess
                    break
            new_files = [p for p in current if p.is_file() and p.name not in before]
            new_files = [p for p in new_files if not p.name.endswith(".crdownload")]
            if new_files:
                new_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                candidate = new_files[0]
                if candidate.stat().st_size > 0:
                    target = candidate
                    break
            _time.sleep(0.25)

        if target is None:
            raise AssertionError(
                f"Download did not appear in {downloads_dir} within "
                f"{timeout_ms}ms (suggested={suggested!r})"
            )
        return target

    # --- CSV helpers ---------------------------------------------------

    @staticmethod
    def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
        text = Path(path).read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = [dict(r) for r in reader]
        headers = list(reader.fieldnames or [])
        return headers, rows

    @staticmethod
    def find_employee_in_csv(rows: list[dict[str, str]], emp_id: str) -> dict[str, str] | None:
        for r in rows:
            if (r.get("Emp ID") or r.get("EmpID") or "").strip() == str(emp_id).strip():
                return r
        return None

    @staticmethod
    def departments_in_csv(rows: list[dict[str, str]]) -> list[str]:
        return [(r.get("Department") or "").strip() for r in rows]

    @staticmethod
    def has_db_columns(headers: list[str]) -> bool:
        """Returns True if CSV exposes raw DB internals (id/uuid/created_at/updated_at/etc)."""
        sensitive = {"id", "uuid", "_id", "created_at", "updated_at", "password", "ssn", "salary_raw"}
        return any(h.strip().lower() in sensitive for h in headers)
