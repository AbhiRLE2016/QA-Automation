# Story coverage — PASS
_Run: `2026-05-21_12-10-17` · Story: `localhost_5173/user_story_manager_onboards_an_employee__2a9683f9`_

**Verdict:** ✓ PASS

- All captured assertions passed

pytest exit code: `0` · assertions: 31 · missing: 0 · prerequisites: 0

## Assertions
- ✓ **URL changes to http://localhost:5173/dashboard/499** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **Navigation welcome + manager name** — expected `Welcome | Nitin Kumar`, actual `WELCOME | Nitin Kumar`
- ✓ **Default active tab is Manage Employees** — expected `Manage Employees`, actual `Manage Employees`
- ✓ **URL changes to http://localhost:5173/add-employee/499** — expected `http://localhost:5173/add-employee/499`, actual `http://localhost:5173/add-employee/499`
- ✓ **Add New Employee form is displayed** — expected `displayed`, actual `displayed`
- ✓ **Browser alert text** — expected `Employee added successfully!`, actual `Employee added successfully!`
- ✓ **URL changes back to http://localhost:5173/dashboard/499** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **Employee row appears for 7777 Priya Sharma** — expected `visible`, actual `visible`
- ✓ **Manage Revenue panel is displayed** — expected `displayed`, actual `displayed`
- ✓ **URL changes to http://localhost:5173/set-performance/499** — expected `http://localhost:5173/set-performance/499`, actual `http://localhost:5173/set-performance/499`
- ✓ **Set Performance form is displayed** — expected `displayed`, actual `displayed`
- ✓ **Browser alert text** — expected `All KPIs added successfully!`, actual `All KPIs added successfully!`
- ✓ **URL changes back to http://localhost:5173/dashboard/499** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **URL changes to http://localhost:5173/add-revenue/499** — expected `http://localhost:5173/add-revenue/499`, actual `http://localhost:5173/add-revenue/499`
- ✓ **Add Revenue form is displayed** — expected `displayed`, actual `displayed`
- ✓ **Employee Name auto-filled with Priya Sharma and read-only** — expected `Priya Sharma|True`, actual `Priya Sharma|True`
- ✓ **Browser alert text** — expected `Revenue added successfully!`, actual `Revenue added successfully!`
- ✓ **URL changes back to http://localhost:5173/dashboard/499** — expected `http://localhost:5173/dashboard/499`, actual `http://localhost:5173/dashboard/499`
- ✓ **URL changes to http://localhost:5173/show-pli/499** — expected `http://localhost:5173/show-pli/499`, actual `http://localhost:5173/show-pli/499`
- ✓ **PLI Data table is displayed** — expected `displayed`, actual `displayed`
- ✓ **PLI Data row for Emp ID 7777** — expected `{'Emp ID': '7777', 'Eligible Amount (USD)': '318,750', 'Payable Amount (USD)': '280,500'}`, actual `{'Emp ID': '7777', 'Eligible Amount (USD)': '318,750', 'Payable Amount (USD)': '280,500'}`
- ✓ **URL changes to http://localhost:5173/show-employee-pli/499/7777** — expected `http://localhost:5173/show-employee-pli/499/7777`, actual `http://localhost:5173/show-employee-pli/499/7777`
- ✓ **PLI Detail header fields** — expected `{'Emp ID': '7777', 'Name': 'Priya Sharma', 'Manager ID': '499', 'Manager': 'Nitin Kumar'}`, actual `{'Emp ID': '7777', 'Name': 'Priya Sharma', 'Manager ID': '499', 'Manager': 'Nitin Kumar'}`
- ✓ **KPI breakdown row count** — expected `2`, actual `2`
- ✓ **KPI breakdown row 1 matches** — expected `{'KPI': 'Delivery Excellence', 'Quarter': 'Q4_2025', 'Threshold': '5', 'Target': '10', 'Achieved': '8', 'Weightage': '60%', 'Eligible': '191,250', 'Payable': '153,000'}`, actual `{'KPI': 'Delivery Excellence', 'Quarter': 'Q4_2025', 'Threshold': '5', 'Target': '10', 'Achieved': '8', 'Weightage': '60%', 'Eligible': '191,250', 'Payable': '153,000'}`
- ✓ **KPI breakdown row 2 matches** — expected `{'KPI': 'Delivery Quality', 'Quarter': 'Q4_2025', 'Threshold': '4', 'Target': '10', 'Achieved': '10', 'Weightage': '40%', 'Eligible': '127,500', 'Payable': '127,500'}`, actual `{'KPI': 'Delivery Quality', 'Quarter': 'Q4_2025', 'Threshold': '4', 'Target': '10', 'Achieved': '10', 'Weightage': '40%', 'Eligible': '127,500', 'Payable': '127,500'}`
- ✓ **KPI breakdown Total row** — expected `{'Eligible': '318,750', 'Payable': '280,500'}`, actual `{'Eligible': '318,750', 'Payable': '280,500'}`

