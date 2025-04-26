import uvicorn
from fastapi import FastAPI
from api.router import router as api_router

app = FastAPI(
    title="Travel Booking Agent API",
    description="API for AI agents to interact with travel booking websites",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)