from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from loguru import logger
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from typing import Dict

class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.google_api_key,
            temperature=0.2
        )
        self.prompt_template = PromptTemplate(
            input_variables=["document_text", "regulation_text"],
            template="""You are a compliance auditor specializing in India's DPDP Act. Analyze the company privacy policy against the provided DPDP Act sections. 
                        Identify specific compliance gaps and provide actionable recommendations. 
                        If fully compliant, state so clearly. Respond in this exact format with bullet points:

                - Compliance Status: True or False
                - Gaps: List specific issues or "None"
                - Suggestions: List actionable steps or "None"

                Document Text:
                {document_text}

                DPDP Act Sections:
                {regulation_text}
                """
        )
        logger.info("LLMService initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=30))
    async def analyze_compliance(self, document_text: str, regulation_text: str) -> Dict[str, any]:
        max_chars = 15000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "..."
            logger.warning("Document text truncated")
        if len(regulation_text) > max_chars:
            sections = regulation_text.split("\n")
            prioritized = [s for s in sections if any(f"Section {i}" in s for i in range(4, 10))]
            regulation_text = "\n".join(prioritized)[:max_chars] + "..."
            logger.warning("Regulation text truncated")

        prompt = self.prompt_template.format(
            document_text=document_text,
            regulation_text=regulation_text
        )
        response = await self.llm.ainvoke(prompt)
        raw_response = response.content.strip()
        logger.debug(f"LLM response: {raw_response}")

        status_match = re.search(r"- Compliance Status: (True|False)", raw_response, re.IGNORECASE)
        gaps_match = re.search(r"- Gaps:([\s\S]*?)(?=- Suggestions:|$)", raw_response, re.IGNORECASE)
        suggestions_match = re.search(r"- Suggestions:([\s\S]*?)$", raw_response, re.IGNORECASE)

        if status_match and gaps_match and suggestions_match:
            status = status_match.group(1).lower() == "true"
            gaps = gaps_match.group(1).strip() or "None"
            suggestions = suggestions_match.group(1).strip() or "None"
        else:
            logger.warning(f"Fallback parsing for response: {raw_response}")
            status = "false" in raw_response.lower()
            gaps = "\n".join(
                line.strip() for line in raw_response.split("\n")
                if "gap" in line.lower() or "issue" in line.lower()
            ) or "Unable to identify gaps"
            suggestions = "\n".join(
                line.strip() for line in raw_response.split("\n")
                if "suggestion" in line.lower() or "recommend" in line.lower()
            ) or "Manual review required"

        if not status and gaps == "None" and suggestions == "None":
            gaps = "Compliance issues detected"
            suggestions = "Review Sections 4–9 manually"

        return {
            "compliance_status": status,
            "gaps": gaps,
            "suggestions": suggestions
        }
        
llm_service= LLMService()