Feature: Invalid login validation on Scholastic Education CA storefront
  As a visitor of the Scholastic Education CA storefront
  I want to attempt signing in with invalid credentials
  So that I can confirm the system rejects bad credentials and displays the expected validation message

  Background:
    Given the user navigates to "https://storefront:storefront@education-qa.scholastic.ca"
    And the user accepts all cookies if the cookie banner is displayed

  Scenario: Attempting to sign in with invalid credentials shows a validation message
    When the user clicks the sign in link
    And the user enters email "invalid@myyahoo.com" and password "wrongpass"
    And the user submits the sign in form
    Then the user is not logged in
    And the "Invalid email or password" validation message is displayed
