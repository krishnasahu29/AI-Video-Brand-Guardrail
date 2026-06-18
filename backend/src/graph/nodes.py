import json
import os
import logging
import re
from typing import Dict, Any, List

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Import state schema
from backend.src.graph.state import VideoAuditState, ComplianceIssue

# Import service
from backend.src.services.video_indexer import VideoIndexerService

#Configure the logger
logger = logging.getLogger("multi-agentic-stack")
logging.basicConfig(level=logging.INFO)

# Node 1: Indexer
# Function responsible for converting video to text
def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Downloads the youtube video from the URL
    Uploads to the Azure Video Indexer
    Extracts the insights

    :param state: Description
    :type state: VideoAuditState
    :return: Description
    :rtype: Dict[str, Any]
    """

    video_url = state.get('video_url')
    video_id_input = state.get('video_id', 'vid_demo')

    logger.info(f"----[Node:Indexer] Processing: {video_url}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()
        # download 
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise Exception("Please provide valid URL for this test.")
            
        # Upload
        azure_video_id = vi_service.upload_video(local_path, video_name=video_id_input)
        logger.info(f"Upload Success. Azure ID: {azure_video_id}")

        # Cleanup
        if os.path.exists(local_path):
            os.remove(local_path)
        
        # Wait 
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        # Extract
        clean_data = vi_service.extract_data(raw_insights)

        logger.info("----Node[Indexer] Extraction Complete -------")

        return clean_data

    except Exception as e:
        logger.error(f"Video Indexer failed : {e}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": []
        }

# Node 2 : Compliance Auditor
def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Performs RAG to audit the content - brand video
    
    :param state: Description
    :type state: VideoAuditState
    :return: Description
    :rtype: Dict[str, Any]
    """

    logger.info("----[Node: Auditor] querying knowledge base and LLM")
    transcript = state.get("transcript", "")

    if not transcript:
        logger.warning("No transcript available, Skipping Audit")
        return {
            "compliance_results": [],
            "final_status": "FAIL",
            "final_report": "Audit Skipped because video auditing failed (No Transcript.)",
        }

    # Initialize azure clients
    llm = AzureChatOpenAI(
        azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature = 0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-small",
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vector_store = AzureSearch(
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"),
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function = embeddings.embed_query,
    )

    # RAG Retrival
    ocr_text = state.get("ocr_text", [])
    query_text = f"{transcript} {''.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    retrieved_rules = "\n\n".join([doc.page_content for doc in docs])

    system_prompt = f"""
            You are a senior brand compliance auditor.
            OFFICIAL REGULATORY RULES:
            {retrieved_rules}
            INSTRUCTIONS:
            1. Analyse the transcript and ocr text below.
            2. Identify ANY violation of the rules.
            3. Return the result in a JSON format strictly, follow the below format:
            {{
                "compliance_results": [
                    {{
                    "category": "Claim Validation",
                    "severity": "CRITICAL",
                    "description": "Explanation of the violation..."
                    }}
                ],
                "final_status": "FAIL",
                "final_report": "Summary of findings..."
            }}

            If no violations are found, set "final_status" to "PASS" and "compliance_results" to [].
    """

    user_message = f"""
                VIDEO_METADATA: {state.get('video_metadata', {})}
                TRANSCRIPT: {transcript}
                ON-SCREEN TEXT (OCR): {ocr_text}
    """

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content = response.content

        if "```" in content:
            content = re.search(r"```(?:json)?(.?)```", content, re.DOTALL).group(1)
        
        audit_data = json.loads(content.strip())

        final_status = audit_data.get('final_status') or audit_data.get('status')
        if not final_status:
            final_status = 'FAIL' if audit_data.get('compliance_results') else 'PASS'

        return {
            'compliance_results': audit_data.get("compliance_results", []),
            'final_status': final_status,
            'final_report': audit_data.get('final_report', 'No report generated')
        }

    except Exception as e:
        logger.error(f"Auditor Node failed : {str(e)}")

        # logging the raw response
        logger.error(f"Raw LLM response: {response.content if 'response' in locals() else 'Not Available'} ")

        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "final_report": "Audit failed due to technical error."
        }