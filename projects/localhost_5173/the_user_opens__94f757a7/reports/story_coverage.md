# Story coverage — FAIL
_Run: `2026-05-21_12-06-43` · Story: `localhost_5173/the_user_opens__94f757a7`_

**Verdict:** ❌ FAIL

- 1 assertion(s) failed
- pytest exited with code 1

pytest exit code: `1` · assertions: 15 · missing: 0 · prerequisites: 1

## Assertions
- ✓ **URL after action** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **Navigation welcome label** — expected `Welcome`, actual `WELCOME`
- ✓ **Navigation manager name** — expected `Nitin Kumar`, actual `Nitin Kumar`
- ✓ **Four dashboard tiles visible** — expected `all visible`, actual `all visible`
- ✓ **Selected tab on dashboard** — expected `Manage Employees`, actual `Manage Employees`
- ✓ **URL after action** — expected `http://localhost:5173/add-employee/499`, actual `http://localhost:5173/add-employee/499`
- ✓ **Form displayed: Add New Employee** — expected `visible`, actual `visible`
- ✓ **Browser alert text** — expected `Employee added successfully!`, actual `Employee added successfully!`
- ✓ **URL after action** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **Row with Emp ID 7777 / Priya Sharma present in Manage Employees table** — expected `row contains '7777' and 'Priya Sharma'`, actual `row contains '7777' and 'Priya Sharma'`
- ✓ **Manage Revenue panel displayed** — expected `visible`, actual `visible`
- ✓ **Manage Revenue panel buttons visible** — expected `all visible`, actual `all visible`
- ✓ **URL after action** — expected `http://localhost:5173/set-performance/499`, actual `http://localhost:5173/set-performance/499`
- ✓ **Form displayed: Set Performance** — expected `visible`, actual `visible`
- ✗ **Browser alert text** — expected `All KPIs added successfully!`, actual `Invalid data! Please check and try again.`

