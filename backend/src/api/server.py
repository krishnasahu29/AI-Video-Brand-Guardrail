# FastAPI

import uuid
import logging
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from typing import List, Optional

# Load env var
from dotenv import load_dotenv
load_dotenv(override=True)

# Initialize telemetry
from backend.src.api.telemetry import setup_telemetry
setup_telemetry()

# Import langgraph workflow
from backend.src.graph.workflow import app as compliance_graph


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("app-server")

# Create the FastAPI application
app = FastAPI(
    title="Multi-Agentic Compliance Stack",
    description='API for auditing video content against the brand compliance rules',
    version='1.0.0'
    )

# Define the data models
class AuditRequest(BaseModel):
    '''
    Defines the expected structure of incoming API requests
    '''
    video_url: str

class ComplianceIssue(BaseModel):
    category: str
    severity: str
    description: str
    
class AuditResponse(BaseModel):
    session_id: str
    video_id: str
    status: str
    compliance_results: List[ComplianceIssue]

# Define the main endpoint
@app.post("/audit", response_model=AuditResponse)

async def submit_audit(request: AuditRequest):
    """
    Main API endpoint that triggers the compliant audit workflow
    """

    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"
    logger.info(f"New audit request for {request.video_url} (Session : {session_id})")

    # Graph inputs
    initial_inputs = {
        "video_url": request.video_url,
        "video_id": video_id_short,
        "compliance_results": [],
        "errors": []
    }

    try:
        final_state = compliance_graph.invoke(initial_inputs)
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "UNKNOWN"),
            final_report=final_state.get("final_report", "No Report Generated"),
            compliance_results=final_state.get("compliance_results", [])
        )

    except Exception as e:
        logger.error(f"Error processing audit: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check Endpoint
@app.get("/health")

def health_check():
    '''
    Endpoint to verify if API is working or not
    '''
    return {"status": "healthy", "service": "Multi-Agentic Compliance Stack"}