from browsers.base_browser import BaseBrowserActions
from playwright.async_api import Page
from config.settings import EXPEDIA_URL
from api.models import FlightSearchRequest, FlightOption, FlightSegment, Airline, AirportLocation
from typing import List, Dict, Any, Optional
import logging
import json
import uuid
import re
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ExpediaFlightBrowser(BaseBrowserActions):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = EXPEDIA_URL
        self.flight_url = f"{self.base_url}Flights"
        
    async def navigate_to_flights(self):
        """Navigate to the flights page"""
        await self.navigate(self.flight_url)
        
        # Handle any pop-ups or cookie banners that might appear
        await self._handle_popups()
        
    async def _handle_popups(self):
        """Handle common popups like cookie notices"""
        # Accept cookies button
        cookie_button = await self.wait_for_selector('button[id="accept-cookies"]', timeout=5000)
        if cookie_button:
            await cookie_button.click()
            logger.info("Accepted cookies")
        
        # Close any other popups that might appear
        close_buttons = [
            'button[aria-label="Close"]',
            'button.close',
            '.modal-close'
        ]
        
        for selector in close_buttons:
            button = await self.wait_for_selector(selector, timeout=2000)
            if button:
                await button.click()
                logger.info(f"Closed popup with selector: {selector}")
    
    async def search_flights(self, search_params: FlightSearchRequest) -> str:
        """Perform a flight search with the given parameters"""
        await self.navigate_to_flights()
        
        # Set trip type
        if search_params.trip_type == "oneWay":
            await self.click('[data-testid="trip-type-one-way"]')
        elif search_params.trip_type == "roundTrip":
            await self.click('[data-testid="trip-type-roundtrip"]')
        
        # Fill origin and destination
        await self.fill_input('[data-testid="origin-input"]', search_params.origin)
        await asyncio.sleep(1)
        await self.click('[data-testid="origin-suggestion"]')
        
        await self.fill_input('[data-testid="destination-input"]', search_params.destination)
        await asyncio.sleep(1)
        await self.click('[data-testid="destination-suggestion"]')
        
        # Set dates
        departure_date = search_params.departure_date.strftime("%m/%d/%Y")
        await self.fill_input('[data-testid="departure-date-input"]', departure_date)
        
        if search_params.return_date and search_params.trip_type == "roundTrip":
            return_date = search_params.return_date.strftime("%m/%d/%Y")
            await self.fill_input('[data-testid="return-date-input"]', return_date)
        
        # Set cabin class
        await self.click('[data-testid="cabin-class-dropdown"]')
        cabin_map = {
            "economy": '[data-testid="cabin-economy"]',
            "premiumEconomy": '[data-testid="cabin-premium-economy"]',
            "business": '[data-testid="cabin-business"]',
            "first": '[data-testid="cabin-first"]'
        }
        await self.click(cabin_map.get(search_params.cabin_class, cabin_map["economy"]))
        
        # Set travelers
        total_travelers = sum(traveler.count for traveler in search_params.travelers)
        await self.click('[data-testid="travelers-field"]')
        
        # Reset to 1 adult first
        await self.click('[data-testid="adult-counter-decrease"]', timeout=5000)
        
        # Add adults
        adult_count = next((t.count for t in search_params.travelers if t.type == "adult"), 1)
        for _ in range(adult_count - 1):  # -1 because there's already 1 adult by default
            await self.click('[data-testid="adult-counter-increase"]')
        
        # Add children
        child_count = next((t.count for t in search_params.travelers if t.type == "child"), 0)
        for _ in range(child_count):
            await self.click('[data-testid="children-counter-increase"]')
        
        # Add infants
        infant_count = next((t.count for t in search_params.travelers if t.type == "infant"), 0)
        for _ in range(infant_count):
            await self.click('[data-testid="infant-counter-increase"]')
        
        # Done with travelers
        await self.click('[data-testid="travelers-done"]')
        
        # Direct flights only
        if search_params.direct_flights_only:
            await self.click('[data-testid="direct-flights-only"]')
        
        # Submit search
        await self.click('[data-testid="search-button"]')
        
        # Wait for results page to load
        await self.wait_for_selector('[data-testid="flight-card"]', timeout=30000)
        
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        return request_id
    
    async def extract_flight_results(self) -> List[FlightOption]:
        """Extract flight results from the search results page"""
        # Wait for flight cards to be visible
        await self.wait_for_selector('[data-testid="flight-card"]', timeout=30000)
        
        # Get the HTML content to parse with BeautifulSoup
        html = await self.get_page_html()
        soup = BeautifulSoup(html, 'html.parser')
        
        flight_cards = soup.select('[data-testid="flight-card"]')
        results = []
        
        for i, card in enumerate(flight_cards):
            try:
                flight_id = f"flight_{i}_{uuid.uuid4().hex[:8]}"
                
                # Price
                price_element = card.select_one('.price')
                price_text = price_element.get_text(strip=True) if price_element else "0"
                price = float(re.sub(r'[^\d.]', '', price_text or "0"))
                
                # Airlines
                airline_elements = card.select('.airline-name')
                airlines = [el.get_text(strip=True) for el in airline_elements]
                
                # Segments
                outbound_segments = []
                return_segments = []
                
                # Flight details
                flight_details = card.select('.flight-details')
                
                # Process outbound segments
                if len(flight_details) > 0:
                    outbound_segments = self._parse_flight_segments(flight_details[0], airlines[0] if airlines else "Unknown")
                
                # Process return segments if round trip
                if len(flight_details) > 1:
                    return_segments = self._parse_flight_segments(flight_details[1], airlines[-1] if airlines else "Unknown")
                
                # Duration
                duration_element = card.select_one('.duration')
                duration_text = duration_element.get_text(strip=True) if duration_element else "0h 0m"
                duration_minutes = self._parse_duration(duration_text)
                
                # Stops
                stops_outbound = len(outbound_segments) - 1 if outbound_segments else 0
                stops_return = len(return_segments) - 1 if return_segments else None
                
                flight_option = {
                    "id": flight_id,
                    "price": price,
                    "currency": "USD",
                    "outbound_segments": outbound_segments,
                    "return_segments": return_segments if return_segments else None,
                    "total_duration_minutes": duration_minutes,
                    "stops_outbound": stops_outbound,
                    "stops_return": stops_return
                }
                
                results.append(flight_option)
                
            except Exception as e:
                logger.error(f"Error parsing flight card {i}: {str(e)}")
        
        return results
    
    def _parse_flight_segments(self, flight_detail_element, airline_name) -> List[Dict[str, Any]]:
        """Parse flight segments from a flight detail element"""
        segments = []
        
        # This is a simplified version - in a real implementation you'd need to 
        # handle the specific structure of the Expedia flight details element
        # which would need adjustment based on actual DOM structure
        
        # For demonstration purposes, creating a mock segment
        segment = {
            "airline": {
                "code": airline_name[:2].upper(),
                "name": airline_name
            },
            "flight_number": "FL123",
            "departure": {
                "code": "DEP",
                "name": "Departure Airport",
                "city": "Departure City"
            },
            "arrival": {
                "code": "ARR",
                "name": "Arrival Airport",
                "city": "Arrival City"
            },
            "departure_time": datetime.now().isoformat(),
            "arrival_time": datetime.now().isoformat(),
            "duration_minutes": 120,
            "cabin_class": "economy"
        }
        
        segments.append(segment)
        return segments
    
    def _parse_duration(self, duration_text: str) -> int:
        """Parse duration text (e.g., '2h 30m') into minutes"""
        hours = 0
        minutes = 0
        
        # Extract hours
        hours_match = re.search(r'(\d+)h', duration_text)
        if hours_match:
            hours = int(hours_match.group(1))
        
        # Extract minutes
        minutes_match = re.search(r'(\d+)m', duration_text)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        
        return hours * 60 + minutes
