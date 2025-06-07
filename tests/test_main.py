import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns the expected response"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to PadelTour API"

def test_docs_endpoint():
    """Test that API documentation is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200

def test_openapi_endpoint():
    """Test that OpenAPI spec is accessible"""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200 