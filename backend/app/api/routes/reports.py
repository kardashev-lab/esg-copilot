from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.services.ai_service import AIService
from app.services.vector_store import VectorStore

router = APIRouter()
ai_service = AIService()
vector_store = VectorStore()

class ReportRequest(BaseModel):
    title: str
    framework: str  # GRI, SASB, TCFD, CSRD
    sections: List[str]
    company_data_documents: List[str] = []
    peer_reports: List[str] = []
    custom_instructions: Optional[str] = None

class ReportSection(BaseModel):
    id: str
    title: str
    content: str
    status: str  # draft, completed, reviewed
    word_count: int
    created_at: datetime
    updated_at: datetime

class Report(BaseModel):
    id: str
    title: str
    framework: str
    status: str  # draft, in_progress, completed
    sections: List[ReportSection]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}

@router.post("/generate", response_model=Report)
async def generate_report(request: ReportRequest):
    """Generate a sustainability report based on framework and company data"""
    
    try:
        report_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Get company data documents
        company_context = []
        for doc_id in request.company_data_documents:
            chunks = await vector_store.get_document_chunks(doc_id)
            company_context.extend(chunks)
        
        # Get peer report context
        peer_context = []
        for doc_id in request.peer_reports:
            chunks = await vector_store.get_document_chunks(doc_id)
            peer_context.extend(chunks)
        
        # Generate sections
        sections = []
        for section_title in request.sections:
            section_id = str(uuid.uuid4())
            
            # Create section prompt
            section_prompt = f"""
            Generate the '{section_title}' section for a {request.framework} sustainability report.
            
            Company Context: {company_context[:3] if company_context else 'No company data provided'}
            Peer Context: {peer_context[:2] if peer_context else 'No peer data provided'}
            
            Custom Instructions: {request.custom_instructions or 'Follow standard reporting practices'}
            
            Please provide a comprehensive, professional section that follows {request.framework} guidelines.
            """
            
            # Generate section content
            ai_result = await ai_service.generate_response(
                query=section_prompt,
                context_documents=company_context + peer_context,
                framework_focus=request.framework.upper()
            )
            
            section = ReportSection(
                id=section_id,
                title=section_title,
                content=ai_result["response"],
                status="draft",
                word_count=len(ai_result["response"].split()),
                created_at=now,
                updated_at=now
            )
            sections.append(section)
        
        report = Report(
            id=report_id,
            title=request.title,
            framework=request.framework,
            status="draft",
            sections=sections,
            created_at=now,
            updated_at=now,
            metadata={
                "company_documents": request.company_data_documents,
                "peer_reports": request.peer_reports,
                "custom_instructions": request.custom_instructions
            }
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

@router.post("/{report_id}/sections/{section_id}/regenerate")
async def regenerate_section(report_id: str, section_id: str, instructions: Optional[str] = None):
    """Regenerate a specific section of a report"""
    
    try:
        # In a real implementation, fetch the report and section from database
        # For now, return a mock response
        
        return {
            "message": "Section regenerated successfully",
            "section_id": section_id,
            "updated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating section: {str(e)}"
        )

@router.get("/templates")
async def get_report_templates():
    """Get available report templates by framework"""
    
    templates = {
        "GRI": {
            "name": "GRI Standards Report Template",
            "sections": [
                "Organizational Profile",
                "Material Topics and Boundaries",
                "Stakeholder Engagement",
                "Report Profile",
                "Governance",
                "Ethics and Integrity",
                "Strategy, Policies, and Practices",
                "Environmental Performance",
                "Social Performance",
                "Economic Performance"
            ],
            "description": "Comprehensive template following GRI Universal Standards 2021"
        },
        "SASB": {
            "name": "SASB Standards Report Template",
            "sections": [
                "Business Model and Innovation",
                "Leadership and Governance",
                "Risk and Risk Management",
                "Metrics and Targets",
                "Industry-Specific Disclosures"
            ],
            "description": "Template focused on financially material sustainability information"
        },
        "TCFD": {
            "name": "TCFD Climate Report Template",
            "sections": [
                "Governance",
                "Strategy",
                "Risk Management",
                "Metrics and Targets"
            ],
            "description": "Template for climate-related financial disclosures"
        },
        "CSRD": {
            "name": "CSRD Sustainability Report Template",
            "sections": [
                "General Information",
                "Environmental Matters",
                "Social Matters",
                "Governance Matters",
                "Double Materiality Assessment",
                "Sustainability Strategy",
                "Sustainability Due Diligence",
                "Remuneration"
            ],
            "description": "Template aligned with EU Corporate Sustainability Reporting Directive"
        }
    }
    
    return {"templates": templates}

@router.get("/frameworks/{framework}/sections")
async def get_framework_sections(framework: str):
    """Get recommended sections for a specific framework"""
    
    framework_sections = {
        "gri": [
            "Organizational Profile",
            "Material Topics and Boundaries",
            "Stakeholder Engagement",
            "Report Profile",
            "Governance",
            "Ethics and Integrity",
            "Strategy, Policies, and Practices",
            "Environmental Performance",
            "Social Performance",
            "Economic Performance"
        ],
        "sasb": [
            "Business Model and Innovation",
            "Leadership and Governance",
            "Risk and Risk Management",
            "Metrics and Targets",
            "Industry-Specific Disclosures"
        ],
        "tcfd": [
            "Governance",
            "Strategy",
            "Risk Management",
            "Metrics and Targets"
        ],
        "csrd": [
            "General Information",
            "Environmental Matters",
            "Social Matters",
            "Governance Matters",
            "Double Materiality Assessment",
            "Sustainability Strategy",
            "Sustainability Due Diligence",
            "Remuneration"
        ]
    }
    
    if framework.lower() in framework_sections:
        return {
            "framework": framework,
            "sections": framework_sections[framework.lower()]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Framework '{framework}' not found"
        )

@router.post("/{report_id}/export")
async def export_report(report_id: str, format: str = "pdf"):
    """Export a report in the specified format"""
    
    supported_formats = ["pdf", "docx", "html"]
    
    if format not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Format not supported. Supported formats: {', '.join(supported_formats)}"
        )
    
    try:
        # In a real implementation, generate the export file
        return {
            "message": f"Report exported successfully in {format.upper()} format",
            "download_url": f"/api/v1/reports/{report_id}/download/{format}",
            "exported_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting report: {str(e)}"
        )
