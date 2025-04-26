import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000/api"

# Example structured flight search
def search_flights_structured():
    # Calculate dates (2 months from now)
    today = datetime.now()
    departure_date = (today + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (today + timedelta(days=67)).strftime("%Y-%m-%d")
    
    # Create the request payload
    payload = {
        "origin": "SFO",
        "destination": "JFK",
        "departure_date": departure_date,
        "return_date": return_date,
        "trip_type": "roundTrip",
        "travelers": [
            {
                "type": "adult",
                "count": 1
            }
        ],
        "cabin_class": "economy",
        "direct_flights_only": False
    }
    
    # Make the API request
    response = requests.post(f"{BASE_URL}/flights/search", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        request_id = data["request_id"]
        print(f"Search initiated with request ID: {request_id}")
        return request_id
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Example natural language flight search
def search_flights_natural_language():
    # Create the request payload
    payload = {
        "text": "I want to book a flight from San Francisco to New York departing on December 10, 2023 and returning December 17, 2023 for 2 adults in economy class."
    }
    
    # Make the API request to process the natural language request
    response = requests.post(f"{BASE_URL}/nlu/process", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["intent"] == "flight_search" and data["request"]:
            # Use the structured request to search for flights
            search_response = requests.post(f"{BASE_URL}/flights/search", json=data["request"])
            
            if search_response.status_code == 200:
                request_id = search_response.json()["request_id"]
                print(f"Search initiated with request ID: {request_id}")
                return request_id
            else:
                print(f"Error: {search_response.status_code}")
                print(search_response.text)
                return None
        else:
            print("Could not parse flight search request from text")
            return None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Check flight search results
def check_flight_results(request_id):
    if not request_id:
        return
    
    response = requests.get(f"{BASE_URL}/flights/search/{request_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total results: {data['total_results']}")
        
        if data['total_results'] > 0:
            # Print the first few results
            print("\nTop flight options:")
            for i, flight in enumerate(data['results'][:3], 1):
                print(f"\nOption {i}:")
                print(f"Price: ${flight['price']}")
                print(f"Duration: {flight['total_duration_minutes']} minutes")
                print(f"Stops outbound: {flight['stops_outbound']}")
                if flight['stops_return'] is not None:
                    print(f"Stops return: {flight['stops_return']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Main execution
if __name__ == "__main__":
    print("=== Structured Flight Search ===\n")
    request_id = search_flights_structured()
    # In a real scenario, you would wait for the background task to complete
    # For now, just assume it's ready
    check_flight_results(request_id)
    
    print("\n=== Natural Language Flight Search ===\n")
    request_id = search_flights_natural_language()
    # In a real scenario, you would wait for the background task to complete
    # For now, just assume it's ready
    check_flight_results(request_id)
