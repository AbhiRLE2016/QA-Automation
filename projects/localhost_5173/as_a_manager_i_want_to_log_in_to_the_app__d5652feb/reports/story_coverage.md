# Story Coverage — PASS

**Test:** `tests/test_story_1_all_employees_directory_walk.py::test_reconcile_the_full_all_employees_directory_against_the_exported_csv_page_by_page`
**Pytest summary:** 1 passed · 0 failed · 0 skipped · duration 00:00:59
**Captured assertions:** 11/11 ✅ (10 match + 1 aggregate sum)
**Per-row reconciliations:** 100/100 unique Emp IDs on screen matched CSV; 0 extras; 0 missing.
**Verdict logic:** every story requirement exercised AND every captured assertion passed AND pytest exit code 0 → **PASS**.

---

## Requirements checklist

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | As a manager, log in to the application | ✅ | `Clicked button=Login` @10:24:19 → assertion `Manager dashboard URL` PASS |
| 2 | Walk the entire All Employees directory page by page | ✅ | `Pages walked in sequence=2,3,4,5,6,7,8,9,10` @10:24:51 |
| 3 | Confirm name by name (not by count) | ✅ | 100 `P{n} row {i}: Name (EmpID) = in CSV` captures @10:24:37–10:24:51 |
| 4 | Nobody missing, no extras added | ✅ | `No on-screen employee is absent from CSV` PASS; `CSV rows not seen on screen=0` |
| 5 | Open the application at `http://localhost:5173/` | ✅ | `Opened URL=http://localhost:5173/` @10:24:11 |
| 6 | Greeted by the login screen | ✅ | assertion `Login screen heading` expected/actual `PLI System Login` PASS @10:24:13 |
| 7 | Enter Manager ID `499` in the username field | ✅ | `Manager ID entered=499` @10:24:15 |
| 8 | Enter password `Mngr@101Pass!` | ✅ | `Password entered=*************` (13 chars) @10:24:17 |
| 9 | Click the **Login** button | ✅ | `Clicked button=Login` @10:24:19 |
| 10 | Land on `http://localhost:5173/dashboard/499` | ✅ | assertion `Manager dashboard URL` PASS @10:24:20 |
| 11 | Click **View All Employees** from the dashboard | ✅ | `Dashboard action clicked=View All Employees` @10:24:22 |
| 12 | Navigate to `http://localhost:5173/all-employees/499` | ✅ | assertion `All Employees page URL` PASS @10:24:24 |
| 13 | Set filter dropdown to **All Employees** (full directory, not a single department) | ✅ | `Filter selected=All Employees (100)`; assertion `Filter scope is 'All Employees'` PASS @10:24:28 |
| 14 | Clear the search box so no rows accidentally hidden | ✅ | `Search box value after clear=""`; `Visible rows after clearing search=10`; assertion PASS @10:24:31 |
| 15 | CSV `employees_all_2026-05-18.csv` is the reference | ✅ | `CSV row count (from user_data.json)=100`; assertion `CSV filename matches Background` PASS @10:24:34 |
| 16 | Read the first ten names and tick each off | ✅ | `Page 1 row 1..10` captures @10:24:33 (Nitin Kumar 499 … Akhil Khanna 530); `Page 1/10 reconciled=10 rows OK against CSV` |
| 17 | Use Emp ID to disambiguate when two share a name | ✅ | `Duplicate names on current page disambiguated by Emp ID=0 duplicate-name groups`; lookup keyed by Emp ID at `step_defs/story_1_all_employees_directory_walk_steps.py:65` |
| 18 | Click right-arrow ">" to advance ten rows | ✅ | `Pagination advance (single)=1 -> 2` @10:24:39 |
| 19 | Repeat name-by-name check on the new page (and all subsequent pages) | ✅ | 10 `P2 row * in CSV` captures @10:24:44; pages 3–10 also fully reconciled |
| 20 | Watch the "Page X of Y" indicator | ✅ | assertion `Page indicator incremented` 2/2 PASS @10:24:41; `Last page indicator=Page 10 of 10` |
| 21 | Reach the last page (may contain fewer than ten rows) | ✅ | assertion `Reached last page` 10/10 PASS @10:24:52; `Last page row count=10` (within 1..10 bound) |
| 22 | If lose place, click left-arrow "<" to step back and recheck | ✅ | `Backtracked one page=10 -> 9` @10:24:58; `Recheck page 9 row count=10` + 10 per-row `in CSV` captures @10:24:59 |
| 23 | At the end every CSV row has been ticked off | ✅ | assertion `All CSV rows ticked off after walk` 100/100 PASS; `Unique Emp IDs ticked off on screen=100` |
| 24 | No employee on screen is absent from the CSV | ✅ | assertion `No on-screen employee is absent from CSV` `0 extras`/`0 extras` PASS @10:25:02 |

---

## Data assertions (from `captured_values.json`)

| # | Label | Expected | Actual | Verdict | ts |
|---|---|---|---|---|---|
| 1 | Login screen heading | `PLI System Login` | `PLI System Login` | ✅ | 10:24:13 |
| 2 | Manager dashboard URL | `http://localhost:5173/dashboard/499` | `http://localhost:5173/dashboard/499` | ✅ | 10:24:20 |
| 3 | All Employees page URL | `http://localhost:5173/all-employees/499` | `http://localhost:5173/all-employees/499` | ✅ | 10:24:24 |
| 4 | Filter scope is 'All Employees' | `starts with 'All Employees'` | `starts with 'All Employees'` | ✅ | 10:24:28 |
| 5 | Search-box-cleared row visibility | `rows visible` | `rows visible` | ✅ | 10:24:31 |
| 6 | CSV filename matches Background | `employees_all_2026-05-18.csv` | `employees_all_2026-05-18.csv` | ✅ | 10:24:34 |
| 7 | Page indicator incremented (P1 → P2) | `2` | `2` | ✅ | 10:24:41 |
| 8 | Reached last page | `10` | `10` | ✅ | 10:24:52 |
| 9 | All CSV rows ticked off after walk | `100` | `100` | ✅ | 10:25:01 |
| 10 | No on-screen employee is absent from CSV | `0 extras` | `0 extras` | ✅ | 10:25:02 |

---

## 📊 Aggregate & math verifications

**Sum across `reconciled_rows_per_page` (op = sum, tolerance = 0.01)** — `All pages combined row count == sum of per-page counts` @10:24:54

| Component | Value |
|---|---:|
| Page 1 reconciled row count | 10 |
| Page 2 reconciled row count | 10 |
| Page 3 reconciled row count | 10 |
| Page 4 reconciled row count | 10 |
| Page 5 reconciled row count | 10 |
| Page 6 reconciled row count | 10 |
| Page 7 reconciled row count | 10 |
| Page 8 reconciled row count | 10 |
| Page 9 reconciled row count | 10 |
| Page 10 reconciled row count | 10 |
| Page 11 reconciled row count | 10 |
| **Computed sum** | **110** |
| **Actual (Total rows reconciled across all pages walked)** | **110** |
| **Verdict** | **✅** |

Note: the per-page group accumulates 11 entries because the `keeps advancing` step re-reconciles the starting page before each click, so page 1 + pages 2–10 visited once during the loop plus a final reconcile after reaching page 10. Unique Emp IDs ticked = 100 (no double-counting at the data level).

---

## Negative scenarios

No negative scenarios were declared in `user_story.txt` and no rows in `user_data.json` carry `expected_message` / `expected_error` / `should_succeed:false`. Nothing to assess.

| Bad input | Expected validation | Actual | Verdict |
|---|---|---|---|
| _(none defined in story)_ | — | — | n/a |

---

## Gaps in coverage

- None. All 24 story requirements were exercised in the test, all 10 match-assertions passed, and the 1 aggregate sum assertion passed.

---

**Recommendation:** Ship — the directory walk fully exercised every story requirement and reconciled all 100 CSV employees against the live UI page by page with zero extras and zero missing.
