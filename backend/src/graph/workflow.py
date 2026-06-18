'''
This module defines the DAG : Directed Acyclic Graph that orchestrates the video compliance
audit process.
It connects the nodes using the StateGraph from LangGraph

START -> index_video_node -> audio_content_node -> END
'''

import logging
from langgraph.graph import StateGraph, START, END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import index_video_node, audio_content_node

logger = logging.getLogger("multi-agentic-stack")

def create_graph():
    '''
    Constructs and compiles the Langgraph workflow
    Returns:
        CompiledGraph : The compiled workflow ready to run
    '''
    # 1. Init the builder with State
    app_builder = StateGraph(VideoAuditState)

    # 2. Register Nodes
    app_builder.add_node("indexer", index_video_node)
    app_builder.add_node("auditor", audio_content_node)

    # 3. Define Edges (Flow)
    app_builder.add_edge(START, "indexer")
    app_builder.add_edge("indexer", "auditor")
    app_builder.add_edge("auditor", END)

    # 4. Compile
    return app_builder.compile()

# Expose this runnable app
app = create_graph()
