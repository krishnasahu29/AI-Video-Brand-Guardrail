import operator
from typing import Annotated, List, Dict, Optional, Any, TypedDict

# define the schema for a single compliance result
# Error report structure

class ComplianceIssue(TypedDict):
    category: str # FTC disclosure
    description: str # Specific detail of violation
    severity: str # Criticality
    timestamp: Optional[str]

# Define the global graph state
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langgraph execution content
    Main container: holds all the info about the audit right 
    from the initial URL to the final report
    '''
    # Input Parameters
    video_url: str
    video_id: str

    # Ingestion and Extraction data
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]  # {duration: '15', resolution: "1080p"}
    transcript: Optional[str] # Fully extracted speech-to-text
    ocr_text: List[str]

    # Analysis output: list of all the violations found by AI
    compliance_results: Annotated[List[ComplianceIssue], operator.add]

    # Final deliverables
    final_status: str # PASS | FAIL | PENDING
    final_report: str # markdown format

    # System Observability
    # errors: API timeout, system level errors
    # Stores list of system level crashes
    errors: Annotated[List[str], operator.add]
    