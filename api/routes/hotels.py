from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.models import HotelSearchRequest, HotelSearchResponse, ErrorResponse, HotelOption
from browsers.browser_manager import BrowserManager
from browsers.expedia.hotel_browser import ExpediaHotelBrowser
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache for active searches
active_searches: Dict[str, Dict[str, Any]] = {}

@router.post("/search", response_model=HotelSearchResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def search_hotels(search_request: HotelSearchRequest, background_tasks: BackgroundTasks):
    try:
        # Validate request
        if search_request.check_in_date >= search_request.check_out_date:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Store initial search state
        active_searches[request_id] = {
            "status": "processing",
            "search_params": search_request.dict(),
            "results": [],
            "error": None,
            "search_time": datetime.now()
        }
        
        # Start background task to perform the search
        background_tasks.add_task(perform_hotel_search, request_id, search_request)
        
        # Return initial response with request ID
        return HotelSearchResponse(
            request_id=request_id,
            search_params=search_request,
            results=[],
            total_results=0,
            search_time=active_searches[request_id]["search_time"]
        )
        
    except Exception as e:
        logger.exception("Error starting hotel search")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{request_id}", response_model=HotelSearchResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_hotel_search_results(request_id: str):
    try:
        # Check if request exists
        if request_id not in active_searches:
            raise HTTPException(status_code=404, detail=f"Hotel search with ID {request_id} not found")
        
        search_data = active_searches[request_id]
        
        # Check for errors
        if search_data["error"]:
            raise HTTPException(status_code=500, detail=search_data["error"])
        
        # Reconstruct the search request from stored parameters
        search_request = HotelSearchRequest(**search_data["search_params"])
        
        # Build response
        response = HotelSearchResponse(
            request_id=request_id,
            search_params=search_request,
            results=search_data["results"],
            total_results=len(search_data["results"]),
            search_time=search_data["search_time"]
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting hotel search results for {request_id}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_hotel_search(request_id: str, search_request: HotelSearchRequest):
    """Background task to perform the actual hotel search"""
    browser_manager = BrowserManager()
    
    try:
        async with browser_manager.create_page() as page:
            hotel_browser = ExpediaHotelBrowser(page)
            
            # Perform search
            await hotel_browser.search_hotels(search_request)
            
            # Extract results
            results = await hotel_browser.extract_hotel_results()
            
            # Update search data
            active_searches[request_id]["status"] = "completed"
            active_searches[request_id]["results"] = results
    
    except Exception as e:
        logger.exception(f"Error performing hotel search for {request_id}")
        active_searches[request_id]["status"] = "error"
        active_searches[request_id]["error"] = str(e)
