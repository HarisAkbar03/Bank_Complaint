
# Import os to read environment variables like database username and password
import os

# Import csv to read data from CSV files
import csv

# Import argparse to accept command-line arguments like --reset
import argparse

# Import Path to work with file and folder locations
from pathlib import Path

# Import load_dotenv to load database credentials from the .env file
from dotenv import load_dotenv

# Import SQLAlchemy tools for connecting to and working with PostgreSQL
from sqlalchemy import create_engine, MetaData, Table, select, func, delete

# Import URL to create the database connection address
from sqlalchemy.engine import URL


# Load environment variables from the .env file
load_dotenv()

# Get the folder where this Python script is located
ROOT = Path(__file__).resolve().parent

# Set the location of the folder containing CSV files
DATA_DIR = ROOT / "Data"

# Set the location where the integrity report will be saved
REPORT_FILE = ROOT / "integrity_report.txt"


# Dictionary matching PostgreSQL table names to CSV filenames
# Tables are listed in the order they should be loaded
TABLES = {
    "customer": "customers.csv",   # Customer table uses customers.csv
    "account": "accounts.csv",     # Account table uses accounts.csv
    "complaint": "complaints.csv"  # Complaint table uses complaints.csv
}


# Define the required columns for each table
REQUIRED = {
    # Customers must have an ID, first name, and last name
    "customer": ["customer_id", "first_name", "last_name"],

    # Accounts must have an account ID and a customer ID
    "account": ["account_id", "customer_id"],

    # Complaints must have a complaint ID and a customer ID
    "complaint": ["complaint_id", "customer_id"]
}


# Main function responsible for loading CSV data into PostgreSQL
# reset=False means existing data will not be deleted by default
def main(reset=False):

    # Create an empty list to store information for the integrity report
    report = []

    # Create an empty list to store rejected rows and their reasons
    rejected = []

    # Create the PostgreSQL connection URL using environment variables
    url = URL.create(
        "postgresql+psycopg",                 # PostgreSQL database using psycopg driver
        username=os.getenv("DB_USER"),        # Get database username from .env
        password=os.getenv("DB_PASSWORD"),    # Get database password from .env
        host=os.getenv("DB_HOST", "localhost"), # Get host, default to localhost
        port=int(os.getenv("DB_PORT", "5432")), # Get port and convert it to integer
        database=os.getenv("DB_NAME")         # Get database name from .env
    )

    # Create the SQLAlchemy engine to manage database connections
    engine = create_engine(url)

    # Try to execute the database loading process
    try:

        # Open a connection and begin a database transaction
        # SQLAlchemy commits on success and rolls back on an exception
        with engine.begin() as conn:

            # Create a MetaData object to hold database table information
            metadata = MetaData()

            # Read the structure of existing tables from PostgreSQL
            metadata.reflect(
                bind=conn,         # Use the current database connection
                only=list(TABLES) # Only read customer, account, complaint
            )

            # Store the reflected SQLAlchemy table objects in a dictionary
            tables = {
                name: metadata.tables[name]  # Get table object using its name
                for name in TABLES           # Repeat for each table
            }

            # Check whether the user requested a database reset
            if reset:

                # Display a message that reset is starting
                print("Resetting seed tables...")

                # Loop through tables in reverse order
                # Complaint first, then Account, then Customer
                for name in reversed(TABLES):

                    # Delete existing records from the current table
                    conn.execute(delete(tables[name]))

            # Loop through each table name and its CSV filename
            for name, filename in TABLES.items():

                # Display which CSV file is currently being loaded
                print(f"Loading {filename}...")

                # Create the full path to the CSV file
                path = DATA_DIR / filename

                # Open the CSV file
                # newline="" handles CSV line endings correctly
                # utf-8-sig handles UTF-8 files with or without a BOM
                with open(path, newline="", encoding="utf-8-sig") as file:

                    # Read CSV rows as dictionaries using column headers
                    reader = csv.DictReader(file)

                    # Get the CSV column names, or empty list if missing
                    headers = reader.fieldnames or []

                    # Get the column names from the PostgreSQL table
                    columns = set(tables[name].columns.keys())

                    # Check whether the CSV headers are valid
                    if (
                        # Check if any CSV column names are duplicated
                        len(headers) != len(set(headers))

                        # Check if all required columns exist in the CSV
                        or not set(REQUIRED[name]).issubset(headers)

                        # Check if CSV columns exist in the database table
                        or not set(headers).issubset(columns)
                    ):

                        # Stop the process if CSV headers are invalid
                        raise ValueError(
                            f"Invalid CSV headers in {filename}"
                        )

                    # Count successfully inserted records
                    inserted = 0

                    # Count total records read from the CSV
                    total = 0

                    # Loop through each CSV row
                    # Start at line 2 because line 1 contains headers
                    for line, row in enumerate(reader, start=2):

                        # Increase total record count by one
                        total += 1

                        # Check if the CSV row contains more values than headers
                        if None in row:

                            # Record the filename, line number, and error
                            rejected.append(
                                f"{filename}, line {line}: Extra fields"
                            )

                            # Skip this invalid row and move to the next
                            continue

                        # Clean all values in the CSV row
                        row = {
                            # Remove extra spaces or use None for empty values
                            key: value.strip() if value else None

                            # Repeat for each column and value in the row
                            for key, value in row.items()
                        }

                        # Check whether any required column has a missing value
                        if any(
                            # True if the required value is missing or empty
                            not row.get(col)

                            # Check every required column for the current table
                            for col in REQUIRED[name]
                        ):

                            # Record the rejected row and reason
                            rejected.append(
                                f"{filename}, line {line}: Missing required value"
                            )

                            # Skip this row
                            continue

                        # Accounts and complaints must reference valid customers
                        if name in ("account", "complaint"):

                            # Search the customer table for the referenced ID
                            customer = conn.execute(

                                # Select the customer_id column
                                select(tables["customer"].c.customer_id)

                                # Only find the customer matching the CSV value
                                .where(
                                    tables["customer"].c.customer_id
                                    == row["customer_id"]
                                )

                            # Return the first matching customer, or None
                            ).first()

                            # Check if the customer does not exist
                            if customer is None:

                                # Record the invalid foreign key
                                rejected.append(
                                    f"{filename}, line {line}: Invalid customer_id"
                                )

                                # Skip this row
                                continue

                        # For complaints, check the account if one is provided
                        if name == "complaint" and row.get("account_id"):

                            # Find the customer who owns this account
                            account = conn.execute(

                                # Select customer_id from the account table
                                select(tables["account"].c.customer_id)

                                # Find the account matching the CSV account_id
                                .where(
                                    tables["account"].c.account_id
                                    == row["account_id"]
                                )

                            # Return the first matching account, or None
                            ).first()

                            # Check if account is missing or owned by another customer
                            if account is None or account[0] != row["customer_id"]:

                                # Record the invalid account/customer relationship
                                rejected.append(
                                    f"{filename}, line {line}: Invalid account/customer"
                                )

                                # Skip this complaint
                                continue

                        # Create and execute an INSERT query for this row
                        # **row passes the CSV dictionary as column values
                        conn.execute(tables[name].insert().values(**row))

                        # Increase the inserted count after successful insertion
                        inserted += 1

                    # Add the current table's loading statistics to the report
                    report.append(
                        f"{name}: Source={total}, Inserted={inserted}, "
                        f"Rejected={total - inserted}"
                    )

            # Add a heading for the database record counts
            report.append("\nDatabase counts:")

            # Loop through the SQLAlchemy table objects
            for name, table in tables.items():

                # Execute SELECT COUNT(*) for the current table
                count = conn.execute(

                    # Count all records in the table
                    select(func.count()).select_from(table)

                # Return the single count value
                ).scalar_one()

                # Add the table name and count to the report
                report.append(f"{name}: {count}")

        # This runs after the transaction commits successfully
        report.append("\nSTATUS: COMMITTED")

        # Display success message
        print("Database setup completed successfully!")

    # Catch any error that occurs during the try block
    except Exception as error:

        # Record that the transaction was rolled back
        report.append("\nSTATUS: ROLLED BACK")

        # Record the actual error message
        report.append(f"Error: {error}")

        # Display the error in the terminal
        print(f"Setup failed: {error}")

    # Finally runs whether the setup succeeds or fails
    finally:

        # Add the rejected rows section to the report
        report.append("\nRejected rows:")

        # Add rejected row messages, or "None" if there are no rejections
        report.extend(rejected or ["None"])

        # Save the report as a text file
        REPORT_FILE.write_text(

            # Join all report lines with newline characters
            "\n".join(report),

            # Save using UTF-8 encoding
            encoding="utf-8"
        )

        # Release pooled database connections
        engine.dispose()

        # Display where the report was saved
        print(f"Report saved: {REPORT_FILE}")


# Only run the following code when this file is executed directly
if __name__ == "__main__":

    # Create an argument parser for terminal options
    parser = argparse.ArgumentParser()

    # Add an optional --reset flag
    # If --reset is provided, its value becomes True
    parser.add_argument("--reset", action="store_true")

    # Read the arguments entered in the terminal
    args = parser.parse_args()

    # Check if the user requested a reset
    if args.reset:

        # Ask for explicit confirmation before deleting existing records
        confirmation = input("Type RESET to delete existing seed data: ")

        # Cancel the reset if the confirmation is incorrect
        if confirmation != "RESET":
            raise SystemExit("Reset cancelled.")

    # Call the main function with the selected reset option
    main(reset=args.reset)
