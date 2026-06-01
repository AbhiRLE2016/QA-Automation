Feature: Manager walks the All Employees directory page by page and reconciles every row against the exported CSV

  As a manager
  I want to log in to the application and walk through the entire "All Employees" directory page by page
  So that I can confirm — name by name, not by count — that every employee listed in my exported CSV
  is actually present in the live directory, with nobody missing and no extras added

  Background:
    Given the application base URL is "http://localhost:5173/"
    And the manager has the exported CSV "employees_all_2026-05-18.csv" open beside the browser

  Scenario: Reconcile the full All Employees directory against the exported CSV, page by page
    Given the manager opens the application at "http://localhost:5173/"
    Then the manager is greeted by the login screen
    When the manager enters Manager ID "499" in the username field
    And the manager enters password "Mngr@101Pass!"
    And the manager clicks the "Login" button
    Then the manager lands on "http://localhost:5173/dashboard/499"
    When the manager clicks "View All Employees" from the dashboard
    Then the manager navigates to "http://localhost:5173/all-employees/499"
    When the manager sets the filter dropdown to "All Employees"
    Then the manager is working against the full directory rather than a single department
    When the manager clears the search box
    Then no rows are accidentally hidden from the table
    When the manager reads the first ten names in the table
    And the manager ticks each one off in the CSV "employees_all_2026-05-18.csv"
    And the manager uses the "Emp ID" column to disambiguate when two people share a name
    Then every employee shown on the current page is found in the CSV by name and Emp ID
    When the manager clicks the right-arrow ">" button in the pagination footer to advance to the next ten rows
    Then the "Page X of Y" indicator increments to reflect the new page
    And the manager repeats the same name-by-name check on the new page
    And every employee shown on the new page is found in the CSV by name and Emp ID
    When the manager keeps advancing with the right-arrow ">" button, page by page, watching the "Page X of Y" indicator to know how far along they are
    Then the manager reaches the last page, which may contain fewer than ten rows
    And every employee shown on each intermediate page is found in the CSV by name and Emp ID
    When the manager loses their place on the current page
    And the manager clicks the left-arrow "<" button in the pagination footer to step back to an earlier page
    Then the manager rechecks the names on that earlier page against the CSV
    Then at the end of the walk every CSV row has been ticked off
    And no employee shown on screen is absent from the CSV
