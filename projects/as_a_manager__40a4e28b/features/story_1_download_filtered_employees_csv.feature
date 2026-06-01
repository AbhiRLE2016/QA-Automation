Feature: All Employees - Download filtered CSV

  As a manager
  I want to open the "All Employees" page, pick a finance department from the filter dropdown (or "All Employees") and click "Download CSV"
  So that I can quickly find a specific employee in my org and hand over a clean, filtered list to stakeholders without needing database access.

  Scenario: Manager filters the All Employees page by Finance department and downloads the CSV
    Given the user is a manager
    When the user opens the "All Employees" page
    And the user picks the "Finance" department from the filter dropdown
    And the user clicks "Download CSV"
    Then a CSV file of the filtered employee list is downloaded
    And the manager can quickly find a specific employee in the downloaded list
    And the downloaded list is clean and filtered for stakeholders without needing database access
