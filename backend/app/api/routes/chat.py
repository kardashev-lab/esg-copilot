from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.models.chat import ChatRequest, ChatResponse, ChatSession, ChatSessionCreate
from app.services.ai_service import AIService
from app.services.vector_store import VectorStore

router = APIRouter()
ai_service = AIService()
vector_store = VectorStore()
logger = logging.getLogger(__name__)

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the AI and get a response"""
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get context documents if specified
        context_documents = []
        if request.context_documents:
            for doc_id in request.context_documents:
                try:
                    chunks = await vector_store.get_document_chunks(doc_id)
                    context_documents.extend(chunks)
                except Exception as e:
                    logger.warning(f"Failed to retrieve document {doc_id}: {e}")
        
        # Generate AI response
        ai_result = await ai_service.generate_response(
            query=request.message,
            context_documents=context_documents,
            framework_focus=request.framework_focus
        )
        
        # Create response
        response = ChatResponse(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            response=ai_result["response"],
            references=ai_result["references"],
            confidence_score=ai_result["confidence_score"],
            processing_time=ai_result["processing_time"],
            suggested_actions=ai_result["suggested_actions"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@router.post("/sessions", response_model=ChatSession)
async def create_session(session_data: ChatSessionCreate):
    """Create a new chat session"""
    
    try:
        session = ChatSession(
            id=str(uuid.uuid4()),
            title=session_data.title,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            tags=session_data.tags
        )
        
        # TODO: Implement database storage for sessions
        logger.info(f"Created new chat session: {session.id}")
        return session
        
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions(limit: int = 20, offset: int = 0):
    """List chat sessions"""
    
    # TODO: Implement database query for sessions
    logger.info(f"Listing sessions with limit={limit}, offset={offset}")
    return []

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """Get a specific chat session"""
    
    # TODO: Implement database query for specific session
    logger.info(f"Requested session: {session_id}")
    raise HTTPException(status_code=404, detail="Session not found")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    
    # TODO: Implement database deletion for session
    logger.info(f"Deleting session: {session_id}")
    return {"message": "Session deleted successfully"}

@router.get("/search")
async def search_documents(query: str, n_results: int = 5, category: Optional[str] = None):
    """Search documents for context"""
    
    try:
        if category:
            results = await vector_store.search_by_category(query, category, n_results)
        else:
            results = await vector_store.search(query, n_results)
        
        logger.info(f"Search completed for query: '{query}', found {len(results)} results")
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )

@router.get("/frameworks")
async def get_available_frameworks():
    """Get list of available ESG frameworks"""
    
    return {
        "frameworks": [
            {
                "id": "gri",
                "name": "Global Reporting Initiative (GRI)",
                "description": "International standards for sustainability reporting",
                "version": "2021"
            },
            {
                "id": "sasb",
                "name": "Sustainability Accounting Standards Board (SASB)",
                "description": "Industry-specific sustainability accounting standards",
                "version": "2018"
            },
            {
                "id": "tcfd",
                "name": "Task Force on Climate-related Financial Disclosures (TCFD)",
                "description": "Framework for climate-related financial risk disclosures",
                "version": "2017"
            },
            {
                "id": "csrd",
                "name": "Corporate Sustainability Reporting Directive (CSRD)",
                "description": "EU directive for sustainability reporting",
                "version": "2022"
            },
            {
                "id": "ifrs",
                "name": "IFRS Sustainability Standards",
                "description": "International sustainability disclosure standards",
                "version": "2023"
            }
        ]
    }

@router.get("/suggestions")
async def get_suggested_questions(framework: Optional[str] = None):
    """Get suggested questions based on framework or general ESG topics"""
    
    general_questions = [
        "How do I start with ESG reporting?",
        "What are the key ESG frameworks I should consider?",
        "How do I conduct a materiality assessment?",
        "What are the main ESG risks for my industry?",
        "How do I measure and report on Scope 1 and 2 emissions?",
        "What are the best practices for stakeholder engagement?",
        "How do I align my ESG strategy with business objectives?",
        "What are the latest ESG regulatory developments?",
        "How do I benchmark my ESG performance against peers?",
        "What are the key components of a sustainability report?"
    ]
    
    framework_questions = {
        "gri": [
            "What are the core GRI principles?",
            "How do I identify material topics for GRI reporting?",
            "What are the GRI Universal Standards requirements?",
            "How do I report on GRI 305 (Emissions)?",
            "What is the difference between GRI Core and Comprehensive options?"
        ],
        "sasb": [
            "How do I identify my SASB industry classification?",
            "What are the financially material topics for my industry?",
            "How do I calculate SASB metrics?",
            "What is the difference between SASB and GRI?",
            "How do I integrate SASB into my existing reporting?"
        ],
        "tcfd": [
            "What are the four TCFD pillars?",
            "How do I assess climate-related risks and opportunities?",
            "What climate scenarios should I consider?",
            "How do I disclose climate-related financial impacts?",
            "What are the TCFD governance requirements?"
        ],
        "csrd": [
            "What is double materiality in CSRD?",
            "Which companies are subject to CSRD?",
            "What are the ESRS requirements?",
            "How do I prepare for CSRD compliance?",
            "What are the assurance requirements under CSRD?"
        ]
    }
    
    if framework and framework in framework_questions:
        return {
            "framework": framework,
            "questions": framework_questions[framework]
        }
    else:
        return {
            "framework": "general",
            "questions": general_questions
        }
