"""
AI-Powered Clause Extractor
Uses LLM to extract and classify clauses from contracts
"""
import os
import sys
import json
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.chain import get_llm_chain


# Prompt for clause extraction
CLAUSE_EXTRACTION_PROMPT = """You are an expert legal contract analyst. Extract all clauses from the following contract.

Definition - "A clause is one building block of a contract, explaining what is allowed, required, restricted, or promised by the parties."
CONTRACT TEXT:
{contract_text}

For each clause, identify:
1. clause_number: The numbering (e.g., "1", "1.1", "2.3.1")
2. clause_title: The title/heading of the clause
3. clause_type: One of: definitions, scope, term, payment, termination, confidentiality, indemnity, warranty, intellectual_property, dispute, force_majeure, notices, general, other
4. clause_content: The full text of the clause (excluding sub-clauses)
5. risk_level: low, medium, or high (based on potential issues for the reader)
6. key_points: 2-3 bullet points summarizing what this clause means

Return the result as a JSON array. Each element should have:
{{
    "clause_number": "1",
    "clause_title": "DEFINITIONS",
    "clause_type": "definitions",
    "clause_content": "The full text...",
    "risk_level": "low",
    "key_points": ["Point 1", "Point 2"],
    "sub_clauses": [
        {{
            "clause_number": "1.1",
            "clause_title": "Agreement",
            "clause_content": "...",
            "risk_level": "low"
        }}
    ]
}}

IMPORTANT: 
- Return ONLY the JSON array, no other text
- Include ALL clauses found in the document
- Properly nest sub-clauses under parent clauses
- If a clause has no title, infer one from the content

JSON Output:"""


def extract_clauses_with_ai(text: str, max_tokens: int = 4000) -> Dict[str, Any]:
    """
    Extract clauses from contract text using AI.
    
    Args:
        text: Contract text
        max_tokens: Maximum tokens for response
        
    Returns:
        Dictionary with extracted clauses and metadata
    """
    # Get LLM chain
    llm = get_llm_chain()
    
    if not llm.is_configured():
        return {
            "success": False,
            "error": "LLM not configured. Please provide OPENAI_API_KEY.",
            "clauses": []
        }
    
    # Truncate text if too long (to fit in context window)
    max_chars = 12000
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
    
    prompt = CLAUSE_EXTRACTION_PROMPT.format(contract_text=text)
    
    try:
        result = llm.query(prompt, max_tokens=max_tokens, temperature=0.1)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "clauses": []
            }
        
        content = result["content"].strip()
        
        # Try to parse JSON
        try:
            # Handle case where LLM wraps in ```json blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            clauses = json.loads(content)
            
            # Convert to standard format
            formatted_clauses = _format_ai_clauses(clauses)
            
            return {
                "success": True,
                "clauses": formatted_clauses,
                "raw_response": result["content"],
                "truncated": truncated,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0)
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse AI response as JSON: {str(e)}",
                "raw_response": result["content"],
                "clauses": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "clauses": []
        }


def _format_ai_clauses(clauses: List[Dict]) -> List[Dict]:
    """Format AI-extracted clauses to standard format."""
    formatted = []
    
    for i, clause in enumerate(clauses):
        formatted_clause = {
            "id": f"clause_{i+1}",
            "title": clause.get("clause_title", f"Clause {i+1}"),
            "content": clause.get("clause_content", ""),
            "level": 1,
            "clause_type": clause.get("clause_type", "other"),
            "clause_number": clause.get("clause_number", str(i+1)),
            "risk_level": clause.get("risk_level", "low"),
            "key_points": clause.get("key_points", []),
            "sub_clauses": []
        }
        
        # Process sub-clauses
        for j, sub_clause in enumerate(clause.get("sub_clauses", [])):
            formatted_sub = {
                "id": f"clause_{i+1}_{j+1}",
                "title": sub_clause.get("clause_title", f"Sub-clause {j+1}"),
                "content": sub_clause.get("clause_content", ""),
                "level": 2,
                "clause_type": sub_clause.get("clause_type", formatted_clause["clause_type"]),
                "clause_number": sub_clause.get("clause_number", f"{i+1}.{j+1}"),
                "risk_level": sub_clause.get("risk_level", "low"),
                "parent_id": formatted_clause["id"]
            }
            formatted_clause["sub_clauses"].append(formatted_sub)
        
        formatted.append(formatted_clause)
    
    return formatted


def get_clause_count(result: Dict) -> int:
    """Get total clause count including sub-clauses."""
    if not result.get("success") or not result.get("clauses"):
        return 0
    
    count = 0
    for clause in result["clauses"]:
        count += 1
        count += len(clause.get("sub_clauses", []))
    
    return count
