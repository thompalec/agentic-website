from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

class TripType(str, Enum):
    ROUND_TRIP = "roundTrip"
    ONE_WAY = "oneWay"
    MULTI_CITY = "multiCity"

class TravelerType(str, Enum):
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"

class CabinClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premiumEconomy"
    BUSINESS = "business"
    FIRST = "first"

class Traveler(BaseModel):
    type: TravelerType
    count: int = Field(ge=1)

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    trip_type: TripType = TripType.ROUND_TRIP
    travelers: List[Traveler] = Field(default_factory=lambda: [Traveler(type=TravelerType.ADULT, count=1)])
    cabin_class: CabinClass = CabinClass.ECONOMY
    direct_flights_only: bool = False

class Airline(BaseModel):
    code: str
    name: str

class AirportLocation(BaseModel):
    code: str
    name: str
    city: str

class FlightSegment(BaseModel):
    airline: Airline
    flight_number: str
    departure: AirportLocation
    arrival: AirportLocation
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    cabin_class: CabinClass

class FlightOption(BaseModel):
    id: str
    price: float
    currency: str = "USD"
    outbound_segments: List[FlightSegment]
    return_segments: Optional[List[FlightSegment]] = None
    total_duration_minutes: int
    stops_outbound: int
    stops_return: Optional[int] = None

class FlightSearchResponse(BaseModel):
    request_id: str
    search_params: FlightSearchRequest
    results: List[FlightOption]
    total_results: int
    currency: str = "USD"
    search_time: datetime

class HotelSearchRequest(BaseModel):
    destination: str
    check_in_date: date
    check_out_date: date
    rooms: int = 1
    adults: int = 2
    children: int = 0

class HotelAmenity(BaseModel):
    name: str
    description: Optional[str] = None

class HotelLocation(BaseModel):
    address: str
    city: str
    state: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HotelRoom(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price_per_night: float
    total_price: float
    currency: str = "USD"
    cancellation_policy: Optional[str] = None
    amenities: List[str] = []

class HotelOption(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    star_rating: float
    review_score: Optional[float] = None
    review_count: Optional[int] = None
    location: HotelLocation
    thumbnail_url: Optional[str] = None
    amenities: List[HotelAmenity] = []
    rooms: List[HotelRoom] = []
    lowest_price: float
    currency: str = "USD"

class HotelSearchResponse(BaseModel):
    request_id: str
    search_params: HotelSearchRequest
    results: List[HotelOption]
    total_results: int
    currency: str = "USD"
    search_time: datetime

class ErrorResponse(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None
