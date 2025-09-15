# conftest.py
import pytest

@pytest.fixture
def db_conn():
    return "fake_database_connection"