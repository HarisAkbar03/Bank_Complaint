
from unittest.mock import MagicMock, patch

import pytest

from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.complaint_repository import ComplaintRepository

from repositories.models import Customer, Account, Complaint


# ---------------------------------------
# Customer Repository Tests
# ---------------------------------------

@pytest.mark.parametrize("record_id", ["C1", "C2"])
def test_customer_found(record_id):

    session = MagicMock()
    expected = MagicMock(spec=Customer)

    session.get.return_value = expected

    with patch(
        "repositories.customer_repository.SessionLocal"
    ) as mock_session_factory:

        mock_session_factory.return_value.__enter__.return_value = session

        repository = CustomerRepository()
        result = repository.get_by_id(record_id)

    assert result is expected
    session.get.assert_called_once_with(Customer, record_id)


def test_customer_missing():

    session = MagicMock()
    session.get.return_value = None

    with patch(
        "repositories.customer_repository.SessionLocal"
    ) as mock_session_factory:

        mock_session_factory.return_value.__enter__.return_value = session

        repository = CustomerRepository()
        result = repository.get_by_id("missing")

    assert result is None


def test_customer_database_failure():

    session = MagicMock()
    session.get.side_effect = RuntimeError("Simulated database failure")

    with patch(
        "repositories.customer_repository.SessionLocal"
    ) as mock_session_factory:

        mock_session_factory.return_value.__enter__.return_value = session

        repository = CustomerRepository()

        with pytest.raises(
            RuntimeError,
            match="Simulated database failure"
        ):
            repository.get_by_id("C1")

    mock_session_factory.return_value.__exit__.assert_called_once()


# ---------------------------------------
# Account Repository Tests
# ---------------------------------------

@pytest.fixture
def account_session():

    session = MagicMock()

    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = session

    return session, session_factory


def test_account_found(account_session):

    session, session_factory = account_session

    expected = MagicMock(spec=Account)
    session.get.return_value = expected

    repository = AccountRepository(session_factory=session_factory)

    result = repository.get_by_id("A1")

    assert result is expected
    session.get.assert_called_once_with(Account, "A1")


def test_account_missing(account_session):

    session, session_factory = account_session
    session.get.return_value = None

    repository = AccountRepository(session_factory=session_factory)

    assert repository.get_by_id("missing") is None


def test_account_database_failure(account_session):

    session, session_factory = account_session

    session.get.side_effect = RuntimeError(
        "Simulated database failure"
    )

    repository = AccountRepository(session_factory=session_factory)

    with pytest.raises(
        RuntimeError,
        match="Simulated database failure"
    ):
        repository.get_by_id("A1")

    session_factory.return_value.__exit__.assert_called_once()


def test_account_empty_customer_list(account_session):

    session, session_factory = account_session

    session.scalars.return_value.all.return_value = []

    repository = AccountRepository(session_factory=session_factory)

    result = repository.list_by_customer("C1")

    assert result == []
    session.scalars.assert_called_once()


# ---------------------------------------
# Complaint Repository Tests
# ---------------------------------------

@pytest.fixture
def complaint_session():
    return MagicMock()


def test_complaint_found(complaint_session):

    expected = MagicMock(spec=Complaint)
    complaint_session.get.return_value = expected

    repository = ComplaintRepository(complaint_session)

    result = repository.get_by_id("P1")

    assert result is expected
    complaint_session.get.assert_called_once_with(Complaint, "P1")


def test_complaint_missing(complaint_session):

    complaint_session.get.return_value = None

    repository = ComplaintRepository(complaint_session)

    assert repository.get_by_id("missing") is None


def test_complaint_database_failure(complaint_session):

    complaint_session.get.side_effect = RuntimeError(
        "Simulated database failure"
    )

    repository = ComplaintRepository(complaint_session)

    with pytest.raises(
        RuntimeError,
        match="Simulated database failure"
    ):
        repository.get_by_id("P1")
