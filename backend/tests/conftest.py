import pytest
import os
import tempfile
from app import create_app

app = create_app()

#shared fixtures for tests can go here
#conftest.py makes this available everywhere:
@pytest.fixture(scope="function")
def client():
    """Shared Flask test client fixture for :
    -test_app.py
    -test_arso_service.py
    -test_mock_data_generator.py
    -test ANY test file in tests/Directory"""

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as test_client:
        with app.app_context():
            yield test_client


