"""
LLM Chain Module
Handles communication with OpenAI GPT-4 API
"""
import os
import logging
from typing import Optional, Dict, List, Any
from openai import OpenAI
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LLM_MODEL
from .prompts import get_system_prompt

# Initialize logger
logger = logging.getLogger(__name__)


class LLMChain:
    """
    LLM Chain for legal contract analysis using OpenAI GPT-4.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM chain.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: from config)
        """
        # Priority: explicit api_key > env var
        if api_key:
            self.api_key = api_key
            logger.info("LLM initialized with user-provided API key")
        elif os.getenv("OPENAI_API_KEY"):
            self.api_key = os.getenv("OPENAI_API_KEY")
            logger.info("LLM initialized with environment API key")
        else:
            self.api_key = None
            logger.warning("LLM initialized without API key - not configured")
        
        self.model = model or LLM_MODEL
        self.client = None
        self._initialize_client()
        logger.debug(f"LLM model set to: {self.model}")
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.debug("OpenAI client initialized successfully")
        else:
            self.client = None
            logger.debug("OpenAI client not initialized - no API key")
    
    def is_configured(self) -> bool:
        """Check if the LLM is properly configured."""
        return self.client is not None and self.api_key is not None
    
    def get_mode(self) -> str:
        """Get the current mode (demo or user)."""
        return "demo" if self.is_demo_mode else "user"
    
    def query(self, 
              prompt: str, 
              system_prompt: Optional[str] = None,
              temperature: float = 0.3,
              max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Send a query to the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt (defaults to legal analysis prompt)
            temperature: Creativity parameter (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.is_configured():
            logger.error("LLM query attempted but not configured")
            return {
                "success": False,
                "error": "LLM not configured. Please provide OPENAI_API_KEY.",
                "content": None
            }
        
        if system_prompt is None:
            system_prompt = get_system_prompt()
        
        try:
            prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            logger.info(f"Sending query to {self.model} (max_tokens={max_tokens}, temp={temperature})")
            logger.debug(f"Prompt preview: {prompt_preview}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens
            
            logger.info(f"LLM query successful - {total_tokens} tokens used (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            return {
                "success": True,
                "content": content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"LLM query failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def analyze_contract(self, 
                         contract_text: str, 
                         contract_type: str,
                         analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Perform contract analysis.
        
        Args:
            contract_text: The contract text to analyze
            contract_type: Type of contract
            analysis_type: Type of analysis (summary, detailed, quick)
            
        Returns:
            Analysis result
        """
        from .prompts import get_prompt
        
        # Truncate if too long
        max_chars = 15000
        if len(contract_text) > max_chars:
            contract_text = contract_text[:max_chars] + "\n\n[... text truncated for analysis ...]"
        
        prompt = get_prompt(
            "summary" if analysis_type != "quick" else "quick",
            contract_text=contract_text,
            contract_type=contract_type,
            risk_score="",
            entities="",
            clauses=""
        )
        
        return self.query(prompt, max_tokens=3000)
    
    def explain_clause(self, 
                       clause_title: str,
                       clause_type: str,
                       clause_text: str) -> Dict[str, Any]:
        """
        Explain a contract clause in plain language.
        
        Args:
            clause_title: Title of the clause
            clause_type: Type of clause
            clause_text: The clause text
            
        Returns:
            Explanation result
        """
        from .prompts import get_prompt
        
        prompt = get_prompt(
            "clause_explain",
            clause_title=clause_title,
            clause_type=clause_type,
            clause_text=clause_text
        )
        
        return self.query(prompt, max_tokens=1500)
    
    def explain_risk(self,
                     clause_title: str,
                     clause_text: str,
                     risk_level: str,
                     risk_factors: List[str]) -> Dict[str, Any]:
        """
        Explain the risks of a clause.
        
        Args:
            clause_title: Title of the clause
            clause_text: The clause text
            risk_level: Risk level (low/medium/high)
            risk_factors: List of identified risk factors
            
        Returns:
            Risk explanation result
        """
        from .prompts import get_prompt
        
        prompt = get_prompt(
            "risk_explain",
            clause_title=clause_title,
            clause_text=clause_text,
            risk_level=risk_level,
            risk_factors="\n".join(f"- {rf}" for rf in risk_factors)
        )
        
        return self.query(prompt, max_tokens=1500)
    
    def suggest_alternative(self,
                            original_clause: str,
                            clause_type: str,
                            issues: List[str]) -> Dict[str, Any]:
        """
        Suggest alternative clause language.
        
        Args:
            original_clause: Original clause text
            clause_type: Type of clause
            issues: List of identified issues
            
        Returns:
            Alternative suggestion result
        """
        from .prompts import get_prompt
        
        prompt = get_prompt(
            "alternative",
            original_clause=original_clause,
            clause_type=clause_type,
            issues="\n".join(f"- {issue}" for issue in issues)
        )
        
        return self.query(prompt, max_tokens=1500)
    
    def translate_hindi(self, hindi_text: str) -> Dict[str, Any]:
        """
        Translate Hindi contract text to English.
        
        Args:
            hindi_text: Hindi text to translate
            
        Returns:
            Translation result
        """
        from .prompts import get_prompt
        
        prompt = get_prompt(
            "translate",
            hindi_text=hindi_text
        )
        
        return self.query(prompt, max_tokens=3000)
    
    def get_negotiation_advice(self,
                               contract_type: str,
                               risk_level: str,
                               high_risk_clauses: List[str],
                               unfavorable_terms: List[str]) -> Dict[str, Any]:
        """
        Get negotiation advice for the contract.
        
        Args:
            contract_type: Type of contract
            risk_level: Overall risk level
            high_risk_clauses: List of high-risk clause descriptions
            unfavorable_terms: List of unfavorable terms
            
        Returns:
            Negotiation advice result
        """
        from .prompts import get_prompt
        
        prompt = get_prompt(
            "negotiate",
            contract_type=contract_type,
            risk_level=risk_level,
            high_risk_clauses="\n".join(f"- {c}" for c in high_risk_clauses),
            unfavorable_terms="\n".join(f"- {t}" for t in unfavorable_terms)
        )
        
        return self.query(prompt, max_tokens=2000)


# Global instance
_llm_chain: Optional[LLMChain] = None


def get_llm_chain(api_key: Optional[str] = None, model: Optional[str] = None) -> LLMChain:
    """
    Get or create the global LLM chain instance.
    
    Args:
        api_key: User-provided API key
        model: Model to use (e.g., 'gpt-4o', 'gpt-4')
    """
    global _llm_chain
    
    # Always create new instance if params differ or no instance exists
    if _llm_chain is None or api_key or model:
        _llm_chain = LLMChain(api_key=api_key, model=model)
    
    return _llm_chain
