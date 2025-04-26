import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

def test_health_check(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_flight_search_validation(client):
    # Missing required field
    response = client.post("/api/flights/search", json={
        "destination": "JFK",
        "departure_date": "2023-12-15"
    })
    assert response.status_code == 422  # Validation error
    
    # Invalid trip type
    response = client.post("/api/flights/search", json={
        "origin": "SFO",
        "destination": "JFK",
        "departure_date": "2023-12-15",
        "trip_type": "invalid_type"
    })
    assert response.status_code == 422  # Validation error

def test_hotel_search_validation(client):
    # Check-out date before check-in date
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    response = client.post("/api/hotels/search", json={
        "destination": "Los Angeles",
        "check_in_date": str(tomorrow),
        "check_out_date": str(today)
    })
    assert response.status_code == 400
    assert "Check-out date must be after check-in date" in response.json()["detail"]

def test_nlu_process_endpoint(client):
    # Test flight search intent
    response = client.post("/api/nlu/process", json={
        "text": "I want to book a flight from New York to London"
    })
    assert response.status_code == 200
    assert response.json()["intent"] == "flight_search"
    
    # Test hotel search intent
    response = client.post("/api/nlu/process", json={
        "text": "I need a hotel in Paris"
    })
    assert response.status_code == 200
    assert response.json()["intent"] == "hotel_search"
    
    # Test validation
    response = client.post("/api/nlu/process", json={})
    assert response.status_code == 400