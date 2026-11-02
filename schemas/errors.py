ERROR_CODES = {
    400: ("BAD_REQUEST", "Invalid request"),
    404: ("NOT_FOUND", "Resource not found"),
    409: ("CONFLICT", "Resource conflict"),
    422: ("VALIDATION_ERROR", "Request validation failed"),
    500: ("INTERNAL_ERROR", "An unexpected error occurred"),
    503: ("DATABASE_UNAVAILABLE", "Database temporarily unavailable"),
}