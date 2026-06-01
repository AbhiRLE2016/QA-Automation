Feature: Scholastic Education login and cart management
  As a user of the Scholastic Education Canada site
  I want to sign in and manage items in my cart
  So that I can build and clear my order as needed

  Background:
    Given user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    And the cookie banner is dismissed by clicking "Accept All Cookies" if displayed

  Scenario: Invalid login attempt shows an error message
    When user clicks on the "Sign In" link
    And user enters email "invalid@myyahoo.com"
    And user enters password "wrongpass"
    And user submits the sign in form
    Then user should not be logged in
    And the message "Sorry, we cannot find an account with this email address and password. Please try again or click \"Forgot your login information\"?" should be displayed

  Scenario: Valid user can search, add an item, update quantity, and clear the cart
    When user clicks on the "Sign In" link
    And user clears the email and password fields
    And user enters email "qauto@myyahoo.com"
    And user enters password "passw0rd"
    And user submits the sign in form
    Then user lands on the homepage
    When user clicks on the search icon to get all the items
    And user adds the first item to the cart and notes its price
    Then the item should be added to the cart
    When user clicks on the cart icon
    Then user should navigate to the "Your Cart" page
    When user clicks the "+" button to increase the quantity of the item
    And user clicks the "Clear My Order" button
    Then the "Clear Your Cart" popup should be displayed
    When user clicks the "Yes" button on the popup
    Then the "Your Cart" page should be displayed with an empty cart
