from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging
from datetime import datetime

from app.models.compliance import (
    ComplianceCheckRequest, 
    ComplianceReport, 
    ComplianceGap,
    FrameworkRequirement
)
from app.services.vector_store import VectorStore
from app.services.ai_service import AIService

router = APIRouter()
vector_store = VectorStore()
ai_service = AIService()
logger = logging.getLogger(__name__)

@router.post("/check", response_model=ComplianceReport)
async def check_compliance(request: ComplianceCheckRequest):
    """Check compliance with a specific ESG framework"""
    
    try:
        logger.info(f"Starting compliance check for framework: {request.framework}")
        
        # Get company documents for analysis
        company_context = []
        for doc_id in request.company_documents:
            try:
                chunks = await vector_store.get_document_chunks(doc_id)
                company_context.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to retrieve document {doc_id}: {e}")
        
        # Get framework requirements
        framework_requirements = await get_framework_requirements(request.framework)
        
        # Analyze compliance gaps using AI
        gaps = await analyze_compliance_gaps(
            company_context, 
            framework_requirements, 
            request.framework
        )
        
        # Calculate overall compliance score
        total_requirements = len(framework_requirements)
        compliant_requirements = total_requirements - len(gaps)
        compliance_score = (compliant_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        # Generate recommendations
        recommendations = generate_recommendations(gaps, request.framework)
        
        report = ComplianceReport(
            framework=request.framework,
            company_documents=request.company_documents,
            compliance_score=round(compliance_score, 2),
            total_requirements=total_requirements,
            compliant_requirements=compliant_requirements,
            gaps=gaps,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"Compliance check completed. Score: {compliance_score}%")
        return report
        
    except Exception as e:
        logger.error(f"Error checking compliance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking compliance: {str(e)}"
        )

async def analyze_compliance_gaps(
    company_context: List[dict], 
    framework_requirements: List[FrameworkRequirement], 
    framework: str
) -> List[ComplianceGap]:
    """Analyze compliance gaps using AI"""
    
    gaps = []
    
    for requirement in framework_requirements:
        try:
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze if the company's documents address the following {framework} requirement:
            
            Requirement: {requirement.title}
            Description: {requirement.description}
            
            Company Context:
            {company_context[:5]}  # Limit context for analysis
            
            Determine if this requirement is:
            1. Fully addressed (COMPLIANT)
            2. Partially addressed (MEDIUM gap)
            3. Not addressed (HIGH gap)
            
            Provide a brief explanation and recommendation.
            """
            
            # Use AI to analyze compliance
            ai_result = await ai_service.generate_response(
                query=analysis_prompt,
                context_documents=company_context[:3]  # Limit context
            )
            
            # Parse AI response to determine gap severity
            response_text = ai_result["response"].lower()
            
            if "not addressed" in response_text or "missing" in response_text:
                severity = "high"
            elif "partially" in response_text or "incomplete" in response_text:
                severity = "medium"
            else:
                severity = "low"
            
            # Only add as gap if not compliant
            if severity in ["high", "medium"]:
                gap = ComplianceGap(
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    severity=severity,
                    description=f"AI analysis indicates {severity} compliance gap",
                    recommendation=ai_result["response"],
                    status="open"
                )
                gaps.append(gap)
                
        except Exception as e:
            logger.warning(f"Failed to analyze requirement {requirement.id}: {e}")
            # Add as high severity gap if analysis fails
            gap = ComplianceGap(
                requirement_id=requirement.id,
                requirement_title=requirement.title,
                severity="high",
                description="Unable to analyze compliance due to technical error",
                recommendation="Review requirement manually and ensure proper documentation",
                status="open"
            )
            gaps.append(gap)
    
    return gaps

def generate_recommendations(gaps: List[ComplianceGap], framework: str) -> List[str]:
    """Generate recommendations based on compliance gaps"""
    
    recommendations = []
    
    high_gaps = [gap for gap in gaps if gap.severity == "high"]
    medium_gaps = [gap for gap in gaps if gap.severity == "medium"]
    
    if high_gaps:
        recommendations.append(f"Address {len(high_gaps)} high-priority compliance gaps immediately")
    
    if medium_gaps:
        recommendations.append(f"Review and improve {len(medium_gaps)} areas with partial compliance")
    
    if framework.upper() == "GRI":
        recommendations.extend([
            "Conduct a comprehensive materiality assessment",
            "Ensure stakeholder engagement processes are documented",
            "Establish clear governance structures for sustainability reporting"
        ])
    elif framework.upper() == "TCFD":
        recommendations.extend([
            "Develop climate scenario analysis",
            "Establish climate risk governance framework",
            "Implement climate-related metrics and targets"
        ])
    elif framework.upper() == "CSRD":
        recommendations.extend([
            "Conduct double materiality assessment",
            "Prepare for ESRS compliance requirements",
            "Establish assurance processes for sustainability reporting"
        ])
    
    if not recommendations:
        recommendations.append("Continue monitoring compliance and stay updated with framework changes")
    
    return recommendations

@router.get("/frameworks/{framework}/requirements")
async def get_framework_requirements(framework: str):
    """Get requirements for a specific framework"""
    
    try:
        # Search for framework requirements in vector store
        results = await vector_store.search(framework, n_results=20)
        
        requirements = []
        for i, result in enumerate(results):
            requirement = FrameworkRequirement(
                id=f"{framework.lower()}_{i+1}",
                title=f"{framework.upper()} Requirement {i+1}",
                description=result.get('content', '')[:200] + "...",
                category=result.get('metadata', {}).get('category', 'General'),
                mandatory=True
            )
            requirements.append(requirement)
        
        if not requirements:
            # Return basic framework structure if no specific requirements found
            requirements = get_basic_framework_requirements(framework)
        
        return {
            "framework": framework,
            "requirements": requirements,
            "total_count": len(requirements)
        }
        
    except Exception as e:
        logger.error(f"Error getting framework requirements: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting framework requirements: {str(e)}"
        )

def get_basic_framework_requirements(framework: str) -> List[FrameworkRequirement]:
    """Get basic framework requirements when detailed ones are not available"""
    
    basic_requirements = {
        "GRI": [
            FrameworkRequirement(
                id="gri_1",
                title="Organizational Profile",
                description="Report organizational details, activities, and governance structure",
                category="General",
                mandatory=True
            ),
            FrameworkRequirement(
                id="gri_2",
                title="Material Topics",
                description="Identify and report on material sustainability topics",
                category="Materiality",
                mandatory=True
            ),
            FrameworkRequirement(
                id="gri_3",
                title="Stakeholder Engagement",
                description="Describe stakeholder engagement processes and outcomes",
                category="Stakeholders",
                mandatory=True
            )
        ],
        "TCFD": [
            FrameworkRequirement(
                id="tcfd_1",
                title="Governance",
                description="Describe board oversight of climate-related risks and opportunities",
                category="Governance",
                mandatory=True
            ),
            FrameworkRequirement(
                id="tcfd_2",
                title="Strategy",
                description="Describe climate-related risks and opportunities and their impact",
                category="Strategy",
                mandatory=True
            ),
            FrameworkRequirement(
                id="tcfd_3",
                title="Risk Management",
                description="Describe processes for identifying and managing climate-related risks",
                category="Risk Management",
                mandatory=True
            ),
            FrameworkRequirement(
                id="tcfd_4",
                title="Metrics and Targets",
                description="Disclose metrics and targets used to assess climate-related risks",
                category="Metrics",
                mandatory=True
            )
        ],
        "CSRD": [
            FrameworkRequirement(
                id="csrd_1",
                title="Double Materiality Assessment",
                description="Conduct assessment covering both financial and impact materiality",
                category="Materiality",
                mandatory=True
            ),
            FrameworkRequirement(
                id="csrd_2",
                title="ESRS Compliance",
                description="Comply with European Sustainability Reporting Standards",
                category="Standards",
                mandatory=True
            ),
            FrameworkRequirement(
                id="csrd_3",
                title="Assurance",
                description="Obtain third-party assurance on sustainability reporting",
                category="Assurance",
                mandatory=True
            )
        ]
    }
    
    return basic_requirements.get(framework.upper(), [
        FrameworkRequirement(
            id=f"{framework.lower()}_1",
            title=f"{framework.upper()} Requirements",
            description=f"Comply with {framework.upper()} framework requirements",
            category="General",
            mandatory=True
        )
    ])

@router.get("/benchmark")
async def benchmark_compliance(
    framework: str,
    company_documents: List[str],
    peer_companies: List[str]
):
    """Benchmark compliance against peer companies"""
    
    try:
        logger.info(f"Starting compliance benchmarking for {framework}")
        
        # Get company documents
        company_context = []
        for doc_id in company_documents:
            try:
                chunks = await vector_store.get_document_chunks(doc_id)
                company_context.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to retrieve company document {doc_id}: {e}")
        
        # TODO: Implement actual peer company data retrieval
        # For now, return placeholder benchmarking structure
        logger.warning("Peer company benchmarking not yet implemented")
        
        return {
            "framework": framework,
            "company_score": 0.0,
            "peer_average": 0.0,
            "industry_average": 0.0,
            "top_performers": [],
            "benchmarking_insights": [
                "Peer benchmarking requires additional peer company data",
                "Consider uploading peer company sustainability reports",
                "Industry benchmarking data will be available in future updates"
            ],
            "recommendations": [
                "Upload peer company documents for comparison",
                "Focus on improving internal compliance first",
                "Consider industry-specific ESG benchmarks"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error benchmarking compliance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error benchmarking compliance: {str(e)}"
        )

@router.get("/timeline")
async def get_compliance_timeline(framework: str):
    """Get compliance timeline and deadlines for a framework"""
    
    try:
        # TODO: Implement dynamic timeline based on current date and framework requirements
        logger.info(f"Getting compliance timeline for {framework}")
        
        return {
            "framework": framework,
            "current_phase": "assessment",
            "next_deadline": "2024-12-31",
            "timeline": [
                {
                    "phase": "assessment",
                    "description": "Conduct materiality assessment and gap analysis",
                    "deadline": "2024-06-30",
                    "status": "in_progress"
                },
                {
                    "phase": "implementation",
                    "description": "Implement compliance measures and data collection",
                    "deadline": "2024-09-30",
                    "status": "pending"
                },
                {
                    "phase": "reporting",
                    "description": "Prepare and publish sustainability report",
                    "deadline": "2024-12-31",
                    "status": "pending"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting compliance timeline: {str(e)}"
        )
