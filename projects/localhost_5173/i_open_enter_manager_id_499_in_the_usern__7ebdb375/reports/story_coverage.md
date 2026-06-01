# Story Coverage — ⚠️ PARTIAL

**Test:** `tests/test_story_1_verify_all_employees_against_csv.py::test_manager_499_verifies_every_csv_employee_name_appears_in_the_all_employees_table_across_pagination`
**pytest result:** 1 passed, 0 failed, 0 skipped — duration 00:00:34
**Generated:** 2026-05-20T11:48:00

---

## ⚠️ Top-of-report banner — Row coverage incomplete

> **Row coverage incomplete: 0 of 100 rows verified (0 per-row capture entries, expected 100; 0 of 1 aggregate assertions, expected 1).**
>
> pytest-html reports the test PASSED in 34 seconds, but `reports/captured_values.json`
> stops at 11:46:34 — exactly the moment the "Employees table is displayed" assertion
> fired. The subsequent ~12 seconds of test execution (the pagination walk, every
> per-row `cap.add(...)` call inside `_reconcile_current_page`, and the final
> `cap.assert_match("Every CSV name appears on the UI", ...)` aggregate) produced
> **zero** entries in the capture log.
>
> Because this audit is strictly evidence-based, the central claim of the story —
> "every CSV name appears on the UI" — is **not evidenced**, regardless of the
> green pytest result. Verdict downgraded to PARTIAL.

---

## Preconditions

| Label | Status | Time |
|---|---|---|
| App reachable at base URL | ✅ | 11:46:18 |

---

## Requirements checklist

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Open `http://localhost:5173/` | ✅ | `Opened URL=http://localhost:5173/` @11:46:18; prerequisite `App reachable at base URL` passed |
| 2 | Enter Manager ID `499` in the username field | ✅ | `Username (Manager ID) entered=499` @11:46:20 |
| 3 | Enter `Mngr@101Pass!` in the password field | ✅ | `Password entered (masked)=*************` @11:46:22 |
| 4 | Click the Login button | ✅ | `Clicked button=Login` @11:46:24 → `Post-login URL=http://localhost:5173/dashboard/499`; assertion `Dashboard is displayed after login` (expected=yes / actual=yes) PASS |
| 5 | Click `View All Employees` on the dashboard, land on `/all-employees/499` | ✅ | `Dashboard button clicked=View All Employees` @11:46:27; `URL after navigation=http://localhost:5173/all-employees/499`; assertion `URL ends with expected path` PASS |
| 6 | Select `All Employees` in the filter dropdown | ✅ | `Filter selected=All Employees (100)` @11:46:31; assertion `Filter dropdown selection starts with requested label` (expected=all employees / actual=all employees) PASS |
| 7 | Leave the search box empty | ✅ | `Search box value=(empty)` @11:46:33; assertion `Search box is empty` (expected='' / actual='') PASS |
| 8 | Read names in the table and tick each off against the CSV | ⚠️ | Step def `when_walk_all_pages` exists (story_1_verify_all_employees_against_csv_steps.py:201) but NO `P{n} row {i}` cap.add entries are present — 0 of 100 rows evidenced |
| 9 | Click the `>` next-page button until the last page | ⚠️ | Step def at lines 214-219 calls `pom.click_next_page()` in a loop; expected `Pagination total pages` / `Pages walked` entries are ABSENT |
| 10 | Use the `<` previous-page button to go back | ⚠️ | Step def at lines 223-233 demonstrates the back-button; expected `Backtracked one page via < button` entry is ABSENT |
| 11 | If every CSV name appears on the UI, the data matches | ⚠️ | Step def `then_every_csv_name_appears` (lines 238-262) would call `cap.assert_match("Every CSV name appears on the UI", expected="100", actual=<seen>)` — this entry is ABSENT from captured_values.json |
| 12 | If a CSV name is not found, report it as a missing employee | ⚠️ | Step def `then_report_missing` (lines 265-278) would emit `Missing-employee report (count)` and per-item kind=missing rows; NONE present |

Legend: ✅ exercised & evidenced · ❌ failed or no step def · ⚠️ step def exists but capture log silent

---

## Captured values

| Label | Value / Expected | Actual | Verdict | Time |
|---|---|---|---|---|
| Opened URL | — | http://localhost:5173/ | — | 11:46:18 |
| App reachable at base URL (prerequisite) | true | true | ✅ | 11:46:18 |
| Username (Manager ID) entered | — | 499 | — | 11:46:20 |
| Password entered (masked) | — | ************* | — | 11:46:22 |
| Clicked button | — | Login | — | 11:46:24 |
| Post-login URL | — | http://localhost:5173/dashboard/499 | — | 11:46:25 |
| Dashboard 'View All Employees' visible | — | yes | — | 11:46:25 |
| Dashboard is displayed after login (assert) | yes | yes | ✅ | 11:46:25 |
| Dashboard button clicked | — | View All Employees | — | 11:46:27 |
| URL after navigation | — | http://localhost:5173/all-employees/499 | — | 11:46:29 |
| URL ends with expected path (assert) | /all-employees/499 | /all-employees/499 | ✅ | 11:46:29 |
| Filter selected | — | All Employees (100) | — | 11:46:31 |
| Filter dropdown selection starts with label (assert) | all employees | all employees | ✅ | 11:46:31 |
| Search box value | — | (empty) | — | 11:46:33 |
| Search box is empty (assert) | "" | "" | ✅ | 11:46:33 |
| Employees table visible | — | yes | — | 11:46:34 |
| Visible row count on first page | — | 10 | — | 11:46:34 |
| CSV total rows (from user_data.json) | — | 100 | — | 11:46:34 |
| Employees table is displayed (assert) | yes | yes | ✅ | 11:46:34 |
| **— capture log ends here; ~12s of test execution produced no further entries —** | | | | |

---

## Aggregate & math verifications

_No aggregate, diff, percentage, ratio, or range assertions were captured._

The story requires an implicit aggregate check ("every CSV name appears on the UI",
i.e. unique-Emp-IDs-seen-on-screen **equals** csv_total=100). The step def
`then_every_csv_name_appears` would have produced exactly this aggregate via
`cap.assert_match`, but the entry is absent — see top-of-report banner.

---

## Negative scenarios

The story declares **no negative branches** (no invalid-credentials retry, no
"validation message" expectation). `user_data.json` is a flat array of 100
positive employee rows with no `expected_message` / `should_succeed:false`
fields. Nothing to verify in this section.

---

## Gaps in coverage

- Step 8 (per-row CSV reconciliation): **0 of 100** `P{page} row {idx}` cap.add entries — no evidence the rows were actually read off the UI.
- Step 9 (pagination forward walk): no `Pagination total pages` or `Pages walked` entries — no evidence pages 2..10 were visited.
- Step 10 (pagination backward step): no `Backtracked one page via < button` entry — no evidence the `<` control was exercised.
- Step 11 (aggregate CSV-match assertion): no `Every CSV name appears on the UI` entry — the central assertion of the story is unevidenced.
- Step 12 (missing-employee report): no `Missing from UI` or `Missing-employee report` entries — cannot confirm zero misses.
- `reports/screenshots/` directory does not exist — no visual fallback evidence.

---

## Recommendation

Investigate why the walk-and-reconcile portion of the test (between 11:46:34 and
11:46:46) produced no captured_values entries despite the matching step defs
having explicit `cap.add(...)` and `cap.assert_match(...)` calls. Until the
capture log includes per-row reconciliation evidence and the "Every CSV name
appears on the UI" aggregate assertion, **this story should not be considered
fully verified**, even though pytest-html marks it PASSED.
