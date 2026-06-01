# QE Automation Framework — Playwright + pytest-bdd (MCP-Driven, Self-Healing)

A test-automation framework that turns plain-English user stories into executable, self-healing Playwright tests. The framework is **MCP-first** — every selector is captured from a live, headed browser session before any code is generated, so nothing is hallucinated or guessed.

This document is the operating manual: what the framework is, how it's wired, and the exact step-by-step procedure to run it and to add new stories.

---

## 1. What this framework does

| In | → | Out |
|---|---|---|
| User stories in plain English (`user_story.txt`) | Pipeline | Gherkin features + Page Objects + step defs + pytest-bdd tests + selector registry + HTML/Allure reports + master dashboard |

**Core principle:** the live DOM is the only source of truth for selectors. If a test fails, the framework re-runs MCP discovery against the real site, captures fresh selectors, updates the registry, and re-runs — no guessing, no manual selector tweaking.

---

## 2. Prerequisites (one-time setup)

| Tool | Version used | Why |
|---|---|---|
| Python | 3.11+ | runs pytest + Playwright |
| Node.js | 20+ | runs `npx allure-commandline` |
| Java (JRE) | 21 | required by Allure to render the report |
| Playwright browsers | latest | the actual Chromium/Firefox/WebKit binaries |

Install Python packages and browsers:

```powershell
cd "C:\Users\RLE2016\Desktop\qe-automation-playwright-pytest-master - Copy\qe-automation-playwright-pytest-master"
pip install -r requirements.txt
python -m playwright install chromium
```

Java (portable, no admin needed) — already installed in this environment at `%USERPROFILE%\tools\jdk-21.0.10+7-jre`. To use it in any new shell:

```powershell
$env:JAVA_HOME = "$env:USERPROFILE\tools\jdk-21.0.10+7-jre"
$env:PATH      = "$env:JAVA_HOME\bin;$env:PATH"
```

---

## 3. Project layout

```
qe-automation-playwright-pytest-master/
├── prompt.txt                  # The operating contract for the autonomous workflow
├── user_story.txt              # Input: plain-English user stories
├── pytest.ini                  # pytest config (base_url, markers)
├── conftest.py                 # Shared fixtures (browser, page, base_url, --headed)
├── requirements.txt
├── generation_log.txt          # Audit trail of every discovery + generation pass
│
├── features/                   # Gherkin feature files (one per story)
│   ├── story_1_filters_and_add_to_cart.feature
│   └── story_2_cart_quantity_and_clear.feature
│
├── step_defs/                  # Step definitions (one file per story)
│   ├── story_1_steps.py
│   └── story_2_steps.py
│
├── pages/                      # Page Object Model
│   ├── base_page.py            # Shared helpers (selector fallbacks, click_any, fill_any)
│   ├── page_home.py
│   ├── page_search_results.py
│   └── page_cart.py
│
├── tests/                      # pytest-bdd scenario bindings
│   ├── test_story_1.py
│   └── test_story_2.py
│
├── mcp-selectors/
│   ├── locators.json           # Single source of truth for all selectors
│   └── discovery_meta.json     # When/where the last MCP run hit
│
└── reports/
    ├── report.html             # Self-contained pytest-html
    ├── allure-results/         # Raw Allure JSON
    ├── master_dashboard.html
    └── screenshots/            # Auto-captured on failure
```

---

## 4. The end-to-end procedure (what happens for every story)

### Step 1 — Capture the user story
Drop the plain-English story into `user_story.txt`. No format constraints; bullet steps are fine.

### Step 2 — Run MCP discovery (headed, on the real site)
Launch Playwright MCP in **headed** mode and walk through every action the story implies. During this pass:
- navigate the site
- inspect the live DOM
- extract real selectors
- record visited URLs and page titles
- capture screenshots

**Output:** all findings persisted to `mcp-selectors/locators.json` (organized per page key — e.g. `home`, `search_results`, `cart`) and a metadata note in `mcp-selectors/discovery_meta.json`.

> ⚠️ No code generation happens before this step finishes. Selectors come from the live DOM only.

### Step 3 — Generate the Gherkin feature
Convert the MCP action trace into one `.feature` file under `features/`. Each MCP action becomes exactly one Gherkin step.

### Step 4 — Generate Page Object classes
For every distinct page MCP visited, create or update `pages/page_<slug>.py`:
- inherits `BasePage`
- exposes one method per real action performed
- uses **only** selector keys from `locators.json`
- never calls Playwright from outside the POM

### Step 5 — Generate step definitions
Create `step_defs/story_<n>_steps.py`. Each `@given/@when/@then`:
- calls one POM method
- performs exactly one real action
- contains no guessed logic

Register the new module in `conftest.py` under `pytest_plugins`.

### Step 6 — Generate the test
Create `tests/test_story_<n>.py` and bind the scenario via `@scenario(...)`.

### Step 7 — Run
```powershell
pytest -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --headed
```

### Step 8 — Auto-heal on failure
If any step fails:
1. Re-launch MCP in headed mode
2. Reproduce the failing step on the live site
3. Inspect the live DOM
4. Extract updated selectors
5. Update `locators.json`
6. Update the affected POM method (and step def if needed)
7. Add waits/timing if the failure was timing-related
8. Re-run pytest

Repeat until green. **No alternate approaches, no guessing, no asking permission.**

### Step 9 — Story is "done" when
- feature file exists
- POMs for every visited page exist
- step defs exist
- test file exists
- `locators.json` is updated
- all steps pass
- screenshots saved for any failures
- `allure-results/` is updated

---

## 5. How to run

### Run everything
```powershell
cd "C:\Users\RLE2016\Desktop\qe-automation-playwright-pytest-master - Copy\qe-automation-playwright-pytest-master"
pytest -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --headed
```

### Run a single story
```powershell
pytest tests/test_story_1.py -v --headed
```

### Run a single test function (most precise)
```powershell
pytest tests/test_story_1.py::test_story_1_filters_and_add_first_item -v --headed
```

### Run by keyword
```powershell
pytest -k story_1 --headed
```

---

## 6. How to view reports

### Self-contained HTML (no Java needed)
Just open the file:
```
reports\report.html
```

### Allure (full timeline, attachments, history) — requires Java
```powershell
$env:JAVA_HOME = "$env:USERPROFILE\tools\jdk-21.0.10+7-jre"
$env:PATH      = "$env:JAVA_HOME\bin;$env:PATH"
npx allure-commandline serve reports/allure-results
```
Allure picks a free local port and opens your browser automatically.

### Master dashboard
```
reports\master_dashboard.html
```
Summarizes: test results, execution time, failures healed, selectors discovered, MCP traces, per-story status.

---

## 7. Adding a new user story (the recurring loop)

1. Append the new story to `user_story.txt`.
2. Run **MCP discovery** (headed) for the new flow.
3. Confirm new entries appear in `mcp-selectors/locators.json` (and any new page key).
4. Generate the four artifacts: `features/story_<n>_*.feature`, `pages/page_<slug>.py`, `step_defs/story_<n>_steps.py`, `tests/test_story_<n>.py`.
5. Register the new step-defs module in `conftest.py` → `pytest_plugins`.
6. Run the suite. Auto-heal any failures from live DOM until green.
7. Append a one-line entry to `generation_log.txt` recording what was discovered/generated.

---

## 8. Troubleshooting (issues already solved in this repo)

| Symptom | Cause | Fix |
|---|---|---|
| `pytest: error: unrecognized arguments: --headed` | `--headed` was read but never declared | `pytest_addoption(--headed)` added in `conftest.py` |
| `fixture 'base_url' not found` + `Unknown config option: base_url` | `pytest.ini` had `base_url=` but no plugin published it | Registered `base_url` ini option + added a session-scoped fixture in `conftest.py` |
| `npm error ENOENT … AppData\Roaming\npm` | npm's global prefix folder didn't exist | `mkdir "$env:APPDATA\npm"` once |
| `JAVA_HOME is not set …` when running Allure | Java not installed | Portable JRE 21 extracted to `%USERPROFILE%\tools\jdk-21.0.10+7-jre`; export JAVA_HOME + PATH before running Allure |
| `allure serve` opened wrong path | Ran from `reports\`, not project root | Run from project root, or use the relative path that works from your cwd |

---

## 9. Why this approach (the "moto")

- **No flaky selectors.** Selectors come from a real, headed browser session — not from documentation, not from guesses.
- **Self-healing.** A failed test doesn't mean human debugging — it means a fresh MCP pass and a re-run. Drift in the application is absorbed by re-discovery, not by patching test code.
- **One artifact per role.** Features describe behavior, POMs describe pages, step defs are thin glue, `locators.json` is the only place selectors live. Nothing is duplicated, nothing is buried.
- **Replayable evidence.** Every run produces an HTML report + Allure timeline + screenshots on failure + a master dashboard. Anyone — manager, dev, QA lead — can audit what happened without re-running the suite.

---

## 10. Quick reference

| Need | Command |
|---|---|
| Install deps | `pip install -r requirements.txt && python -m playwright install chromium` |
| Run all tests headed | `pytest -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --headed` |
| Run only story 1 | `pytest tests/test_story_1.py --headed` |
| Open HTML report | open `reports\report.html` |
| Serve Allure (after `JAVA_HOME` is set) | `npx allure-commandline serve reports/allure-results` |
| Stop Allure server | `Ctrl+C` in its terminal |
