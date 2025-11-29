import pytest
from app import app
from flask.testing import FlaskClient
from unittest.mock import patch, Mock


"""Tests for the Flask application routes and app behavior."""


def test_home_route(client: FlaskClient):
    response = client.get('/')
    assert response.status_code== 200
    content = response.data.decode('utf-8')
    assert "Hello from Slovenia Air Quality" in content

def test_health_check_endpoint(client: FlaskClient):
    response = client.get('/api/health')
    assert response.status_code == 200

