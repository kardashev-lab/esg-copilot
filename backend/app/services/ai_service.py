import time
import json
import re
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

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
            if framework_focus:
                # Handle multiple frameworks
                frameworks = [fw.strip() for fw in framework_focus.split(',') if fw.strip()]
                
                # Search within selected frameworks
                all_context_docs = []
                for framework in frameworks:
                    try:
                        framework_docs = await self.vector_store.search_by_framework(query, framework, n_results=3)
                        all_context_docs.extend(framework_docs)
                    except Exception as e:
                        # If framework-specific search fails, fall back to general search
                        general_docs = await self.vector_store.search(query, n_results=2)
                        all_context_docs.extend(general_docs)
                
                # Sort by relevance and take top results
                all_context_docs.sort(key=lambda x: x.get('distance', 1.0))
                context_documents = all_context_docs[:5]
            else:
                context_documents = await self.vector_store.search(query, n_results=5)
        
        # Build context from documents
        context = self._build_context(context_documents)
        
        # Select appropriate prompt template
        prompt_template = self._select_prompt_template(query, framework_focus)
        
        # Generate response
        messages = [
            SystemMessage(content=prompt_template),
            HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
        ]
        
        try:
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text.strip()
            
            # Remove any trailing "O" or "0" that might be added by the LLM
            ai_response = re.sub(r'[O0]\s*$', '', ai_response).strip()
            
            # Calculate confidence score (simplified)
            confidence_score = self._calculate_confidence(context_documents)
            
            # Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(query, ai_response)
            
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
    
    async def generate_framework_suggestions(self, prompt: str) -> str:
        """Generate framework suggestions using LLM"""
        
        try:
            messages = [
                SystemMessage(content="ESG framework selector. Return only a JSON array of framework IDs from: gri, sasb, tcfd, csrd, esrs, ifrs-s1, ifrs-s2, uk-tcfd, uk-sdr, canada-tcfd, canada-esg, australia-climate, australia-esg, japan-tcfd, japan-esg, sec-climate, california-sb253, sfdr, cdp. Example: [\"gri\", \"tcfd\"]"),
                HumanMessage(content=f"Query: {prompt}")
            ]
            
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            # Fallback to simple keyword matching
            return self._fallback_framework_suggestion(prompt)
    
    def _fallback_framework_suggestion(self, prompt: str) -> str:
        """Fallback framework suggestion using keyword matching"""
        prompt_lower = prompt.lower()
        suggestions = []
        
        # Keyword-based framework selection
        if any(word in prompt_lower for word in ["eu", "european", "europe"]):
            suggestions.extend(["csrd", "esrs", "sfdr"])
        
        if any(word in prompt_lower for word in ["us", "united states", "america", "american"]):
            suggestions.extend(["sasb", "sec-climate", "california-sb253"])
        
        if any(word in prompt_lower for word in ["uk", "united kingdom", "british"]):
            suggestions.extend(["uk-tcfd", "uk-sdr"])
        
        if any(word in prompt_lower for word in ["canada", "canadian"]):
            suggestions.extend(["canada-tcfd", "canada-esg"])
        
        if any(word in prompt_lower for word in ["australia", "australian"]):
            suggestions.extend(["australia-climate", "australia-esg"])
        
        if any(word in prompt_lower for word in ["japan", "japanese"]):
            suggestions.extend(["japan-tcfd", "japan-esg"])
        
        # Framework-specific keywords
        if any(word in prompt_lower for word in ["gri", "global reporting"]):
            suggestions.append("gri")
        
        if any(word in prompt_lower for word in ["sasb", "sustainability accounting"]):
            suggestions.append("sasb")
        
        if any(word in prompt_lower for word in ["tcfd", "climate-related", "climate risk"]):
            suggestions.append("tcfd")
        
        if any(word in prompt_lower for word in ["csrd", "corporate sustainability reporting"]):
            suggestions.append("csrd")
        
        if any(word in prompt_lower for word in ["ifrs", "international financial reporting"]):
            suggestions.extend(["ifrs-s1", "ifrs-s2"])
        
        # If no specific frameworks mentioned, suggest global ones for general ESG queries
        if not suggestions and any(word in prompt_lower for word in ["esg", "sustainability", "environmental", "social", "governance"]):
            suggestions.extend(["gri", "tcfd"])
        
        return json.dumps(list(set(suggestions)))  # Remove duplicates
    
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
            # Handle multiple frameworks (comma-separated)
            frameworks = [fw.strip().upper() for fw in framework_focus.split(',') if fw.strip()]
            
            framework_templates = {
                "GRI": self.prompts["gri"],
                "SASB": self.prompts["sasb"],
                "TCFD": self.prompts["tcfd"],
                "CSRD": self.prompts["csrd"],
                "ESRS": self.prompts["csrd"],  # ESRS is part of CSRD
                "IFRS-S1": self.prompts["ifrs"],
                "IFRS-S2": self.prompts["ifrs"],
                "UK-TCFD": self.prompts["tcfd"],
                "CANADA-TCFD": self.prompts["tcfd"],
                "AUSTRALIA-CLIMATE": self.prompts["tcfd"],
                "JAPAN-TCFD": self.prompts["tcfd"],
                "SEC-CLIMATE": self.prompts["sasb"],  # SEC climate rule aligns with SASB
                "CALIFORNIA-SB253": self.prompts["sasb"],
                "SFDR": self.prompts["csrd"],  # SFDR is EU regulation
                "UK-SDR": self.prompts["tcfd"],
                "CANADA-ESG": self.prompts["gri"],
                "AUSTRALIA-ESG": self.prompts["gri"],
                "JAPAN-ESG": self.prompts["gri"],
                "CDP": self.prompts["tcfd"],
            }
            
            # If multiple frameworks are selected, use a combined approach
            if len(frameworks) > 1:
                selected_templates = []
                for fw in frameworks:
                    if fw in framework_templates:
                        selected_templates.append(framework_templates[fw])
                
                if selected_templates:
                    # Combine templates for multi-framework queries
                    combined_template = f"""You are an expert ESG consultant with expertise in multiple frameworks: {', '.join(frameworks)}.

{base_template}

When providing guidance, consider the requirements and best practices from all relevant frameworks: {', '.join(frameworks)}.

"""
                    return combined_template
            
            # Single framework or no matching frameworks
            for fw in frameworks:
                if fw in framework_templates:
                    return framework_templates[fw]
        
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
    
    async def _generate_suggested_actions(self, query: str, response: str) -> List[str]:
        """Generate suggested follow-up actions using LLM"""
        try:
            action_prompt = f"Query: {query}\nResponse: {response[:300]}...\nSuggest 3 actionable next steps. Return only JSON array: [\"action1\", \"action2\", \"action3\"]"

            messages = [
                SystemMessage(content="ESG action suggester. Return only JSON array of 3 actionable steps. Example: [\"Review GRI standards\", \"Conduct materiality assessment\", \"Engage stakeholders\"]"),
                HumanMessage(content=action_prompt)
            ]
            
            ai_result = await self.llm.agenerate([messages])
            action_text = ai_result.generations[0][0].text.strip()
            
            # Parse JSON response
            try:
                import json
                actions = json.loads(action_text)
                if isinstance(actions, list):
                    return actions[:3]  # Limit to 3 suggestions
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Fallback to keyword-based suggestions
            return self._fallback_suggested_actions(query, response)
            
        except Exception as e:
            # Fallback to keyword-based suggestions
            return self._fallback_suggested_actions(query, response)
    
    def _fallback_suggested_actions(self, query: str, response: str) -> List[str]:
        """Fallback suggested actions based on keywords"""
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
            "base": """ESG consultant expert. Provide accurate, practical advice on sustainability reporting frameworks (GRI, SASB, TCFD, CSRD, IFRS). Cite specific standards when relevant. Be professional and concise.""",
            
            "gri": """GRI Standards expert. Focus on materiality, stakeholder inclusiveness, sustainability context, and completeness. Reference specific GRI disclosures clearly.""",
            
            "sasb": """SASB Standards expert. Focus on industry-specific, financially material sustainability topics. Emphasize investor perspective and quantitative metrics.""",
            
            "tcfd": """TCFD expert. Cover governance, strategy, risk management, and metrics/targets for climate-related financial disclosures.""",
            
            "csrd": """CSRD expert. Cover double materiality, ESG reporting, third-party assurance, digital tagging, and ESRS alignment for EU compliance.""",
            
            "ifrs": """IFRS Sustainability Standards expert. Cover S1 (general requirements) and S2 (climate disclosures) including governance, strategy, risk management, metrics, targets, and GHG emissions.""",
            
            "report_generation": """Sustainability report writer. Use clear, professional language with specific data and metrics. Follow framework requirements, structure logically, provide context, and avoid greenwashing.""",
            
            "compliance": """ESG compliance expert. Identify requirements, deadlines, scope, framework differences, implementation steps, compliance gaps, and risk mitigation strategies.""",
            
            "risk_management": """ESG risk management expert. Consider physical/transition climate risks, social/governance risks, supply chain vulnerabilities, regulatory/reputational risks, and provide mitigation strategies.""",
            
            "benchmarking": """ESG benchmarking expert. Compare performance metrics, disclosure practices, best practices, performance gaps, industry challenges, and provide actionable recommendations."""
        }
