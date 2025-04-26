from browsers.base_browser import BaseBrowserActions
from playwright.async_api import Page
from config.settings import EXPEDIA_URL
from api.models import HotelSearchRequest, HotelOption, HotelRoom, HotelLocation, HotelAmenity
from typing import List, Dict, Any, Optional
import logging
import uuid
import re
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ExpediaHotelBrowser(BaseBrowserActions):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = EXPEDIA_URL
        self.hotel_url = f"{self.base_url}Hotels"
    
    async def navigate_to_hotels(self):
        """Navigate to the hotels page"""
        await self.navigate(self.hotel_url)
        
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
    
    async def search_hotels(self, search_params: HotelSearchRequest) -> str:
        """Perform a hotel search with the given parameters"""
        await self.navigate_to_hotels()
        
        # Fill destination
        await self.fill_input('[data-testid="destination-input"]', search_params.destination)
        await asyncio.sleep(1)
        await self.click('[data-testid="destination-suggestion"]')
        
        # Set dates
        check_in_date = search_params.check_in_date.strftime("%m/%d/%Y")
        check_out_date = search_params.check_out_date.strftime("%m/%d/%Y")
        
        await self.fill_input('[data-testid="check-in-date-input"]', check_in_date)
        await self.fill_input('[data-testid="check-out-date-input"]', check_out_date)
        
        # Set travelers
        await self.click('[data-testid="travelers-field"]')
        
        # Set rooms
        rooms = search_params.rooms
        current_rooms = 1  # Default is 1
        
        # Add more rooms if needed
        for _ in range(rooms - current_rooms):
            await self.click('[data-testid="add-room"]')
        
        # Set adults
        adults = search_params.adults
        current_adults = 2  # Default is 2
        
        if adults > current_adults:
            # Add more adults
            for _ in range(adults - current_adults):
                await self.click('[data-testid="adults-increase"]')
        elif adults < current_adults:
            # Remove adults
            for _ in range(current_adults - adults):
                await self.click('[data-testid="adults-decrease"]')
        
        # Set children
        children = search_params.children
        for _ in range(children):
            await self.click('[data-testid="children-increase"]')
        
        # Done with travelers
        await self.click('[data-testid="travelers-done"]')
        
        # Submit search
        await self.click('[data-testid="search-button"]')
        
        # Wait for results page to load
        await self.wait_for_selector('[data-testid="hotel-card"]', timeout=30000)
        
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        return request_id
    
    async def extract_hotel_results(self) -> List[HotelOption]:
        """Extract hotel results from the search results page"""
        # Wait for hotel cards to be visible
        await self.wait_for_selector('[data-testid="hotel-card"]', timeout=30000)
        
        # Get the HTML content to parse with BeautifulSoup
        html = await self.get_page_html()
        soup = BeautifulSoup(html, 'html.parser')
        
        hotel_cards = soup.select('[data-testid="hotel-card"]')
        results = []
        
        for i, card in enumerate(hotel_cards):
            try:
                hotel_id = f"hotel_{i}_{uuid.uuid4().hex[:8]}"
                
                # Hotel name
                name_element = card.select_one('.hotel-name')
                name = name_element.get_text(strip=True) if name_element else f"Hotel {i+1}"
                
                # Price
                price_element = card.select_one('.price')
                price_text = price_element.get_text(strip=True) if price_element else "0"
                price = float(re.sub(r'[^\d.]', '', price_text or "0"))
                
                # Rating
                rating_element = card.select_one('.star-rating')
                rating_text = rating_element.get_text(strip=True) if rating_element else "0"
                star_rating = float(re.sub(r'[^\d.]', '', rating_text or "0"))
                
                # Review score
                review_element = card.select_one('.review-score')
                review_score = float(review_element.get_text(strip=True)) if review_element else None
                
                # Review count
                review_count_element = card.select_one('.review-count')
                review_count_text = review_count_element.get_text(strip=True) if review_count_element else "0"
                review_count = int(re.sub(r'[^\d]', '', review_count_text or "0"))
                
                # Location
                address_element = card.select_one('.address')
                address = address_element.get_text(strip=True) if address_element else "Unknown location"
                
                # Create a simple location object
                location = {
                    "address": address,
                    "city": "Unknown",  # Would parse from address in real implementation
                    "country": "Unknown",  # Would parse from address in real implementation
                }
                
                # Thumbnail URL
                thumbnail_element = card.select_one('img')
                thumbnail_url = thumbnail_element.get('src') if thumbnail_element else None
                
                # Amenities
                amenity_elements = card.select('.amenity')
                amenities = []
                for amenity_el in amenity_elements:
                    amenity_name = amenity_el.get_text(strip=True)
                    amenities.append({"name": amenity_name})
                
                # Create a sample room
                room = {
                    "id": f"room_{uuid.uuid4().hex[:8]}",
                    "name": "Standard Room",
                    "price_per_night": price,
                    "total_price": price,  # Would calculate based on stay duration
                    "currency": "USD",
                }
                
                hotel_option = {
                    "id": hotel_id,
                    "name": name,
                    "star_rating": star_rating,
                    "review_score": review_score,
                    "review_count": review_count,
                    "location": location,
                    "thumbnail_url": thumbnail_url,
                    "amenities": amenities,
                    "rooms": [room],
                    "lowest_price": price,
                    "currency": "USD"
                }
                
                results.append(hotel_option)
                
            except Exception as e:
                logger.error(f"Error parsing hotel card {i}: {str(e)}")
        
        return results
