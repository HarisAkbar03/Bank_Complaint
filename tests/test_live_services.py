
from agents.live_services import (
    get_customer_service,
    get_accounts_service,
    get_complaint_service,
)

customer_id = input("Enter customer ID: ").strip()
complaint_id = input("Enter complaint ID: ").strip()

print("\nCUSTOMER:")
print(get_customer_service(customer_id))

print("\nACCOUNTS:")
print(get_accounts_service(customer_id))

print("\nCOMPLAINT:")
print(get_complaint_service(complaint_id))
