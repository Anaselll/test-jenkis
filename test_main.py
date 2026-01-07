import sys
import os
import tempfile
import pytest

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import app as app_module
from app import app, BusinessDashboard


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config["TESTING"] = True

    # Override the global dashboard used by routes
    app_module.dashboard = BusinessDashboard(db_name=db_path)

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_dashboard_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    # Update if your dashboard.html title differs
    assert b"Business Management Dashboard" in response.data


def test_add_employee(client):
    response = client.post(
        "/api/employees",
        json={"name": "Alice", "position": "Engineer", "salary": 90000}
    )
    assert response.status_code == 201

    response = client.get("/api/employees")
    data = response.get_json()
    assert data["count"] == 1
    assert data["employees"][0]["name"] == "Alice"


def test_add_sale(client):
    response = client.post(
        "/api/sales",
        json={"product": "Product X", "amount": 1200.50, "customer": "Client A"}
    )
    assert response.status_code == 201

    response = client.get("/api/sales")
    data = response.get_json()
    assert data["count"] == 1
    assert data["sales"][0]["product"] == "Product X"


def test_dashboard_summary_api(client):
    # Seed data
    client.post("/api/employees", json={"name": "Bob", "position": "Manager", "salary": 80000})
    client.post("/api/sales", json={"product": "Service A", "amount": 500, "customer": "Corp Ltd"})

    response = client.get("/api/dashboard")
    assert response.status_code == 200

    data = response.get_json()
    assert data["total_employees"] == 1
    assert data["total_sales"] == 1
    assert data["total_revenue"] == 500
    assert data["average_sale"] == 500
