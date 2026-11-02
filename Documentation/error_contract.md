# API Error Contract

All API error responses must follow a consistent JSON structure.

## Response Fields

- **code:** Machine-readable error identifier.
- **message:** Human-readable description of the error.
- **correlation_id:** Unique request identifier used to match an API error with application logs.

## Example

```json
{
  "code": "NOT_FOUND",
  "message": "Resource not found",
  "correlation_id": "a7b9c12d-456e-478f-9a23-19b8a01c2d44"
}
```

## Error Mapping

| HTTP Status | Error Code | Message |
|---|---|---|
| 400 | BAD_REQUEST | Invalid request |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource conflict |
| 422 | VALIDATION_ERROR | Request validation failed |
| 500 | INTERNAL_ERROR | An unexpected error occurred |
| 503 | DATABASE_UNAVAILABLE | Database temporarily unavailable |

## Security Considerations

Error responses must not expose database credentials, stack traces, customer complaint narratives, or other sensitive information.

The correlation ID allows developers to investigate errors using structured application logs without exposing internal implementation details to API clients.