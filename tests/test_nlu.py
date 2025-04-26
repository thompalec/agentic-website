import pytest
from utils.nlu_processor import NLUProcessor
from api.models import TripType, CabinClass

@pytest.fixture
def nlu_processor():
    return NLUProcessor()

def test_extract_intent_flight(nlu_processor):
    text = "I want to book a flight from New York to London on December 15, 2023"
    intent_info = nlu_processor.extract_intent(text)
    assert intent_info["intent"] == "flight_search"
    assert intent_info["confidence"] > 0.5

def test_extract_intent_hotel(nlu_processor):
    text = "I need a hotel in Paris from June 10 to June 15, 2023"
    intent_info = nlu_processor.extract_intent(text)
    assert intent_info["intent"] == "hotel_search"
    assert intent_info["confidence"] > 0.5

def test_parse_flight_search_request(nlu_processor):
    text = "I want to book a flight from New York to London on December 15, 2023 returning December 25, 2023"
    request = nlu_processor.parse_flight_search_request(text)
    
    assert request is not None
    assert request.origin == "New York"
    assert request.destination == "London"
    assert request.trip_type == TripType.ROUND_TRIP
    assert request.cabin_class == CabinClass.ECONOMY

def test_parse_hotel_search_request(nlu_processor):
    text = "I need a hotel in Paris from June 10 to June 15, 2023 for 2 adults and 1 child"
    request = nlu_processor.parse_hotel_search_request(text)
    
    assert request is not None
    assert request.destination == "Paris"
    assert request.adults == 2
    assert request.children == 1
