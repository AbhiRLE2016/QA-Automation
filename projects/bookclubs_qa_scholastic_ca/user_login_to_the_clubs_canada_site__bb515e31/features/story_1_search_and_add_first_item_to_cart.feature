Feature: Search for items and add the first item to the cart on Clubs Canada
  As a registered Clubs Canada shopper
  I want to log in, search for items, and add the first item to my cart
  So that I can verify the item is added with the correct price

  Background:
    Given the user is on the Clubs Canada login page at "https://storefront:storefront@bookclubs-qa.scholastic.ca/en/home"

  Scenario: Add the first searched item to the cart
    Given the user logs in with email "qauto@myyahoo.com" and password "passw0rd"
    And the user lands on the homepage
    When the user clicks on the search icon to view all items
    And the user adds the first item to the cart and notes its price
    Then the first item should be present in the cart with the noted price
