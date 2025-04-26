from fastapi import APIRouter
from api.routes import flights, hotels, nlu

router = APIRouter()

router.include_router(flights.router, prefix="/flights", tags=["flights"])
router.include_router(hotels.router, prefix="/hotels", tags=["hotels"])
router.include_router(nlu.router, prefix="/nlu", tags=["nlu"])

@router.get("/", tags=["health"])
async def health_check():
    return {"status": "healthy", "message": "Travel booking agent API is running"}
