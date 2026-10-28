# Banking Complaint Management System — Model Design Notes

## Design Choices

I used Python dataclasses to represent the Customer, Account, Complaint, and StatusEvent models. Dataclasses reduce repetitive code and make the models easier to read and maintain.

I used `frozen=True` to prevent objects from being modified after creation.

I implemented enums for account and complaint statuses to ensure only predefined values are accepted.

I defined valid complaint status transitions to prevent invalid workflow changes, such as moving directly from Open to Closed.

I used `Decimal` for account balances to represent financial amounts accurately and `datetime` for complaint dates and status events.

## Testing

I used pytest to verify valid and invalid model states, status transitions, and dataclass immutability.

**Results:** 10 tests passed, 0 failed.

## Conclusion

The models provide a structured and validated representation of banking data while keeping business rules separate from database access logic.