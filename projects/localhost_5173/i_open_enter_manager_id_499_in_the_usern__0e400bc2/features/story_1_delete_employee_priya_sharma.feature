Feature: Delete employee Priya Sharma and verify removal end to end

  Scenario: Manager 499 deletes Priya Sharma and confirms the record is gone
    Given the user opens "http://localhost:5173/"
    When the user enters Manager ID "499" in the username field
    And the user enters "Mngr@101Pass!" in the password field
    And the user clicks the Login button
    Then the dashboard at "/dashboard/499" is displayed
    When the user makes sure the "Manage Employees" tab is selected
    And the user finds the row for "Priya Sharma" in the employees table
    And the user selects that row
    And the user clicks the "Delete Employee" button
    And the user confirms the deletion when prompted
    When the user clicks the "View All Employees" button
    Then the page navigates to "/all-employees/499"
    When the user sets the filter dropdown to "All Employees"
    And the user types "Priya Sharma" into the search box
    Then the table shows the "No employees match 'Priya Sharma'." message
    And the employee "Priya Sharma" is not found in the record
    And the delete went through end to end
