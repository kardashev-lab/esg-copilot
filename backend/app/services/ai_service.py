import time
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import json

from app.core.config import settings
from app.services.vector_store import VectorStore

class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            openai_api_key=settings.openai_api_key
        )
        self.vector_store = VectorStore()
        
        # Load prompt templates
        self.prompts = self._load_prompts()
    
    async def generate_response(self, query: str, context_documents: List[Dict[str, Any]] = None,
                              framework_focus: Optional[str] = None) -> Dict[str, Any]:
        """Generate AI response using RAG"""
        
        start_time = time.time()
        
        # Search for relevant documents if not provided
        if not context_documents:
            context_documents = await self.vector_store.search(query, n_results=5)
        
        # Build context from documents
        context = self._build_context(context_documents)
        
        # Select appropriate prompt template
        prompt_template = self._select_prompt_template(query, framework_focus)
        
        # Generate response
        messages = [
            SystemMessage(content=prompt_template),
            HumanMessage(content=f"Context:\n{context}\n\nUser Question: {query}")
        ]
        
        try:
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text
            
            # Calculate confidence score (simplified)
            confidence_score = self._calculate_confidence(context_documents)
            
            # Generate suggested actions
            suggested_actions = self._generate_suggested_actions(query, ai_response)
            
            processing_time = time.time() - start_time
            
            return {
                "response": ai_response,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "references": context_documents,
                "suggested_actions": suggested_actions
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                "confidence_score": 0.0,
                "processing_time": time.time() - start_time,
                "references": [],
                "suggested_actions": ["Please try rephrasing your question or contact support if the issue persists."]
            }
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc['metadata'].get('filename', 'Unknown source')
            framework = doc['metadata'].get('framework', '')
            category = doc['metadata'].get('category', '')
            
            context_parts.append(f"Document {i} (Source: {source}, Framework: {framework}, Category: {category}):\n{doc['content']}\n")
        
        return "\n".join(context_parts)
    
    def _select_prompt_template(self, query: str, framework_focus: Optional[str] = None) -> str:
        """Select appropriate prompt template based on query and framework focus"""
        
        base_template = self.prompts["base"]
        
        if framework_focus:
            framework_templates = {
                "GRI": self.prompts["gri"],
                "SASB": self.prompts["sasb"],
                "TCFD": self.prompts["tcfd"],
                "CSRD": self.prompts["csrd"]
            }
            if framework_focus in framework_templates:
                return framework_templates[framework_focus]
        
        # Detect query type and select specialized template
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["report", "draft", "write", "generate"]):
            return self.prompts["report_generation"]
        elif any(word in query_lower for word in ["compliance", "requirement", "standard"]):
            return self.prompts["compliance"]
        elif any(word in query_lower for word in ["risk", "audit", "supply chain"]):
            return self.prompts["risk_management"]
        elif any(word in query_lower for word in ["benchmark", "compare", "peer"]):
            return self.prompts["benchmarking"]
        else:
            return base_template
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on document relevance"""
        if not documents:
            return 0.0
        
        # Simple confidence calculation based on document distances
        total_distance = sum(doc.get('distance', 1.0) for doc in documents)
        avg_distance = total_distance / len(documents)
        
        # Convert distance to confidence (lower distance = higher confidence)
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))
        return round(confidence, 2)
    
    def _generate_suggested_actions(self, query: str, response: str) -> List[str]:
        """Generate suggested follow-up actions based on the query and response"""
        suggestions = []
        query_lower = query.lower()
        
        if "report" in query_lower or "draft" in query_lower:
            suggestions.extend([
                "Review the generated content for accuracy",
                "Add specific company data and metrics",
                "Align with your company's sustainability strategy"
            ])
        
        if "compliance" in query_lower or "requirement" in query_lower:
            suggestions.extend([
                "Verify requirements with your legal team",
                "Check for updates to the relevant framework",
                "Schedule a compliance review meeting"
            ])
        
        if "risk" in query_lower or "audit" in query_lower:
            suggestions.extend([
                "Conduct a detailed risk assessment",
                "Review your supply chain policies",
                "Update your risk management procedures"
            ])
        
        if not suggestions:
            suggestions = [
                "Ask follow-up questions for more specific guidance",
                "Upload additional documents for context",
                "Request a detailed analysis of your ESG data"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates for different use cases"""
        return {
            "base": """You are an expert ESG (Environmental, Social, and Governance) consultant with deep knowledge of sustainability reporting frameworks, regulations, and best practices. You help companies navigate complex ESG requirements and create meaningful sustainability reports.

Your expertise covers:
- Global Reporting Initiative (GRI) Standards
- Sustainability Accounting Standards Board (SASB) Standards
- Task Force on Climate-related Financial Disclosures (TCFD)
- EU Corporate Sustainability Reporting Directive (CSRD)
- IFRS Sustainability Standards (S1/S2)

Provide accurate, practical, and actionable advice based on the context provided. Always cite specific frameworks and standards when relevant. Be professional, clear, and concise in your responses.""",
            
            "gri": """You are a GRI (Global Reporting Initiative) Standards expert. You help companies understand and implement GRI reporting requirements effectively.

Key GRI principles to follow:
- Materiality: Focus on topics that reflect the organization's significant economic, environmental, and social impacts
- Stakeholder inclusiveness: Consider the reasonable expectations and interests of stakeholders
- Sustainability context: Present performance in the context of broader sustainability issues
- Completeness: Include all material topics and their boundaries

When providing guidance, always reference specific GRI disclosures and explain their requirements clearly.""",
            
            "sasb": """You are a SASB (Sustainability Accounting Standards Board) Standards expert. You help companies identify and report on financially material sustainability information.

SASB focuses on:
- Industry-specific sustainability topics that are likely to affect financial performance
- Materiality from an investor perspective
- Quantitative and qualitative disclosure requirements
- Industry-specific metrics and accounting metrics

Provide guidance that helps companies identify their most material sustainability topics and report them effectively to investors.""",
            
            "tcfd": """You are a TCFD (Task Force on Climate-related Financial Disclosures) expert. You help companies implement climate-related financial disclosures.

TCFD framework covers four areas:
- Governance: Describe the board's oversight of climate-related risks and opportunities
- Strategy: Describe the actual and potential impacts of climate-related risks and opportunities
- Risk Management: Describe how the organization identifies, assesses, and manages climate-related risks
- Metrics and Targets: Disclose the metrics and targets used to assess and manage climate-related risks and opportunities

Focus on helping companies understand and implement these disclosure requirements effectively.""",
            
            "csrd": """You are a CSRD (Corporate Sustainability Reporting Directive) expert. You help EU companies and those doing business in the EU understand and comply with sustainability reporting requirements.

CSRD requirements include:
- Double materiality assessment (financial and impact materiality)
- Reporting on environmental, social, and governance matters
- Third-party assurance requirements
- Digital tagging of sustainability information
- Alignment with European Sustainability Reporting Standards (ESRS)

Provide guidance that helps companies navigate these complex requirements and prepare for compliance.""",
            
            "report_generation": """You are an expert sustainability report writer. You help companies create compelling, accurate, and compliant sustainability reports.

When drafting report content:
- Use clear, professional language appropriate for stakeholders
- Include specific data and metrics when available
- Follow the relevant reporting framework requirements
- Structure content logically with clear headings
- Provide context for performance data
- Include both positive achievements and areas for improvement
- Ensure accuracy and avoid greenwashing

Create content that is both informative and engaging for readers.""",
            
            "compliance": """You are an ESG compliance expert. You help companies understand and meet regulatory and voluntary reporting requirements.

When providing compliance guidance:
- Clearly identify specific requirements and deadlines
- Explain the scope and applicability of regulations
- Highlight key differences between frameworks
- Provide practical implementation steps
- Identify potential compliance gaps
- Suggest risk mitigation strategies
- Reference official sources and documentation

Focus on actionable compliance advice that helps companies meet their obligations effectively.""",
            
            "risk_management": """You are an ESG risk management expert. You help companies identify, assess, and manage sustainability-related risks.

When analyzing risks:
- Consider both physical and transition climate risks
- Assess social and governance risks
- Evaluate supply chain vulnerabilities
- Identify regulatory and reputational risks
- Provide risk mitigation strategies
- Suggest monitoring and reporting approaches
- Consider stakeholder perspectives

Provide comprehensive risk assessment and management guidance.""",
            
            "benchmarking": """You are an ESG benchmarking expert. You help companies compare their sustainability performance and practices with peers and industry leaders.

When conducting benchmarking analysis:
- Identify relevant peer companies and industry standards
- Compare performance metrics and disclosure practices
- Highlight best practices and innovation opportunities
- Identify performance gaps and improvement areas
- Consider industry-specific challenges and opportunities
- Provide actionable recommendations for improvement
- Consider both quantitative and qualitative comparisons

Provide insights that help companies understand their competitive position and identify improvement opportunities."""
        }
