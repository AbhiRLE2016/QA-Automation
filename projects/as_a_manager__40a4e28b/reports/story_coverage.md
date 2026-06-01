# Story Coverage — PASS

**Test:** `tests/test_story_1_download_filtered_employees_csv.py::test_manager_filters_the_all_employees_page_by_finance_department_and_downloads_the_csv`
**Pytest summary:** 1 passed, 0 failed, 0 skipped, 0 errors — 00:00:18
**Captured-values log:** 47 entries (19 values, 25 aggregate components, 4 assertions)
**Overall verdict:** ✅ **PASS** — every story requirement was exercised, every assertion matched expected.

---

## Requirements checklist

| # | Requirement (from `user_story.txt`) | Verdict | Evidence |
|---|---|---|---|
| 1 | As a manager (signed-in manager role) | ✅ | `given_user_is_manager` logged in id=499, welcome banner contained `Nitin Kumar` (captured 09:37:01); dashboard URL `http://localhost:5173/dashboard/499` |
| 2 | Open the "All Employees" page | ✅ | `when_user_opens_page` navigated to `http://localhost:5173/all-employees/499`; heading `Company Directory — All departments — 100 employees in scope` captured 09:37:03 |
| 3 | Pick a finance department from the filter dropdown (or "All Employees") | ✅ | `when_user_picks_department` selected `Finance`, filter banner `Showing Finance`, pagination total 25 captured 09:37:05 |
| 4 | Click "Download CSV" | ✅ | `when_user_clicks_label` saved `employees_Finance_2026-05-19.csv` at 09:37:07 |
| 5 | A CSV file of the filtered employee list is downloaded | ✅ | `then_csv_downloaded` — 2284 bytes, 25 rows; assertion `All CSV rows belong to Finance` 25==25 ✅ |
| 6 | Manager can quickly find a specific employee in the downloaded list | ✅ | `then_find_specific_employee` — emp 503 row `503 / Aarav Mehta / Finance`; assertion `Employee 503 name in CSV` `Aarav Mehta`==`Aarav Mehta` ✅ |
| 7 | Downloaded list is clean and filtered for stakeholders without needing database access | ✅ | `then_csv_clean_and_filtered` — headers `Emp ID,Name,Email,Grade,Department,Project,Manager,Status` (no raw DB cols); assertions `CSV is clean` False==False ✅ and `CSV row count matches UI total` 25==25 ✅ |

---

## Captured values (kind=value)

| ts | Label | Value |
|---|---|---|
| 09:37:01 | Logged-in manager id (input) | `499` |
| 09:37:01 | Welcome banner text | `Employee Hub\nWELCOME\nNitin Kumar\nLogout` |
| 09:37:01 | Dashboard URL | `http://localhost:5173/dashboard/499` |
| 09:37:03 | All Employees URL | `http://localhost:5173/all-employees/499` |
| 09:37:03 | Page heading | `Company Directory\nAll departments — 100 employees in scope` |
| 09:37:05 | Selected department | `Finance` |
| 09:37:05 | Filter banner after select | `Showing Finance` |
| 09:37:05 | Visible rows on filtered page (first page) | `10` |
| 09:37:05 | Pagination total after filter | `25` |
| 09:37:07 | Downloaded file path | `C:\Users\RLE2016\Downloads\employees_Finance_2026-05-19.csv` |
| 09:37:07 | Downloaded file name | `employees_Finance_2026-05-19.csv` |
| 09:37:09 | Downloaded CSV size (bytes) | `2284` |
| 09:37:09 | CSV headers | `Emp ID,Name,Email,Grade,Department,Project,Manager,Status` |
| 09:37:09 | CSV row count | `25` |
| 09:37:11 | Looked-up employee id | `503` |
| 09:37:11 | Looked-up employee row | `503 / Aarav Mehta / Finance` |
| 09:37:12 | CSV exposes raw DB columns? | `False` |
| 09:37:12 | CSV total rows for Finance | `25` |
| 09:37:12 | Expected total rows from UI pagination | `25` |

## Data assertions (kind=assertion)

| ts | Label | Expected | Actual | Verdict |
|---|---|---|---|---|
| 09:37:09 | All CSV rows belong to Finance | `25` | `25` | ✅ |
| 09:37:11 | Employee 503 name in CSV | `Aarav Mehta` | `Aarav Mehta` | ✅ |
| 09:37:12 | CSV is clean (no raw DB columns) | `False` | `False` | ✅ |
| 09:37:12 | CSV row count matches UI total for Finance | `25` | `25` | ✅ |

---

## 📊 Aggregate & math verifications

### `csv_dept_match` — per-row "department == Finance" flags, summed

**Operation:** sum of 25 per-row component flags (1 if `row.Department == "Finance"`, else 0)

| Emp ID row | flag |
|---|---|
| 503 | 1 |
| 521 | 1 |
| 522 | 1 |
| 523 | 1 |
| 524 | 1 |
| 544 | 1 |
| 545 | 1 |
| 546 | 1 |
| 547 | 1 |
| 548 | 1 |
| 549 | 1 |
| 550 | 1 |
| 551 | 1 |
| 552 | 1 |
| 553 | 1 |
| 554 | 1 |
| 555 | 1 |
| 556 | 1 |
| 557 | 1 |
| 558 | 1 |
| 559 | 1 |
| 560 | 1 |
| 561 | 1 |
| 562 | 1 |
| 563 | 1 |

**Computed:** 1 × 25 = **25**
**Actual on-screen total (UI pagination + CSV row count):** **25**
**Tolerance:** 0 (exact integer match)
**Verdict:** ✅ — every CSV row's Department equals `Finance`. The summed flag total (25) matches the UI pagination total (25) and the CSV total row count (25).

---

## Negative scenarios

`user_story.txt` describes only the positive happy path. `user_data.json` contains no rows with `expected_message`, `expected_error`, or `should_succeed: false`. The feature file has no negative `Scenario` or `Scenario Outline`. → **No negative scenarios in scope; nothing to audit here.**

---

## Gaps in coverage

No gaps against the requirements actually stated in `user_story.txt`. Possible enhancements (not gaps against the story as written):
- Story mentions "(or All Employees)" as a filter option but only `Finance` was exercised. The "or" makes this acceptable, but an "All departments" path would broaden confidence.
- No negative case is asserted (e.g. unauthorized user, missing manager session, malformed CSV) — story did not require one.

---

**Recommendation:** Ship. Story 1 (download filtered employees CSV) is fully and verifiably covered — login → All Employees → Finance filter → download → row count, per-row department purity, target-employee lookup, and clean headers all assert green.
