from database import SessionLocal
from repositories.models import Customer, Account, Complaint

with SessionLocal() as session:

    customer = session.get(Customer, "CUS001")

    if customer:
        print("Customer found!")
        print("ID:", customer.customer_id)
        print("Name:", customer.first_name, customer.last_name)
        print("Email:", customer.email)
    else:
        print("Customer not found")