# Kingban ERP Development Guidelines

## Business Context
This is an ERP system for a chemical toilet rental and sales business. Operations include:
- Purchasing from factories
- Storage and warehousing
- Assembly and packaging
- Sales and rental management

## Key Modules
- Sales management
- Estimate/quote generation
- Inventory tracking
- Financial reporting

## Technical Stack
- Backend: Python with FastAPI
- Frontend: Modern web framework (React/Vue)
- Database: PostgreSQL with SQLAlchemy
- Deployment: Docker with docker-compose

## Development Practices
- Follow REST API best practices
- Implement proper error handling and validation
- Use async operations where appropriate
- Maintain clean, readable code with proper documentation
- Write tests for business logic, especially for financial calculations and inventory management

## Code Quality
- Use type hints in Python
- Follow PEP 8 style guidelines
- Implement proper logging
- Validate all inputs and handle edge cases

Always consider the impact on business operations when making changes.