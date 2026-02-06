"""
Contract Summarizer Module
Generates summaries and explanations using LLM
"""
from typing import Dict, List, Optional, Any
from .chain import get_llm_chain, LLMChain


def generate_contract_summary(
    contract_text: str,
    contract_type: str,
    entities: Dict[str, List],
    clauses: List[Dict],
    risk_score: float,
    llm: Optional[LLMChain] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive contract summary.
    
    Args:
        contract_text: Full contract text
        contract_type: Type of contract
        entities: Extracted entities
        clauses: Extracted clauses
        risk_score: Overall risk score
        llm: Optional LLM chain instance
        
    Returns:
        Summary result dictionary
    """
    if llm is None:
        llm = get_llm_chain()
    
    if not llm.is_configured():
        # Generate a basic summary without LLM
        return _generate_basic_summary(contract_text, contract_type, entities, clauses, risk_score)
    
    # Use LLM for rich summary
    result = llm.analyze_contract(contract_text, contract_type, "summary")
    
    if result["success"]:
        return {
            "success": True,
            "summary": result["content"],
            "tokens_used": result.get("usage", {}).get("total_tokens", 0),
            "generated_by": "llm"
        }
    else:
        # Fall back to basic summary
        basic = _generate_basic_summary(contract_text, contract_type, entities, clauses, risk_score)
        basic["llm_error"] = result.get("error")
        return basic


def _generate_basic_summary(
    contract_text: str,
    contract_type: str,
    entities: Dict[str, List],
    clauses: List[Dict],
    risk_score: float
) -> Dict[str, Any]:
    """Generate a basic summary without LLM."""
    # Extract parties
    parties = []
    for entity in entities.get("PARTY", []):
        if hasattr(entity, 'text'):
            parties.append(entity.text)
        elif isinstance(entity, dict):
            parties.append(entity.get("text", ""))
    
    # Extract dates
    dates = []
    for entity in entities.get("DATE", []):
        if hasattr(entity, 'text'):
            dates.append(entity.text)
        elif isinstance(entity, dict):
            dates.append(entity.get("text", ""))
    
    # Extract amounts
    amounts = []
    for entity in entities.get("MONEY", []):
        if hasattr(entity, 'text'):
            amounts.append(entity.text)
        elif isinstance(entity, dict):
            amounts.append(entity.get("text", ""))
    
    # Build summary
    summary_parts = []
    
    summary_parts.append(f"**Contract Type:** {contract_type}")
    
    if parties:
        summary_parts.append(f"**Parties Involved:** {', '.join(parties[:5])}")
    
    if dates:
        summary_parts.append(f"**Key Dates:** {', '.join(dates[:5])}")
    
    if amounts:
        summary_parts.append(f"**Financial Values:** {', '.join(amounts[:5])}")
    
    summary_parts.append(f"**Number of Clauses:** {len(clauses)}")
    
    # Risk assessment
    if risk_score >= 7:
        risk_text = "⚠️ HIGH RISK - Legal review strongly recommended"
    elif risk_score >= 4:
        risk_text = "⚡ MEDIUM RISK - Some clauses need attention"
    else:
        risk_text = "✅ LOW RISK - Generally balanced terms"
    
    summary_parts.append(f"**Risk Assessment:** {risk_text} (Score: {risk_score}/10)")
    
    return {
        "success": True,
        "summary": "\n\n".join(summary_parts),
        "tokens_used": 0,
        "generated_by": "basic"
    }


def generate_clause_explanations(
    clauses: List[Dict],
    llm: Optional[LLMChain] = None,
    max_clauses: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate plain-language explanations for clauses.
    
    Args:
        clauses: List of clause dictionaries
        llm: Optional LLM chain instance
        max_clauses: Maximum clauses to explain (to manage API costs)
        
    Returns:
        List of clause explanations
    """
    if llm is None:
        llm = get_llm_chain()
    
    explanations = []
    
    for i, clause in enumerate(clauses[:max_clauses]):
        clause_title = clause.get("title", f"Clause {i+1}")
        clause_type = clause.get("clause_type", "general")
        clause_text = clause.get("content", "")
        
        if not clause_text or len(clause_text) < 10:
            continue
        
        if llm.is_configured():
            result = llm.explain_clause(clause_title, clause_type, clause_text[:2000])
            
            if result["success"]:
                explanations.append({
                    "clause_id": clause.get("id", f"clause_{i}"),
                    "clause_title": clause_title,
                    "explanation": result["content"],
                    "generated_by": "llm"
                })
            else:
                explanations.append({
                    "clause_id": clause.get("id", f"clause_{i}"),
                    "clause_title": clause_title,
                    "explanation": _generate_basic_clause_explanation(clause),
                    "generated_by": "basic"
                })
        else:
            explanations.append({
                "clause_id": clause.get("id", f"clause_{i}"),
                "clause_title": clause_title,
                "explanation": _generate_basic_clause_explanation(clause),
                "generated_by": "basic"
            })
    
    return explanations


def _generate_basic_clause_explanation(clause: Dict) -> str:
    """Generate basic clause explanation without LLM."""
    clause_type = clause.get("clause_type", "general")
    content = clause.get("content", "")[:500]
    
    explanations = {
        "definitions": "This section defines key terms used throughout the contract.",
        "term": "This clause specifies the duration and timeline of the agreement.",
        "payment": "This section outlines payment terms, amounts, and schedules.",
        "termination": "This clause describes how and when the contract can be ended.",
        "confidentiality": "This section covers what information must be kept private.",
        "indemnity": "This clause assigns responsibility for potential losses or damages.",
        "warranty": "This section describes guarantees and representations made by parties.",
        "dispute": "This clause outlines how disagreements will be resolved.",
        "force_majeure": "This section covers unforeseeable circumstances that may affect the contract.",
        "intellectual_property": "This clause addresses ownership of ideas, creations, and IP rights.",
        "non_compete": "This section restricts competitive activities during or after the contract.",
        "obligations": "This clause describes what each party must do under the agreement."
    }
    
    base_explanation = explanations.get(clause_type, "This clause is part of the contract terms.")
    
    return f"{base_explanation}\n\n*Original text preview:* {content}..."


def generate_risk_report(
    contract_type: str,
    risk_score: float,
    high_risk_clauses: List[Dict],
    compliance_issues: List[Dict],
    llm: Optional[LLMChain] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive risk report.
    
    Args:
        contract_type: Type of contract
        risk_score: Overall risk score
        high_risk_clauses: List of high-risk clause details
        compliance_issues: List of compliance issues
        llm: Optional LLM chain instance
        
    Returns:
        Risk report dictionary
    """
    report_parts = []
    
    # Header
    if risk_score >= 7:
        risk_level = "HIGH"
        emoji = "🔴"
    elif risk_score >= 4:
        risk_level = "MEDIUM"
        emoji = "🟡"
    else:
        risk_level = "LOW"
        emoji = "🟢"
    
    report_parts.append(f"# Risk Assessment Report\n")
    report_parts.append(f"**Contract Type:** {contract_type}")
    report_parts.append(f"**Overall Risk Level:** {emoji} {risk_level}")
    report_parts.append(f"**Risk Score:** {risk_score:.1f}/10\n")
    
    # High-risk clauses
    if high_risk_clauses:
        report_parts.append("## ⚠️ High-Risk Clauses\n")
        for i, clause in enumerate(high_risk_clauses, 1):
            title = clause.get("clause_title", f"Clause {i}")
            concerns = clause.get("concerns", [])
            report_parts.append(f"### {i}. {title}")
            for concern in concerns[:3]:
                report_parts.append(f"- {concern}")
            report_parts.append("")
    
    # Compliance issues
    if compliance_issues:
        report_parts.append("## 📋 Compliance Considerations\n")
        for issue in compliance_issues[:5]:
            severity = issue.get("severity", "")
            desc = issue.get("description", "")
            icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            report_parts.append(f"- {icon} {desc}")
        report_parts.append("")
    
    # Recommendations
    report_parts.append("## 💡 Recommendations\n")
    report_parts.append("1. Review highlighted clauses carefully before signing")
    report_parts.append("2. Consider negotiating unfavorable terms")
    report_parts.append("3. Consult a lawyer for high-risk items")
    report_parts.append("4. Keep a copy of all contract documents")
    
    return {
        "success": True,
        "report": "\n".join(report_parts),
        "risk_level": risk_level,
        "risk_score": risk_score
    }


def generate_negotiation_points(
    high_risk_clauses: List[Dict],
    unfavorable_terms: List[str],
    llm: Optional[LLMChain] = None
) -> Dict[str, Any]:
    """
    Generate negotiation talking points.
    
    Args:
        high_risk_clauses: List of high-risk clauses
        unfavorable_terms: List of unfavorable terms
        llm: Optional LLM chain instance
        
    Returns:
        Negotiation points dictionary
    """
    points = []
    
    for clause in high_risk_clauses[:5]:
        title = clause.get("clause_title", "Clause")
        recommendations = clause.get("recommendations", [])
        
        point = {
            "clause": title,
            "issue": clause.get("concerns", ["Unfavorable terms"])[0] if clause.get("concerns") else "Needs review",
            "suggestions": recommendations[:3] if recommendations else ["Request modification"]
        }
        points.append(point)
    
    return {
        "success": True,
        "negotiation_points": points,
        "priority_order": [p["clause"] for p in points]
    }


def generate_ai_recommendations(
    contract_type: str,
    risk_score: float,
    high_risk_clauses: List[Dict],
    llm: Optional[LLMChain] = None
) -> List[str]:
    """
    Generate specific, actionable recommendations using LLM.
    
    Args:
        contract_type: Type of contract
        risk_score: Overall risk score
        high_risk_clauses: List of high-risk clauses
        llm: Optional LLM chain instance
        
    Returns:
        List of recommended actions
    """
    if llm is None:
        llm = get_llm_chain()
    
    if not llm.is_configured():
        return []
        
    # Format high risk clauses for prompt
    clauses_text = ""
    if high_risk_clauses:
        for clause in high_risk_clauses[:5]:
            title = clause.get("clause_title", "Clause")
            if isinstance(clause, dict):
                content = clause.get("text_excerpt", "") or clause.get("content", "") or ""
            else:
                content = getattr(clause, "content", "")
            
            # Create a short excerpt
            short_content = str(content)[:200].replace("\n", " ") if content else "Check clause text"
            clauses_text += f"- {title}: {short_content}...\n"
    else:
        clauses_text = "No specific high risk clauses identified. Focus on general best practices."
    
    from .prompts import get_prompt
    import re
    
    try:
        prompt = get_prompt(
            "recommendations",
            contract_type=contract_type,
            risk_score=f"{risk_score:.1f}",
            high_risk_clauses=clauses_text
        )
        
        result = llm.query(prompt, max_tokens=1000)
        
        if result["success"]:
            content = result["content"]
            recommendations = []
            for line in content.split('\n'):
                line = line.strip()
                # Check for list markers
                if line and (line.startswith('-') or line.startswith('*') or (line[0].isdigit() and line[1:3] in ['. ', ') '])):
                     # Remove marker
                     clean = re.sub(r'^[\d\-\*\.]+\s*', '', line).strip()
                     if clean:
                         recommendations.append(clean)
            return recommendations
            
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        
    return []


def generate_ai_top_concerns(
    contract_type: str,
    risk_score: float,
    high_risk_clauses: List[Dict],
    llm: Optional[LLMChain] = None
) -> List[str]:
    """
    Generate top concerns using LLM.
    
    Args:
        contract_type: Type of contract
        risk_score: Overall risk score
        high_risk_clauses: List of high-risk clauses
        llm: Optional LLM chain instance
        
    Returns:
        List of top concerns
    """
    if llm is None:
        llm = get_llm_chain()
    
    if not llm.is_configured():
        return []
        
    # Format high risk clauses for prompt
    clauses_text = ""
    if high_risk_clauses:
        for clause in high_risk_clauses[:5]:
            title = clause.get("clause_title", "Clause")
            if isinstance(clause, dict):
                content = clause.get("text_excerpt", "") or clause.get("content", "") or ""
            else:
                content = getattr(clause, "content", "")
            
            # Create a short excerpt
            short_content = str(content)[:200].replace("\n", " ") if content else "Check clause text"
            clauses_text += f"- {title}: {short_content}...\n"
    else:
        clauses_text = "No specific high risk clauses identified. Focus on general best practices."
    
    from .prompts import get_prompt
    import re
    
    try:
        prompt = get_prompt(
            "top_concerns",
            contract_type=contract_type,
            risk_score=f"{risk_score:.1f}",
            high_risk_clauses=clauses_text
        )
        
        result = llm.query(prompt, max_tokens=1000)
        
        if result["success"]:
            content = result["content"]
            concerns = []
            for line in content.split('\n'):
                line = line.strip()
                # Check for list markers
                if line and (line.startswith('-') or line.startswith('*') or (line[0].isdigit() and line[1:3] in ['. ', ') '])):
                     # Remove marker
                     clean = re.sub(r'^[\d\-\*\.]+\s*', '', line).strip()
                     if clean:
                         concerns.append(clean)
            return concerns
            
    except Exception as e:
        print(f"Error generating top concerns: {e}")
        
    return []


def extract_entities_with_ai(contract_text: str, llm: Optional[LLMChain] = None) -> Dict[str, List]:
    """
    Extract key entities using LLM (to improve precision over regex).
    
    Args:
        contract_text: The contract text
        llm: Optional LLM chain instance
        
    Returns:
        Dictionary of entities
    """
    if llm is None:
        llm = get_llm_chain()
    
    if not llm.is_configured():
        return {}
        
    from .prompts import get_prompt
    import json
    
    try:
        # Truncate text if needed
        text_preview = contract_text[:10000]
        
        prompt = get_prompt(
            "entity_extraction",
            contract_text=text_preview
        )
        
        result = llm.query(prompt, max_tokens=1000)
        
        if result["success"]:
            # Clean content if it contains markdown code blocks
            content = result["content"].replace("```json", "").replace("```", "").strip()
            
            # Try to extract JSON if it's wrapped in other text
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)
            
            try:
                data = json.loads(content)
                # Map keys to app expectations
                mapped = {
                    "PARTY": data.get("parties", []),
                    "JURISDICTION": data.get("jurisdiction", []),
                    "DATE": [data.get("effective_date")] if data.get("effective_date") else [],
                    "MONEY": data.get("financial_values", []),
                    "DURATION": [data.get("duration")] if data.get("duration") else []
                }
                
                # Filter out nulls/empties
                final = {}
                for k, v in mapped.items():
                    final[k] = [x for x in v if x and str(x).lower() != "null" and str(x).lower() != "none"]
                
                return final
                
            except json.JSONDecodeError as e:
                print(f"Failed to decode AI entity extraction JSON: {e}")
                
    except Exception as e:
        print(f"Error AI entity extraction: {e}")
        
    return {}
