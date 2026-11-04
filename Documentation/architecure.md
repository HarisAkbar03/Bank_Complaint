## API Architecture

The application follows a layered architecture:

Client / Swagger UI
        |
        v
FastAPI Routers
        |
        v
Service Layer
        |
        v
Repository Layer
        |
        v
SQLAlchemy ORM
        |
        v
PostgreSQL Database

### Components

- Routers: Handle HTTP requests and responses.
- Services: Enforce business rules.
- Repositories: Perform database operations.
- Models: Define database entities and relationships.
- Schemas: Validate API inputs and outputs.
- Middleware: Track requests using correlation IDs.
- Exception Handlers: Return standardized error responses.