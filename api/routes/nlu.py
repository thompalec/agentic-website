from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from utils.nlu_processor import NLUProcessor
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize NLU processor
nlu_processor = NLUProcessor()

@router.post("/process")
async def process_natural_language(request: Dict[str, Any] = Body(...)):
    """Process a natural language request and convert it to structured data"""
    try:
        if "text" not in request:
            raise HTTPException(status_code=400, detail="Text field is required")
        
        text = request["text"]
        
        # Process the text using the NLU processor
        result = nlu_processor.process_agent_request(text)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing natural language request")
        raise HTTPException(status_code=500, detail=str(e))
