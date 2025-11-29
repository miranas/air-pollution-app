import pytest
from simple_app import app
from flask.testing import FlaskClient

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):    
    response = client.get('/')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    expected = "Hello from Slovenia Air Quality!"
    assert expected in content 
    assert "Sloveniaw" not in content
            

def test_that_will_fail(client: "FlaskClient"):
    response = client.get('/')
    assert response.status_code == 404
    assert response.status_code ==404

      

def test_that_app_exists():
    assert app is not None

def test_that_app_is_in_testing_mode():
    assert app.config['TESTING'] == True
    assert app.config['TESTING'] == True


def test_what_methods_does_app_have():
    assert hasattr(app, 'test_client')
    assert hasattr(app, 'run')
    assert hasattr(app, 'route')

    methods = [method for method in dir(app) if not method.startswith('_')]
    print(f"\nFlask app has these methods: {methods}")
    print(f"Flask app has {len(methods)} methods")

        




