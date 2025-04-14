# Azure Rambi Coding Instructions

## Azure Guidelines
- @azure Rule - Use Azure Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `get_azure_best_practices` tool if available.
- Use Infrastructure as Code (IaC) with Bicep for all Azure deployments
- Prefer Azure Container Apps for microservices deployment
- Use Managed Identity for authentication when possible
- Configure proper RBAC permissions with least privilege

## Architecture Patterns
- Follow microservices architecture principles
- Implement the DAPR sidecars pattern for service-to-service communication
- Use API Management for API exposure and governance
- Implement proper error handling and retry logic

## Service-Specific Guidelines
- **Movie Generator Service**: Use Azure OpenAI with gpt-4o model
- **Movie Poster Service**: Use Azure OpenAI with dall-e-3 model
- **Movie Gallery Service**": Use DAPR components.
- **GUI Service**: Follow Flask best practices with proper templating

## Security Requirements
- Never hardcode credentials; use Key Vault references
- Implement proper error handling that doesn't leak sensitive information
- Follow secure networking practices
- Enable encryption for data at rest and in transit

## Performance Guidelines
- Implement caching where appropriate (especially for movie data)
- Use connection pooling for database operations
- Configure proper timeouts and circuit breakers
- Consider Redis cache for frequent operations

## Development Workflow
- Use Docker containers for local development
- Follow GitOps principles for deployments
- Implement proper CI/CD patterns
- Use `azd` commands for deployment when possible

## Code Quality Standards
- Follow language-specific conventions (Python PEP8, JavaScript ESLint)
- Use proper documentation and comments
- Implement comprehensive logging
- Write unit tests for critical functionality