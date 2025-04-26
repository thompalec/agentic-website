from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from api.models import FlightSearchRequest, FlightSearchResponse, ErrorResponse, FlightOption
from browsers.browser_manager import BrowserManager
from browsers.expedia.flight_browser import ExpediaFlightBrowser
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache for active searches
active_searches: Dict[str, Dict[str, Any]] = {}

@router.post("/search", response_model=FlightSearchResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def search_flights(search_request: FlightSearchRequest, background_tasks: BackgroundTasks):
    try:
        # Validate request
        if search_request.trip_type == "roundTrip" and not search_request.return_date:
            raise HTTPException(status_code=400, detail="Return date is required for round-trip flights")
        
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
        background_tasks.add_task(perform_flight_search, request_id, search_request)
        
        # Return initial response with request ID
        return FlightSearchResponse(
            request_id=request_id,
            search_params=search_request,
            results=[],
            total_results=0,
            search_time=active_searches[request_id]["search_time"]
        )
        
    except Exception as e:
        logger.exception("Error starting flight search")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{request_id}", response_model=FlightSearchResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_flight_search_results(request_id: str):
    try:
        # Check if request exists
        if request_id not in active_searches:
            raise HTTPException(status_code=404, detail=f"Flight search with ID {request_id} not found")
        
        search_data = active_searches[request_id]
        
        # Check for errors
        if search_data["error"]:
            raise HTTPException(status_code=500, detail=search_data["error"])
        
        # Reconstruct the search request from stored parameters
        search_request = FlightSearchRequest(**search_data["search_params"])
        
        # Build response
        response = FlightSearchResponse(
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
        logger.exception(f"Error getting flight search results for {request_id}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_flight_search(request_id: str, search_request: FlightSearchRequest):
    """Background task to perform the actual flight search"""
    browser_manager = BrowserManager()
    
    try:
        async with browser_manager.create_page() as page:
            flight_browser = ExpediaFlightBrowser(page)
            
            # Perform search
            await flight_browser.search_flights(search_request)
            
            # Extract results
            results = await flight_browser.extract_flight_results()
            
            # Update search data
            active_searches[request_id]["status"] = "completed"
            active_searches[request_id]["results"] = results
    
    except Exception as e:
        logger.exception(f"Error performing flight search for {request_id}")
        active_searches[request_id]["status"] = "error"
        active_searches[request_id]["error"] = str(e)
