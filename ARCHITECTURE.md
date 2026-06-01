# QE Agent — System Architecture

**Audience:** Engineering leadership / CEO
**Stack:** Python · Streamlit · Playwright · pytest-bdd · Claude Code CLI · MCP

---

## 1. What this system does

It turns a **plain-English user story** — written by a QE engineer, a PM, or a
business analyst — into a **runnable, browser-driven automated test** complete
with selectors, page objects, step definitions, and a coverage report. The
operator writes a paragraph; the system writes the test code, runs it against
the live application, and produces an evidence-based audit report.

```
                ┌──────────────────────────┐
                │  Plain-English story     │
                │  (paste / upload .txt)   │
                └────────────┬─────────────┘
                             │
            ┌────────────────▼─────────────────┐
            │  ① Gherkin (LLM)                  │   feature files
            │     Given/When/Then per sentence  │
            └────────────────┬─────────────────┘
                             │
            ┌────────────────▼─────────────────┐
            │  ② Test Framework (LLM + MCP)     │   POMs, step defs,
            │     • Reads app's _shared/        │   locators, tests
            │     • Reuses prior POMs           │
            │     • MCP discovers new selectors │
            └────────────────┬─────────────────┘
                             │
            ┌────────────────▼─────────────────┐
            │  ③ Run (pytest-bdd, headed)       │   pytest report,
            │     • Captures every value        │   captured_values.json
            │     • Records misses + halts      │
            │       on missing data             │
            └────────────────┬─────────────────┘
                             │
            ┌────────────────▼─────────────────┐
            │  Inline coverage report (Python)  │   story_coverage.html,
            │     <100 ms, no LLM call          │   per-run snapshot
            └──────────────────────────────────┘
```

**Key business outcomes:**
- A test suite that historically takes a QE engineer 1–2 days to author is
  produced in minutes from a paragraph.
- Tests reuse selectors and POMs **across every story on the same application**
  via a per-app knowledge base, so the *second* test for a given app is much
  faster (and cheaper) than the first.
- Every test run produces an **evidence-based truth report**, not a
  green/red checkmark — the operator sees every value the test observed and
  whether the live application matched expectations.

---

## 2. The three-step pipeline

The operator clicks three buttons in order. Each is gated by the previous and
each persists its outputs to disk so the run is interruptible and resumable.

### ① Generate Gherkin

- **Input:** `user_story.txt` (the paragraph the operator pasted).
- **Engine:** Claude Code CLI (LLM), tools allowed: file read/write only.
- **Output:** one `.feature` file per distinct story, written to `features/`.
- **Hard rules enforced by prompt:** every sentence in the story becomes at
  least one Gherkin step; no step is dropped or merged; negative paths
  ("invalid creds → error message") get their own scenario; data tables in
  the story become Examples rows.

### ② Generate Test Framework

- **Input:** the `.feature` file(s) from ①, plus the **per-app `_shared/`
  folder** (see §4).
- **Engine:** Claude Code CLI with Playwright MCP tools enabled (headless
  browser).
- **Pipeline:**
  1. Read existing POMs and step defs in `_shared/`.
  2. For each Gherkin step, decide: **reuse** an existing POM method, or
     **discover** a new one via Playwright MCP.
  3. Write any new POMs to `pages/`, step defs to `step_defs/`, and a
     pytest entrypoint to `tests/`.
  4. Run `pytest -v` headless once to validate. On failure, heal up to
     three times by re-discovering selectors.
- **Output:** runnable Python test code rooted in the workspace.

### ③ Run All Tests

- **Engine:** `pytest --headed` (real browser, visible to the operator).
- The test executes the story step-by-step. Every value it extracts (a
  manager's name, a row count, a confirmation message, a downloaded CSV's
  rows) is recorded in `reports/captured_values.json`.
- **Post-run (instant, Python only):** an inline coverage-report builder
  reads `captured_values.json` + the pytest exit code, computes the verdict
  (PASS / PARTIAL / FAIL / BLOCKED), and writes
  `reports/story_coverage.html` along with a timestamped snapshot to
  `projects/<app>/<story>/reports/runs/<YYYY-MM-DD_HH-MM-SS>/`.

---

## 3. Core components

| Layer | File / Module | Responsibility |
|---|---|---|
| **UI / Orchestrator** | `agent_ui.py` (Streamlit, ~4900 LOC) | Workflow buttons, sidebar, log streaming, file upload, run history, status pills. |
| **Prompts** | `BDD_PROMPT`, `FRAMEWORK_PROMPT`, `FRAMEWORK_DELTA_PROMPT`, `AUDITOR_PROMPT` in `agent_ui.py` | Hard-coded contracts for Claude — fidelity rules, no-fabrication rules, captured-values rules. |
| **Test Framework Runtime** | `conftest.py`, `pages/base_page.py` | pytest-bdd plumbing, Playwright session, `CaptureLog` (every assertion goes through this), `TabRegistry` (multi-tab support), download routing to `~/Downloads` via CDP. |
| **Per-app Knowledge Base** | `projects/<app>/_shared/` | Reusable POMs, step defs, locators, and a `flow_index.json` mapping flow verbs → POM methods. Grown automatically after every successful ② / ③. |
| **Inline Report Builder** | `build_inline_coverage_report()` in `agent_ui.py` | Reads `captured_values.json` + pytest exit code → produces HTML / Markdown / JSON in <100 ms. No LLM call. |
| **Subprocess Streamer** | `stream_command()` in `agent_ui.py` | Pipes Claude CLI's stream-JSON events into the UI log in real time. Heartbeat collapses, duplicate-line consolidation, stop-signal polling. |

---

## 4. Per-application knowledge base (RAG)

The system organises everything it has learned about a given web application
into a per-app folder. The folder is keyed by URL host:

```
projects/
├── localhost_5173/                       ← app folder
│   ├── _shared/                          ← reusable knowledge
│   │   ├── pages/                        (every POM)
│   │   ├── step_defs/                    (every reusable step def)
│   │   ├── mcp-selectors/locators.json   (every confirmed selector)
│   │   └── flow_index.json               (method-name → file index)
│   ├── delete_employee__52539d78/        ← per-story
│   │   ├── user_story.txt
│   │   ├── features/
│   │   └── reports/runs/<ts>/
│   └── ...
├── education_qa_scholastic_ca/
│   └── ...
└── www_saucedemo_com/
    └── ...
```

**How it makes the agent faster and cheaper over time:**

- First story on a new app → full MCP discovery (~5–15 min).
- Second story on the **same app** → `_shared/` is consulted first. If the
  story includes "log in as manager 499", the existing `page_login.py`'s
  `login_as_manager()` method is reused — no MCP, no token spend on
  re-discovery.
- Newly-discovered POMs are **promoted to `_shared/`** automatically after
  every successful ② and green ③. The flow index is rebuilt.

In a typical engagement, after the first 2-3 stories on an application,
subsequent stories reuse **80%+** of the existing artefacts and only the
new flow steps trigger MCP discovery.

---

## 5. Reliability guardrails

### Captured Values — every assertion goes through one API

`conftest.py` exposes a `captured_values` (`CaptureLog`) fixture that step
definitions MUST use to record every observation. This is the single source
of truth for the report.

| Helper | Use case |
|---|---|
| `cap.add(label, value)` | Record any observed value (a name, a price, a confirmation message). |
| `cap.assert_match(label, expected, actual)` | A direct equality check. |
| `cap.assert_sum/avg/min/max/count/...(group, actual)` | Arithmetic aggregation over recorded components. |
| `cap.assert_percentage(part, whole, expected_pct)` | "HST should be 13% of subtotal". |
| `cap.record_missing(label, target, reason)` | Per-item miss in a loop (continue to next item). |
| `cap.assert_prerequisite(label, condition, reason)` | Blocking precondition failed (halt scenario). |

Everything written by these helpers ends up in `captured_values.json`, which
drives the inline coverage report.

### No-fabrication rule

Generated tests **must** do exactly what the story names — no more, no less.
This rule is enforced both in the FRAMEWORK_PROMPT (banning autouse seeding
fixtures, banning direct HTTP API calls that POST/PUT/DELETE app state) and
in the runtime helpers themselves.

**Example:** if a story says *"find Priya Sharma and delete her"* and Priya
isn't in the live application, the test reports:

> **BLOCKED — Locate 'Priya Sharma' on Manage Employees table:**
> Employee 'Priya Sharma' is not present in the Manage Employees table for
> manager 499. The story expects this row to exist; since it does not, the
> delete cannot proceed.

**It does NOT** auto-create Priya so the delete has something to act on.
This means the report reflects the truth of the application's data — bugs
and missing data are surfaced, not masked.

### Missing-data / per-item handling

When a story has multiple independent targets (search A AND B, delete X AND
Y), each is handled independently:
- Found → executed, recorded, asserted.
- Not found → recorded via `cap.record_missing()`, loop continues with the
  next target.
- The report shows both outcomes side by side: *"✓ chocolate added to cart,
  ✗ ice cream NOT FOUND (search returned 0 results)"*.

### Row-coverage audit

When a user provides a sidecar CSV / XLSX / JSON file and the story says
"verify the entire data file", the agent generates a test that loops over
**every row × every column the story scopes** — no sampling, no first-25
truncation. The auditor flags PARTIAL if the captured assertions don't
match the file's row count.

---

## 6. The coverage report (deterministic, instant)

The previous version of this system used a Claude agent to write the
coverage report — 2-3 minutes per run, ~13 LLM tool calls each time. The
current version replaces that agent with a pure-Python builder that reads
`captured_values.json` and produces:

- `reports/story_coverage.html` — human-readable styled report (verdict
  banner, assertions table, missing items, prerequisites, observed values).
- `reports/story_coverage.md` — Markdown for chat / email summaries.
- `reports/story_coverage.json` — machine-readable for downstream tooling.

**Per-run history:** each ③ Run snapshots its outputs to
`projects/<app>/<story>/reports/runs/<YYYY-MM-DD_HH-MM-SS>/`, so the
operator can browse every prior run's verdict in the UI's *Run history*
section and compare regressions over time.

### Verdict hierarchy

| Verdict | Meaning |
|---|---|
| 🚫 BLOCKED | A `cap.assert_prerequisite` failed — the test couldn't begin meaningfully (login failed, missing data, page didn't load). |
| ❌ FAIL | At least one assertion failed, or pytest exited with a nonzero code. |
| ⚠ PARTIAL | Some items were not found (recorded via `cap.record_missing`); the rest passed. |
| ✓ PASS | All recorded assertions passed and pytest exited 0. |

---

## 7. Where the LLM is involved (and where it isn't)

| Phase | LLM (Claude) | Deterministic Python |
|---|---|---|
| ① Generate Gherkin | ✓ (yes) | — |
| ② Generate Test Framework | ✓ (yes, with MCP) | — |
| ③ Run pytest | — | ✓ (Playwright + pytest-bdd) |
| Coverage report | — | ✓ (instant, <100 ms) |
| Per-app retrieval | — | ✓ (filesystem + filename matching) |
| Run history & timestamping | — | ✓ |

This design **minimises LLM calls to the two creative phases** (writing
Gherkin, writing Python test code) and uses deterministic logic for
everything else. The result is a system whose runtime / reporting cost is
near-zero and whose token cost decreases as the per-app knowledge base
grows.

---

## 8. Data flow on a typical run

```
user pastes story
       │
       ▼
agent_ui.compute_story_id()
       │   → returns localhost_5173/delete_priya__52539d78
       ▼
auto-fork checks _shared/ for localhost_5173
       │   → pages:7 step_defs:5 selectors:4 → copy into workspace
       ▼
① Generate Gherkin (Claude)
       │   → writes features/story_1_delete_priya.feature
       ▼
② Generate Test Framework (Claude, DELTA mode)
       │   → reuses login / navigate / search POMs from _shared/
       │   → MCP-discovers only NEW selectors (e.g. confirm-delete modal)
       │   → writes pages/page_delete_employee.py, step_defs/.../delete_steps.py,
       │     tests/test_delete_priya.py
       │   → headless smoke run; heals if needed
       ▼
③ Run All Tests (pytest, headed)
       │   → step defs use Playwright POMs against real localhost:5173
       │   → captured_values.json appended on every assertion
       ▼
write_inline_coverage_report() (Python, <100 ms)
       │   → reports/story_coverage.{html, md, json}
       │   → projects/localhost_5173/.../reports/runs/2026-05-21_11-05-30/...
       ▼
promote_to_shared(story_id)
       │   → new POMs / step_defs / selectors copied to _shared/
       │   → flow_index.json refreshed
       ▼
operator sees verdict banner + per-row evidence in the UI
```

---

## 9. Operational characteristics

- **Headed runs are demo-friendly:** Playwright `slow_mo` and a configurable
  pytest-bdd post-step delay keep tests slow enough for an audience to
  follow each action visually.
- **Stop button mid-run:** a sentinel file polled every ~10 seconds lets
  the operator kill a stuck Claude / pytest subprocess from a second
  browser tab even when the main Streamlit page is blocked.
- **Refresh = fresh session:** any reload clears in-memory state and
  reseeds the workspace from disk; all durable artefacts live in
  `projects/<app>/<story>/`.
- **Downloads route to `~/Downloads` natively** via Chromium CDP
  (`Browser.setDownloadBehavior`), so test-triggered file downloads land
  in the operator's real Downloads folder with the server's suggested
  filename — no UUID temp files.

---

## 10. Roadmap signals

- **Story → step traceability mapping** (currently the Python report shows
  every captured value but doesn't draw lines from each story sentence to
  the test step that covered it). Three implementation options exist; any
  can be added without breaking the current pipeline.
- **Multi-app concurrent runs.** Streamlit currently runs one pipeline at
  a time per browser session; the project layout already supports parallel
  runs against different apps.
- **CI hook.** The per-app `_shared/` folder + the deterministic report
  builder are CI-compatible today; we have not yet wired a GitHub Action
  / Jenkins entrypoint.

---

## 11. The pitch in one paragraph

> A QE engineer types a paragraph. Within minutes the system has read every
> POM and locator the team has ever built for that application, reused
> what fits, browsed the live site only for the genuinely new parts,
> written runnable test code, run it against the real browser, and emitted
> a human-readable verdict report citing every value the test observed.
> Every subsequent test on that application costs less and runs faster
> because the system retains its learnings as a per-app knowledge base.
> When the application's data isn't what the story expects, the system
> reports the truth rather than fabricating success.
