from unittest.mock import MagicMock
import pytest
from database_manager import DatabaseManager
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.complaint_repository import ComplaintRepository
from repositories.models import Customer, Account, Complaint

@pytest.fixture
def fake_db(monkeypatch):
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "fake_password")
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    connector = MagicMock(return_value=connection)
    return DatabaseManager(connect=connector), connection, cursor

@pytest.mark.parametrize("repo_class,record,model", [
    (CustomerRepository, ("C1", "Ada", "Lovelace", "ada@example.test"), Customer),
    (AccountRepository, ("A1", "C1", "Checking", "Active", None), Account),
    (ComplaintRepository, ("P1", "C1", "Fees", "Open", None), Complaint),
])
def test_found(fake_db, repo_class, record, model):
    db, connection, cursor = fake_db
    cursor.fetchone.return_value = record
    result = repo_class(db).get_by_id(record[0])
    assert isinstance(result, model)
    assert result == model(*record)
    assert cursor.execute.call_args.args[1] == (record[0],)
    connection.commit.assert_called_once()
    connection.close.assert_called_once()

@pytest.mark.parametrize("repo_class", [CustomerRepository, AccountRepository, ComplaintRepository])
def test_missing(fake_db, repo_class):
    db, connection, cursor = fake_db
    cursor.fetchone.return_value = None
    assert repo_class(db).get_by_id("missing") is None
    connection.close.assert_called_once()

@pytest.mark.parametrize("repo_class", [CustomerRepository, AccountRepository, ComplaintRepository])
def test_query_failure_rolls_back_and_closes(fake_db, repo_class):
    db, connection, cursor = fake_db
    cursor.execute.side_effect = RuntimeError("query failed")
    with pytest.raises(RuntimeError):
        repo_class(db).get_by_id("C1")
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()

@pytest.mark.parametrize("repo_class", [AccountRepository, ComplaintRepository])
def test_empty_customer_list(fake_db, repo_class):
    db, connection, cursor = fake_db
    cursor.fetchall.return_value = []
    assert repo_class(db).list_by_customer("C1") == []
    assert cursor.execute.call_args.args[1] == ("C1",)
    connection.close.assert_called_once()

def test_connection_failure_does_not_attempt_close(monkeypatch):
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "fake_password")
    connector = MagicMock(side_effect=ConnectionError("offline"))
    with pytest.raises(ConnectionError):
        with DatabaseManager(connect=connector).session():
            pass
