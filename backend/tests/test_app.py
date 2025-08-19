import pytest
import json
import sys 
import os
# Add the parent directory to Python path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app  import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    response = client.get('/')
    assert response.status_code  == 200
    content = response.data.decode('utf-8')
    assert "Hello from Slovenia Air Quality"