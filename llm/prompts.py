"""
LLM Prompt Templates for Legal Contract Analysis
"""

# System prompt for legal analysis
SYSTEM_PROMPT = """You are an expert legal contract analyst specializing in Indian business law. 
Your role is to help SME owners understand complex contract language in simple terms.

Guidelines:
1. Use plain, simple language that business owners can understand
2. Avoid legal jargon; when you must use legal terms, explain them
3. Be specific about risks and their potential business impact
4. Provide actionable recommendations
5. Be balanced - note both favorable and unfavorable terms
6. Consider Indian law context where relevant

Important: You are providing analysis for educational purposes. Always recommend consulting a qualified lawyer for final decisions."""


# Contract summary prompt
CONTRACT_SUMMARY_PROMPT = """Analyze this {contract_type} contract and provide a comprehensive summary.

CONTRACT TEXT:
{contract_text}

Please provide:

1. **Quick Overview** (2-3 sentences)
   - What is this contract about?
   - Who are the main parties?

2. **Key Terms Summary**
   - Contract duration/term
   - Main obligations of each party
   - Key financial terms

3. **Important Dates & Deadlines**
   - List all significant dates mentioned

4. **Risk Highlights**
   - Top 3-5 concerns for the reader
   - Any unusual or non-standard terms

5. **Bottom Line**
   - One paragraph assessment of whether this contract is fair and balanced

Keep your response clear, organized, and in plain language that a business owner without legal background can understand."""


# Clause explanation prompt
CLAUSE_EXPLANATION_PROMPT = """Explain this contract clause in simple, plain language that a business owner can understand.

CLAUSE TITLE: {clause_title}
CLAUSE TYPE: {clause_type}

CLAUSE TEXT:
{clause_text}

Please provide:

1. **Plain Language Explanation**
   What does this clause actually mean in simple terms?

2. **Your Obligations**
   What are you required to do or not do under this clause?

3. **Key Points to Note**
   - Any deadlines or time limits
   - Any financial implications
   - Any restrictions on you

4. **Risk Assessment**
   Is this clause standard and fair, or does it favor one party?

5. **Recommendation**
   Should you accept this as-is, or try to negotiate changes?

Keep your explanation concise and practical."""


# Risk explanation prompt
RISK_EXPLANATION_PROMPT = """Analyze this risky clause and explain the potential issues.

CLAUSE TITLE: {clause_title}
RISK LEVEL: {risk_level}
RISK FACTORS: {risk_factors}

CLAUSE TEXT:
{clause_text}

Please provide:

1. **What's the Risk?**
   Explain in simple terms what could go wrong with this clause.

2. **Worst Case Scenario**
   What's the worst that could happen if this clause is triggered?

3. **How Common Is This?**
   Is this standard contract language or unusually harsh?

4. **Recommended Changes**
   Suggest specific changes to make this clause more balanced.

5. **Negotiation Tip**
   How should the reader approach negotiating this clause?

Be specific and practical in your recommendations."""


# Alternative suggestion prompt
ALTERNATIVE_SUGGESTION_PROMPT = """Suggest alternative language for this clause that would be more balanced.

ORIGINAL CLAUSE:
{original_clause}

CLAUSE TYPE: {clause_type}
ISSUES IDENTIFIED: {issues}

Please provide:

1. **Suggested Alternative Language**
   Provide specific alternative wording for the clause.

2. **Changes Made**
   Explain what changes you made and why.

3. **Benefits of New Language**
   How does the new language better protect the reader?

4. **Negotiation Approach**
   How should the reader propose these changes?

Make the alternative language professional and reasonable - something the other party might realistically accept."""


# Compliance check prompt
COMPLIANCE_CHECK_PROMPT = """Review this {contract_type} contract for compliance with standard Indian business practices.

CONTRACT TEXT:
{contract_text}

INITIAL COMPLIANCE FINDINGS:
{compliance_findings}

Please assess:

1. **Missing Elements**
   What key provisions seem to be missing from this contract?

2. **Indian Law Considerations**
   Any specific Indian law requirements that may not be met?

3. **Industry Standards**
   Does this contract follow standard practices for its type?

4. **Documentation Requirements**
   What additional steps (stamp duty, registration, etc.) may be needed?

5. **Recommendations**
   Specific steps to ensure the contract is properly enforceable.

Focus on practical compliance requirements for Indian SMEs."""


# Hindi translation prompt
HINDI_TRANSLATION_PROMPT = """Translate this Hindi legal text to English for contract analysis.

HINDI TEXT:
{hindi_text}

Guidelines:
1. Maintain accuracy of legal terminology
2. Preserve all dates, numbers, and amounts exactly
3. Keep party names unchanged
4. Indicate any terms that may have specific legal significance in Indian law
5. Note any ambiguities in the original text

Provide:
1. **English Translation**
   Clear, accurate translation of the text.

2. **Key Terms**
   List any specialized legal terms and their meanings.

3. **Notes**
   Any important context about the translation."""


# Quick analysis prompt
QUICK_ANALYSIS_PROMPT = """Provide a quick analysis of this contract in 100 words or less.

CONTRACT TYPE: {contract_type}
RISK SCORE: {risk_score}/10

KEY ENTITIES:
{entities}

KEY CLAUSES IDENTIFIED:
{clauses}

Provide a brief assessment covering:
1. Overall fairness (1-2 sentences)
2. Main concern (1 sentence)
3. Key recommendation (1 sentence)

Be direct and actionable."""


# Negotiation advice prompt
NEGOTIATION_ADVICE_PROMPT = """Based on the analysis, provide negotiation advice for this contract.

CONTRACT TYPE: {contract_type}
RISK LEVEL: {risk_level}

HIGH-RISK CLAUSES:
{high_risk_clauses}

UNFAVORABLE TERMS:
{unfavorable_terms}

Provide:

1. **Priority Items to Negotiate**
   Rank the top 3-5 items to focus on negotiating.

2. **Suggested Talking Points**
   What to say when raising each concern.

3. **Fallback Positions**
   If they won't agree to your preferred changes, what's acceptable?

4. **Deal Breakers**
   What terms should absolutely not be accepted?

5. **Overall Strategy**
   How to approach this negotiation.

Be practical and realistic in your advice."""


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Get a formatted prompt by type.
    
    Args:
        prompt_type: Type of prompt to get
        **kwargs: Variables to format into the prompt
        
    Returns:
        Formatted prompt string
    """
    prompts = {
        "summary": CONTRACT_SUMMARY_PROMPT,
        "clause_explain": CLAUSE_EXPLANATION_PROMPT,
        "risk_explain": RISK_EXPLANATION_PROMPT,
        "alternative": ALTERNATIVE_SUGGESTION_PROMPT,
        "compliance": COMPLIANCE_CHECK_PROMPT,
        "translate": HINDI_TRANSLATION_PROMPT,
        "quick": QUICK_ANALYSIS_PROMPT,
        "negotiate": NEGOTIATION_ADVICE_PROMPT
    }
    
    if prompt_type not in prompts:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    return prompts[prompt_type].format(**kwargs)


def get_system_prompt() -> str:
    """Get the system prompt for LLM."""
    return SYSTEM_PROMPT
