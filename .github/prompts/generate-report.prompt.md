---
description: Generate business reports from ERP data for chemical toilet rental/sales operations
argument-hint: "Report type (sales, inventory, financial, summary) and optional date range/filters"
---

Generate a comprehensive business report from the Kingban ERP system data.

## Input Parameters
- **Report Type**: sales | inventory | financial | summary | custom
- **Date Range**: Start date to end date (default: current month)
- **Filters**: Optional filters like client name, product type, salesperson, etc.

## Report Structure
1. **Executive Summary**: High-level overview of key metrics and performance
2. **Key Metrics**: Quantified results (revenue, units sold, inventory turnover, etc.)
3. **Detailed Breakdown**: Tables and charts of the data
4. **Trends Analysis**: Month-over-month or year-over-year comparisons
5. **Business Insights**: Interpretation of data for rental/sales operations
6. **Recommendations**: Actionable suggestions based on the data

## Business Context
- Focus on chemical toilet rental and sales metrics
- Include inventory levels, rental utilization rates
- Highlight financial performance (revenue, margins, outstanding payments)
- Consider seasonal patterns in rental demand

## Output Format
- Use clear headings and subheadings
- Include tables for data presentation
- Add calculations for percentages, totals, and averages
- Format professionally for management review

Query the database using appropriate SQL queries or API calls to gather accurate data. Ensure all financial figures are properly calculated and validated.