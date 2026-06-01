Feature: Browse search results, validate filters, and add the first item to the cart
  As a logged-in shopper on the Scholastic Education CA storefront
  I want to open the search results, see the Filter By options, and add the first item to my cart
  So that I can confirm the filtering UI and add-to-cart flow work end-to-end

  Background:
    Given the user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    And the user accepts all cookies if the cookie banner is displayed
    When the user clicks the sign in link
    And the user logs in with email "qauto@myyahoo.com" and password "passw0rd"
    Then the user lands on the homepage

  Scenario: Validate Filter By options, expand each filter, clear all, and add the first item to cart
    When the user clicks the search icon to view all items
    Then the "Filter By:" label is displayed
    And the following filter options are present
      | Curriculum   |
      | Grade        |
      | Language     |
      | GRL: F&P     |
      | GRL: DRA     |
      | Program      |
      | Subject      |
      | Price        |
      | Product Type |
      | Book Type    |
    When the user clicks each filter one by one
    Then each clicked filter expands
    When the user clicks the "Clear All" button
    Then all open filters are collapsed
    When the user adds the first item to the cart and notes its dollar value
    Then the item is added to the cart page
