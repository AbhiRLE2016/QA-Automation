Feature: Create a new Organization on RA Demo

  Scenario: Sign in and create the Relevance Lab organization
    Given the user navigates to "https://ra-demo.rlcatalyst.com/login"
    When the user clicks on the sign in link
    And the user enters email "sundeep.mallya+a@relevancelab.com" and password "Relevance@123" to login
    Then the user lands on the "My Organizations" page
    When the user clicks on "Add New"
    Then the "Create Organization" page is displayed
    When the user fills in the Organization details:
      | Field                    | Value                         |
      | Organization Name        | Relevance Lab                 |
      | Organization Description | Providing IT services globaly |
    And the user clicks on the "Create Organization" button
    Then the Organization with Name "Relevance Lab" is created
    And the Organization "Relevance Lab" is shown on the "My Organizations" page
