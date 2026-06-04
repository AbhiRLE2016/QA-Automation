Feature: Add a new user via the Users page

  Scenario: Admin adds a new Researcher user to the organization
    Given the user navigates to "https://ra-demo.rlcatalyst.com/login"
    And the user types the email "sundeep.mallya+a@relevancelab.com" and the password "Relevance@123"
    And the user clicks on the "Sign In" link
    Then the Organization page is displayed
    And the user clicks on the Menu on the top left corner and clicks "Users"
    Then the user lands on the Users page
    And the user clicks on "Add New" and the list appears and selects "Add New User"
    Then the "Add User" modal is shown
    And the user provides the email "skumar@gmail.com" for the new user
    And the user selects the Role "Researcher" from the Role list
    And the user provides the First name "Jon"
    And the user provides the Last name "kumar"
    And the user selects the Organization unit "Relevance lab"
    And the user clicks on "Add User"
    Then the user is created and the Users page is shown
