Feature: Update cart quantity and clear the cart
  As a logged-in shopper on the Scholastic Education CA storefront
  I want to add an item to my cart, increase its quantity, and then clear the cart
  So that I can confirm the cart quantity controls and the Clear My Order flow work end-to-end

  Background:
    Given the user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    And the user accepts all cookies if the cookie banner is displayed
    When the user clicks the sign in link
    And the user logs in with email "qauto@myyahoo.com" and password "passw0rd"
    Then the user lands on the homepage

  Scenario: Add the first item, increase its quantity, then clear the cart
    When the user clicks the search icon to view all items
    And the user adds the first item to the cart and notes its dollar value
    Then the item is added to the cart page
    When the user clicks the cart icon
    Then the user is navigated to the "Your Cart" page
    When the user clicks the "+" button to increase the item quantity
    And the user clicks the "Clear My Order" button
    Then the "Clear your Cart" popup is displayed
    When the user clicks the "Yes" button on the Clear your Cart popup
    Then the "Your Cart" page is displayed with an empty cart
