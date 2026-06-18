# Azure opentelemetry integration

import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor
# Import the GenAI instrumentation package
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

# Create a dedicated logger
logger = logging.getLogger("multi-agentic-stack-telemetry")

def setup_telemetry():
    '''
    Sets up Azure Monitor OpenTelemetry configuration.
    Call this once at application startup.
    Tracks: HTTP requests, database queries, errors, performance metrics, and GenAI Agents
    
    No need to log manually each endpoint - it will be done automatically!
    '''

    # Retrieve the connections
    connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')

    if not connection_string:
        logger.warning('No ApplicationInsights connection string found. Telemetry will be disabled.')
        return

    # Configure the Azure Monitor
    try:
        configure_azure_monitor(
            connection_string=connection_string,
            enable_distributed_tracing=True,
            enable_http_instrumentation=True,
            enable_db_instrumentation=True,
            enable_exception_instrumentation=True,
            enable_performance_metrics=True
        )
        logger.info('Azure Monitor OpenTelemetry configured successfully')

        # -------------------------------------------------------------
        # FEATURE ADDITION: Instrument GenAI Agents
        # This maps LLM calls to standard OTel GenAI Semantic Conventions
        # which populates the "Agents (preview)" dashboard.
        # -------------------------------------------------------------
        OpenAIInstrumentor().instrument(
            suppress_assistant_content=False  # Set to True if you want to hide prompt/response text for privacy
        )
        logger.info('OpenAI/GenAI Agent instrumentation enabled successfully')
        # -------------------------------------------------------------

    except Exception as e:
        logger.error(f'Failed to configure Azure Monitor: {e}')

    
'''
Why we use telemetry?

without:
API is slow -> which part is slow?
DB is slow -> which query is slow
How many users logged in today -> No visibility
Agent behavior -> Why did the agent fail to answer? No clue.

with:
API is slow -> which part is slow
DB is slow -> which query is slow
How many users logged in today -> 1000+ (can see)
How many requests per second -> can see
How many errors per second -> can see
Type of error -> 12% of audits failed due to youtube download errors

NEW Agent Capabilities:
Agent Behavior -> Track agent execution steps, token usage, and tool/function choices directly in the dashboard!
'''