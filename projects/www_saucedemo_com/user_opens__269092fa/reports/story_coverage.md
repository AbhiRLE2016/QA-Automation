# Story Coverage Audit — VERDICT: ✅ PASS

**Test:** `tests/test_saucedemo_fleece_jacket_checkout.py::test_complete_checkout_for_the_sauce_labs_fleece_jacket`
**Result:** 1 passed, 0 failed, 0 skipped, 0 errors — duration **00:01:20**
**Report generated:** 2026-05-21 10:18 (pytest-html 4.1.1)

Every line of `user_story.txt` mapped to exactly one Gherkin step in `features/saucedemo_fleece_jacket_checkout.feature`, every Gherkin step has a corresponding `@given` / `@when` / `@then` handler in `step_defs/saucedemo_steps.py`, and pytest reports the single scenario PASSED. No negative scenarios were specified in the story.

---

## Requirements checklist

| # | Requirement | ✓/✗ | Evidence |
|---|---|---|---|
| 1 | User opens https://www.saucedemo.com/ | ✅ | `saucedemo_steps.py:9-12` `open_url()` → `page.goto(url)` |
| 2 | Wait for 5 seconds | ✅ | `saucedemo_steps.py:15-19` `wait_for_seconds()` |
| 3 | Username: `standard_user` | ✅ | `saucedemo_steps.py:24` fills `#user-name` |
| 4 | Password: `secret_sauce` | ✅ | `saucedemo_steps.py:25` fills `#password` |
| 5 | And logs in | ✅ | `saucedemo_steps.py:26-27` clicks `#login-button` + `expect(.inventory_list).to_be_visible()` |
| 6 | Wait for 5 seconds | ✅ | `wait_for_seconds()` |
| 7 | Adds the fleece jacket to cart | ✅ | `saucedemo_steps.py:30-35` add_product_to_cart('Sauce Labs Fleece Jacket'); asserts Remove button appears |
| 8 | Opens the cart page | ✅ | `saucedemo_steps.py:38-41` clicks `.shopping_cart_link` + URL regex `cart.html` |
| 9 | Wait for 5 seconds | ✅ | `wait_for_seconds()` |
| 10 | On cart page presses checkout button | ✅ | `saucedemo_steps.py:44-46` clicks `#checkout` |
| 11 | Taken to "Your Information" page | ✅ | `saucedemo_steps.py:49-56` URL `checkout-step-one.html` + title contains "Your Information" |
| 12 | Wait for 5 seconds | ✅ | `wait_for_seconds()` |
| 13 | Enter First name: `abc` | ✅ | `saucedemo_steps.py:59-61` fills `#first-name` |
| 14 | Enter Last name: `cde` | ✅ | `saucedemo_steps.py:64-66` fills `#last-name` |
| 15 | Enter zip/postal code: `23212` | ✅ | `saucedemo_steps.py:69-71` fills `#postal-code` |
| 16 | Presses continue | ✅ | `saucedemo_steps.py:74-77` clicks `#continue` + asserts title "Checkout: Overview" |
| 17 | Wait for 5 seconds | ✅ | `wait_for_seconds()` |
| 18 | Note the total price and click finish | ⚠ | `saucedemo_steps.py:80-85` reads `.summary_total_label` into `story_context['total_price']` then clicks `#finish` — value is *noted* (read) but never *asserted* and never logged to captured_values |
| 19 | Wait for 5 seconds | ✅ | `wait_for_seconds()` |
| 20 | See "Thank you for your order!" page | ✅ | `saucedemo_steps.py:88-93` `.complete-header` contains "Thank you for your order" + URL `checkout-complete.html` |

Result: **19 ✅ + 1 ⚠ (cosmetic)** — every action was performed and every page transition was asserted by Playwright `expect()`.

---

## Data assertions

_No `user_data.json` was provided and the story has no canonical expected total. Pytest-html shows no failed expectation messages._

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| _(none defined)_ | — | — | — |

---

## Captured values (per-step `captured_values.add(...)` trace)

⚠ **`reports/captured_values.json` does not exist.** Step defs do not call `captured_values.add(...)`. The total price the test read on the overview page is held only in the in-process `story_context['total_price']` dict and is not persisted for downstream audit.

| Label | Expected | Actual | Verdict | Timestamp |
|---|---|---|---|---|
| _(no entries)_ | — | — | — | — |

---

## Aggregate & math verifications

_No aggregate/sum/diff/percentage/ratio/range assertions present. Story does not require any._

---

## Negative scenarios

_The story has no negative cases — no invalid-credentials, no missing-field, no bad-postal-code branch. `features/saucedemo_fleece_jacket_checkout.feature` defines only the positive happy path._

| Bad input | Expected validation | Actual | Verdict |
|---|---|---|---|
| _(none required by story)_ | — | — | — |

---

## Gaps in coverage

- **No captured_values.json emitted.** `step_defs/saucedemo_steps.py` never invokes `captured_values.add(...)`. The framework supports it but this generation skipped it. → For future runs, log the order total at minimum so the auditor can show the actual number the user saw.
- **Total price is "noted" but not asserted.** Story line 38 says *"note the total price and click on finish"*. The step reads `.summary_total_label` into `story_context['total_price']` then immediately clicks finish; the value is never compared against anything, never logged to a report, and never returned to the auditor. Since the story doesn't define an expected total, no failure occurred — but the audit trail for *what number the user saw* is missing.
- **No screenshot artifacts.** `reports/screenshots/` is absent for this run. Acceptable for a passing run but means no visual evidence is available if anyone later disputes the result.
- **No row-coverage audit applicable** — single-scenario flow, no spreadsheet/CSV.

---

## Recommendation

✅ Ship as-is for the functional acceptance of this story. To strengthen future audits, have the *"note the total price"* step also call `captured_values.add(label="overview_total", actual=<value>)` so the order total ends up in `captured_values.json` for the audit report.
