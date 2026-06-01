Feature: Valid login, search items, and add the first item to the cart
  As a registered shopper on the Scholastic Education CA storefront
  I want to sign in with valid credentials, view all search results, and add the first item to my cart
  So that I can confirm the login flow and the add-to-cart flow work end-to-end

  Background:
    Given the user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    And the user accepts all cookies if the cookie banner is displayed

  Scenario: Sign in with valid credentials and add the first searched item to the cart
    When the user clicks the sign in link
    And the user clears the email and password fields
    And the user enters email "qauto@myyahoo.com" and password "passw0rd"
    And the user submits the sign in form
    Then the user lands on the homepage
    When the user clicks the search icon to view all items
    And the user adds the first item to the cart and notes its dollar value
    Then the item is added to the cart page
