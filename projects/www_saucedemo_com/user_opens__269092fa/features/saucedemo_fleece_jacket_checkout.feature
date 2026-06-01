Feature: SauceDemo end-to-end checkout for the fleece jacket
  As a SauceDemo customer
  I want to log in, add the Sauce Labs Fleece Jacket to my cart, and complete checkout
  So that I can place an order and see the order confirmation page

  Scenario: Complete checkout for the Sauce Labs Fleece Jacket
    Given the user opens "https://www.saucedemo.com/"
    And the user waits for 5 seconds
    When the user logs in with username "standard_user" and password "secret_sauce"
    And the user waits for 5 seconds
    And the user adds the product "Sauce Labs Fleece Jacket" to the cart
    And the user opens the cart page
    And the user waits for 5 seconds
    And the user presses the checkout button on the cart page
    Then the user is taken to the "Your Information" page
    And the user waits for 5 seconds
    When the user enters first name "abc"
    And the user enters last name "cde"
    And the user enters postal code "23212"
    And the user presses continue
    And the user waits for 5 seconds
    And the user notes the total price and clicks finish
    And the user waits for 5 seconds
    Then the user sees the "Thank you for your order!" page
