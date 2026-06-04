Feature: Delete user Jon Kumar from the Users page

  Scenario: Admin deletes user Jon Kumar from the Users page
    Given the user navigates to "https://ra-demo.rlcatalyst.com/login"
    And the user types the email "sundeep.mallya+a@relevancelab.com"
    And the user types the password "Relevance@123"
    And the user clicks on the "Sign In" link
    Then the Organization page is displayed
    And the user clicks on the Menu on the top left corner
    And the user clicks on "Users"
    Then the user lands on the Users page
    When the user clicks on the three dots on the row for user "Jon Kumar"
    And the user clicks on "Delete User"
    Then the "Are you sure you want to delete user" modal appears
    When the user clicks on the "Delete User" button in the modal
    Then the user "Jon Kumar" is deleted from the Users page
