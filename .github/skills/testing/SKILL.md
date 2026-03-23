---
name: testing
description: Specialized testing workflows for ERP systems, focusing on business logic validation, unit tests, and integration tests for rental/sales operations.
---

# ERP Testing Skill

This skill provides comprehensive testing strategies for ERP systems, particularly for rental and sales businesses handling chemical toilet operations.

## When to Use
- Writing unit tests for business logic (financial calculations, inventory tracking)
- Creating integration tests for ERP workflows (sales to inventory, estimates to orders)
- Validating data integrity and consistency across modules
- Testing API endpoints and user interfaces

## Workflow

1. **Analyze Requirements**: Understand the business logic and edge cases for the feature being tested
2. **Write Test Cases**: Create focused tests for each business rule, including happy paths and error conditions
3. **Set Up Test Data**: Use fixtures or factories to create realistic test data for rental/sales scenarios
4. **Execute Tests**: Run tests using pytest or similar frameworks, ensuring coverage of critical paths
5. **Validate Results**: Check for data consistency, proper error handling, and business rule compliance

## Best Practices for ERP Testing
- **Financial Accuracy**: Test all monetary calculations with multiple decimal places and currency conversions
- **Inventory Integrity**: Validate stock levels, reservations, and transfers across operations
- **Business Rules**: Ensure estimates, quotes, and orders follow company policies
- **Data Validation**: Test input sanitization and edge cases (negative quantities, invalid dates)
- **Integration Points**: Verify data flow between sales, inventory, and financial modules

## Common Test Scenarios
- Order creation with inventory deduction
- Financial report generation with accurate totals
- Estimate approval workflow
- Inventory alerts for low stock
- Client credit limit validation

## Tools and Frameworks
- pytest for Python backend testing
- Jest/React Testing Library for frontend components
- Playwright or Cypress for end-to-end testing
- Factory Boy or pytest fixtures for test data

Always ensure tests reflect real business operations and help prevent costly errors in production.