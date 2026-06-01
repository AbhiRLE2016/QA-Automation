Feature: Manager onboards an employee, sets KPIs, uploads revenue, and verifies the PLI breakdown

  Scenario: Manager 499 onboards Priya Sharma, sets KPIs, adds revenue and verifies the PLI breakdown
    Given the user opens "http://localhost:5173/"
    When the user types "499" into the "Manager ID" input
    And the user types "Mngr@101Pass!" into the "Password" input
    And the user clicks the "Login" button
    Then the URL changes to "http://localhost:5173/dashboard/499"
    And the navigation bar displays "Welcome" with the manager name "Nitin Kumar"
    And the following four tiles are visible on the dashboard:
      | Tile                |
      | Total Employees     |
      | Total Revenue       |
      | Growth %            |
      | Active Departments  |
    And the "Manage Employees" tab is selected by default

    When the user clicks the green "Add Employee" button on the Manage Employees tab
    Then the URL changes to "http://localhost:5173/add-employee/499"
    And the "Add New Employee" form is displayed

    When the user fills the "Add New Employee" form with the following details:
      | Field           | Value                    |
      | Employee Name   | Priya Sharma             |
      | Employee ID     | 7777                     |
      | Grade           | L2                       |
      | Employment Type | Full-Time                |
      | CTC             | 1500000                  |
      | Fixed Pay       | 1125000                  |
      | Variable Pay    | 375000                   |
      | Employee Status | Active                   |
      | Email           | priya.sharma@example.com |
      | Department      | Engineering              |
      | Project         | HRMS Revamp              |
    And the user clicks the blue "Add Employee" button at the bottom of the form
    Then a browser alert is displayed with the text "Employee added successfully!"

    When the user clicks "OK" on the alert
    Then the URL changes back to "http://localhost:5173/dashboard/499"
    And a row with Emp ID "7777" and Name "Priya Sharma" appears in the Manage Employees table

    When the user clicks the "Manage Revenue" tab at the top of the dashboard
    Then the Manage Revenue panel is displayed
    And the following buttons are visible on the panel:
      | Button             |
      | Add Revenue        |
      | Upload Review      |
      | Set Performance    |
      | Show PLI           |
      | Modify Performance |

    When the user clicks the red "Set Performance" button
    Then the URL changes to "http://localhost:5173/set-performance/499"
    And the "Set Performance" form is displayed

    When the user selects "Q4_2025" from the "Quarter" dropdown
    And the user selects "7777" from the "Emp_ID" dropdown
    And the user fills KPI row #1 with the following details:
      | Field           | Value                |
      | KPI #1 Name     | Delivery Excellence  |
      | KPI #1 Threshold| 5                    |
      | KPI #1 Target   | 10                   |
      | KPI #1 Achieved | 8                    |
      | KPI #1 Weightage| 60                   |
    And the user clicks the dark "Add More KPI" button
    And the user fills KPI row #2 with the following details:
      | Field           | Value             |
      | KPI #2 Name     | Delivery Quality  |
      | KPI #2 Threshold| 4                 |
      | KPI #2 Target   | 10                |
      | KPI #2 Achieved | 10                |
      | KPI #2 Weightage| 40                |
    And the user clicks the blue "Save All KPIs" button
    Then a browser alert is displayed with the text "All KPIs added successfully!"

    When the user clicks "OK" on the alert
    Then the URL changes back to "http://localhost:5173/dashboard/499"

    When the user clicks the "Manage Revenue" tab
    And the user clicks the blue "Add Revenue" button
    Then the URL changes to "http://localhost:5173/add-revenue/499"
    And the "Add Revenue" form is displayed

    When the user selects "7777 — Priya Sharma" from the "Employee" dropdown
    Then the "Employee Name" field is auto-filled with "Priya Sharma" and is read-only

    When the user fills the "Add Revenue" form with the following details:
      | Field            | Value   |
      | Revenue ID       | 7777    |
      | Month            | 2025-10 |
      | Cost             | 200000  |
      | Cost_Currency    | INR     |
      | Revenue          | 500000  |
      | Revenue Currency | INR     |
    And the user clicks the blue "Add Revenue" button at the bottom of the form
    Then a browser alert is displayed with the text "Revenue added successfully!"

    When the user clicks "OK" on the alert
    Then the URL changes back to "http://localhost:5173/dashboard/499"

    When the user clicks the "Manage Revenue" tab
    And the user clicks the blue "Show PLI" button
    Then the URL changes to "http://localhost:5173/show-pli/499"
    And the "PLI Data" table is displayed
    And the PLI Data table contains a row with the following values:
      | Field                 | Value   |
      | Emp ID                | 7777    |
      | Eligible Amount (USD) | 318,750 |
      | Payable Amount (USD)  | 280,500 |

    When the user clicks the "7777" link in the Emp ID column
    Then the URL changes to "http://localhost:5173/show-employee-pli/499/7777"
    And the page header shows the following values:
      | Field      | Value         |
      | Emp ID     | 7777          |
      | Name       | Priya Sharma  |
      | Manager ID | 499           |
      | Manager    | Nitin Kumar   |
    And the KPI breakdown table contains exactly two rows
    And KPI breakdown row 1 has the following values:
      | Field     | Value               |
      | KPI       | Delivery Excellence |
      | Quarter   | Q4_2025             |
      | Threshold | 5                   |
      | Target    | 10                  |
      | Achieved  | 8                   |
      | Weightage | 60%                 |
      | Eligible  | 191,250             |
      | Payable   | 153,000             |
    And KPI breakdown row 2 has the following values:
      | Field     | Value             |
      | KPI       | Delivery Quality  |
      | Quarter   | Q4_2025           |
      | Threshold | 4                 |
      | Target    | 10                |
      | Achieved  | 10                |
      | Weightage | 40%               |
      | Eligible  | 127,500           |
      | Payable   | 127,500           |
    And the Total row at the bottom of the KPI breakdown table shows:
      | Field    | Value   |
      | Eligible | 318,750 |
      | Payable  | 280,500 |
    And the Total Eligible value "318,750" equals the sum of the two row Eligible values "191,250" and "127,500"
    And the Total Payable value "280,500" equals the sum of the two row Payable values "153,000" and "127,500"
