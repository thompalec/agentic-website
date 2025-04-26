import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000/api"

# Example structured hotel search
def search_hotels_structured():
    # Calculate dates (1 month from now)
    today = datetime.now()
    check_in_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out_date = (today + timedelta(days=35)).strftime("%Y-%m-%d")
    
    # Create the request payload
    payload = {
        "destination": "Los Angeles",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "rooms": 1,
        "adults": 2,
        "children": 0
    }
    
    # Make the API request
    response = requests.post(f"{BASE_URL}/hotels/search", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        request_id = data["request_id"]
        print(f"Search initiated with request ID: {request_id}")
        return request_id
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Example natural language hotel search
def search_hotels_natural_language():
    # Create the request payload
    payload = {
        "text": "I need a hotel in Los Angeles from November 15 to November 20, 2023 for 2 adults and 1 child."
    }
    
    # Make the API request to process the natural language request
    response = requests.post(f"{BASE_URL}/nlu/process", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["intent"] == "hotel_search" and data["request"]:
            # Use the structured request to search for hotels
            search_response = requests.post(f"{BASE_URL}/hotels/search", json=data["request"])
            
            if search_response.status_code == 200:
                request_id = search_response.json()["request_id"]
                print(f"Search initiated with request ID: {request_id}")
                return request_id
            else:
                print(f"Error: {search_response.status_code}")
                print(search_response.text)
                return None
        else:
            print("Could not parse hotel search request from text")
            return None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Check hotel search results
def check_hotel_results(request_id):
    if not request_id:
        return
    
    response = requests.get(f"{BASE_URL}/hotels/search/{request_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total results: {data['total_results']}")
        
        if data['total_results'] > 0:
            # Print the first few results
            print("\nTop hotel options:")
            for i, hotel in enumerate(data['results'][:3], 1):
                print(f"\nOption {i}:")
                print(f"Name: {hotel['name']}")
                print(f"Price: ${hotel['lowest_price']} per night")
                print(f"Rating: {hotel['star_rating']} stars")
                if hotel['review_score']:
                    print(f"Review score: {hotel['review_score']}")
                print(f"Address: {hotel['location']['address']}")
                
                # Print a few amenities if available
                if hotel['amenities']:
                    print("Amenities:")
                    for amenity in hotel['amenities'][:3]:
                        print(f"- {amenity['name']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Main execution
if __name__ == "__main__":
    print("=== Structured Hotel Search ===\n")
    request_id = search_hotels_structured()
    # In a real scenario, you would wait for the background task to complete
    # For now, just assume it's ready
    check_hotel_results(request_id)
    
    print("\n=== Natural Language Hotel Search ===\n")
    request_id = search_hotels_natural_language()
    # In a real scenario, you would wait for the background task to complete
    # For now, just assume it's ready
    check_hotel_results(request_id)
