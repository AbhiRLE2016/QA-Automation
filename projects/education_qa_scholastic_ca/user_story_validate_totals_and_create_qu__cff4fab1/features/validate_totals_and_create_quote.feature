Feature: Validate totals and create quote
  As a signed-in storefront user
  I want to add a product to my cart, validate the totals on the cart and checkout pages,
  create a quote, and then delete it
  So that I can verify the quote lifecycle and the order math end-to-end

  Background:
    Given user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    When the cookie banner is displayed the user clicks the "Accept All Cookies" button
    And the user clicks the sign in link
    And the user signs in with email "sel1@yopmail.com" and password "passw0rd"
    Then the user lands on the homepage

  Scenario Outline: Validate cart and checkout totals, then create and delete a quote
    When the user enters product id "<productid>" and clicks search
    Then the search result page is displayed
    When the user clicks the "Add to Cart" button
    Then a "Product added to cart" confirmation message is displayed on a green background
    When the user clicks the cart icon
    Then the "Your Cart" page is displayed
    And the Subtotal value displayed on the page equals "<Subtotal>"
    When the user clicks the "Checkout or Create Quote" button
    Then the Checkout page is displayed
    And the Subtotal value displayed on the Checkout page equals "<Subtotal>"
    And the Shipping & Handling value displayed on the Checkout page equals "<shipping>"
    And the HST value displayed on the Checkout page equals "<HST>"
    And the Total value displayed on the Checkout page equals "<Total>"
    When the user clicks the red "Payment or Create Quote" button
    Then the Checkout page is displayed
    When the user clicks the "Create Quote" link
    Then a new popup is displayed
    When the user clicks the "Close" button on the popup
    And the user clicks "Submit Quote"
    Then the Quote Confirmation page is displayed
    When the user clicks the "My Account" link
    And the user clicks the "My Quotes and Orders" link
    Then the "My Quotes and Orders" page is displayed
    When the user clicks the "delete" link
    Then the Delete quote popup is displayed
    When the user clicks "Yes" on the popup
    Then the text "You have no quotes" is displayed

    Examples:
      | productid     | Subtotal | shipping | HST  | Total |
      | 9781338670905 | 48.99    | 10.00    | 2.95 | 61.94 |
