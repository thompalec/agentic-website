from typing import Dict, Any, List, Optional, Union
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
import re
from datetime import datetime, date
from api.models import FlightSearchRequest, HotelSearchRequest, TripType, CabinClass, Traveler, TravelerType

logger = logging.getLogger(__name__)

class NLUProcessor:
    def __init__(self):
        """Initialize the NLU processor"""
        # Load pre-trained model for NLU tasks
        # In a production environment, you'd load an actual model here
        # For demo purposes, we're using a rule-based approach
        pass
    
    def parse_flight_search_request(self, text: str) -> Optional[FlightSearchRequest]:
        """Parse a natural language flight search request"""
        try:
            # Extract origin/destination
            origin_match = re.search(r'from\s+([\w\s]+?)\s+to', text, re.IGNORECASE)
            dest_match = re.search(r'to\s+([\w\s]+?)\s+(on|for|leaving|departing)', text, re.IGNORECASE)
            
            if not origin_match or not dest_match:
                logger.warning("Could not extract origin/destination from text")
                return None
            
            origin = origin_match.group(1).strip()
            destination = dest_match.group(1).strip()
            
            # Extract dates
            departure_match = re.search(r'(on|departing|leaving)\s+([\w\s,]+?)\s+(and|returning|coming|to)', text, re.IGNORECASE)
            return_match = re.search(r'(returning|coming back)\s+([\w\s,]+?)\s*(\.|$|for)', text, re.IGNORECASE)
            
            if not departure_match:
                logger.warning("Could not extract departure date from text")
                return None
            
            # Parse dates (in a real implementation, use a date parser like dateutil)
            # For demo, assume a fixed date format
            departure_date = self._parse_date_string(departure_match.group(2).strip())
            return_date = None
            
            if return_match:
                return_date = self._parse_date_string(return_match.group(2).strip())
                trip_type = TripType.ROUND_TRIP
            else:
                trip_type = TripType.ONE_WAY
            
            # Extract cabin class
            cabin_class = CabinClass.ECONOMY
            if re.search(r'business\s+class', text, re.IGNORECASE):
                cabin_class = CabinClass.BUSINESS
            elif re.search(r'first\s+class', text, re.IGNORECASE):
                cabin_class = CabinClass.FIRST
            elif re.search(r'premium\s+economy', text, re.IGNORECASE):
                cabin_class = CabinClass.PREMIUM_ECONOMY
            
            # Extract travelers
            adult_match = re.search(r'(\d+)\s+adults?', text, re.IGNORECASE)
            child_match = re.search(r'(\d+)\s+child(ren)?', text, re.IGNORECASE)
            infant_match = re.search(r'(\d+)\s+infants?', text, re.IGNORECASE)
            
            travelers = []
            
            # Add adults
            adult_count = int(adult_match.group(1)) if adult_match else 1
            travelers.append(Traveler(type=TravelerType.ADULT, count=adult_count))
            
            # Add children if specified
            if child_match:
                child_count = int(child_match.group(1))
                travelers.append(Traveler(type=TravelerType.CHILD, count=child_count))
            
            # Add infants if specified
            if infant_match:
                infant_count = int(infant_match.group(1))
                travelers.append(Traveler(type=TravelerType.INFANT, count=infant_count))
            
            # Extract direct flights preference
            direct_flights_only = bool(re.search(r'direct\s+(flights?|only)', text, re.IGNORECASE))
            
            return FlightSearchRequest(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                trip_type=trip_type,
                travelers=travelers,
                cabin_class=cabin_class,
                direct_flights_only=direct_flights_only
            )
        
        except Exception as e:
            logger.exception(f"Error parsing flight search request: {str(e)}")
            return None
    
    def parse_hotel_search_request(self, text: str) -> Optional[HotelSearchRequest]:
        """Parse a natural language hotel search request"""
        try:
            # Extract destination
            destination_match = re.search(r'(hotel|stay|accommodation)\s+in\s+([\w\s]+?)\s+(from|for|starting)', text, re.IGNORECASE)
            
            if not destination_match:
                logger.warning("Could not extract destination from text")
                return None
            
            destination = destination_match.group(2).strip()
            
            # Extract dates
            check_in_match = re.search(r'(from|starting|check\s+in)\s+([\w\s,]+?)\s+(to|until|through)', text, re.IGNORECASE)
            check_out_match = re.search(r'(to|until|through|check\s+out)\s+([\w\s,]+?)\s*(\.|$|for)', text, re.IGNORECASE)
            
            if not check_in_match or not check_out_match:
                logger.warning("Could not extract check-in/check-out dates from text")
                return None
            
            # Parse dates (in a real implementation, use a date parser like dateutil)
            check_in_date = self._parse_date_string(check_in_match.group(2).strip())
            check_out_date = self._parse_date_string(check_out_match.group(2).strip())
            
            # Extract rooms and guests
            rooms_match = re.search(r'(\d+)\s+rooms?', text, re.IGNORECASE)
            adults_match = re.search(r'(\d+)\s+adults?', text, re.IGNORECASE)
            children_match = re.search(r'(\d+)\s+child(ren)?', text, re.IGNORECASE)
            
            rooms = int(rooms_match.group(1)) if rooms_match else 1
            adults = int(adults_match.group(1)) if adults_match else 2
            children = int(children_match.group(1)) if children_match else 0
            
            return HotelSearchRequest(
                destination=destination,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                rooms=rooms,
                adults=adults,
                children=children
            )
        
        except Exception as e:
            logger.exception(f"Error parsing hotel search request: {str(e)}")
            return None
    
    def _parse_date_string(self, date_string: str) -> date:
        """Parse a date string into a date object"""
        # In a real implementation, use a robust date parser
        # For demo purposes, assume a date format like "January 15, 2023" or "01/15/2023"
        try:
            # Try to parse as "January 15, 2023"
            return datetime.strptime(date_string, "%B %d, %Y").date()
        except ValueError:
            try:
                # Try to parse as "01/15/2023"
                return datetime.strptime(date_string, "%m/%d/%Y").date()
            except ValueError:
                # Default to a future date for demo purposes
                return date.today().replace(year=date.today().year + 1)
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extract the intent from a natural language request"""
        # In a real implementation, use a trained classifier
        # For demo purposes, using a rule-based approach
        
        if re.search(r'flight|fly', text, re.IGNORECASE):
            return {"intent": "flight_search", "confidence": 0.9}
        elif re.search(r'hotel|stay|accommodation', text, re.IGNORECASE):
            return {"intent": "hotel_search", "confidence": 0.9}
        else:
            return {"intent": "unknown", "confidence": 0.5}
    
    def process_agent_request(self, text: str) -> Dict[str, Any]:
        """Process a natural language request from an AI agent"""
        # Extract intent
        intent_info = self.extract_intent(text)
        intent = intent_info["intent"]
        
        response = {
            "intent": intent,
            "confidence": intent_info["confidence"],
            "request": None,
            "error": None
        }
        
        if intent == "flight_search":
            request = self.parse_flight_search_request(text)
            if request:
                response["request"] = request.dict()
            else:
                response["error"] = "Could not parse flight search request"
        
        elif intent == "hotel_search":
            request = self.parse_hotel_search_request(text)
            if request:
                response["request"] = request.dict()
            else:
                response["error"] = "Could not parse hotel search request"
        
        else:
            response["error"] = "Unknown intent"
        
        return response
