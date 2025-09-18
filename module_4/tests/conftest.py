# Conftest

import pytest
from app import create_app

@pytest.fixture
def app():
    app_instance = create_app()  # Call the factory function
    yield app_instance

@pytest.fixture
def client(app):
    return app.test_client()