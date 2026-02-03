"""
Specialized Clause Analyzers
Detects specific risky clause types
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ClauseAnalysis:
    """Result of analyzing a specific clause type."""
    detected: bool
    clause_type: str
    severity: str  # low, medium, high
    details: Dict
    concerns: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> dict:
        return {
            "detected": self.detected,
            "clause_type": self.clause_type,
            "severity": self.severity,
            "details": self.details,
            "concerns": self.concerns,
            "recommendations": self.recommendations
        }


# ============ Penalty Clause Analyzer ============
def analyze_penalty_clause(text: str) -> ClauseAnalysis:
    """Analyze text for penalty clauses."""
    patterns = [
        r'penalty\s+(?:of|at|@)\s*([\d,]+|[\w\s]+)',
        r'liquidated damages?\s+(?:of|at|@)\s*([\d,]+|[\w\s]+)',
        r'forfeit\s+([\d,]+|[\w\s]+)',
        r'(?:late|delayed?)\s+(?:payment|delivery)\s+(?:fee|charge|penalty)',
        r'interest\s+(?:at|@)\s*(\d+(?:\.\d+)?)\s*%',
    ]
    
    concerns = []
    details = {"penalties_found": [], "interest_rates": []}
    
    content_lower = text.lower()
    for pattern in patterns:
        matches = re.finditer(pattern, content_lower)
        for match in matches:
            details["penalties_found"].append(match.group(0))
    
    # Check for high interest rates
    interest_match = re.search(r'interest\s+(?:at|@)\s*(\d+(?:\.\d+)?)\s*%', content_lower)
    if interest_match:
        rate = float(interest_match.group(1))
        details["interest_rates"].append(rate)
        if rate > 18:
            concerns.append(f"High interest rate of {rate}% may be excessive")
    
    detected = len(details["penalties_found"]) > 0
    
    if detected:
        concerns.append("Penalty clauses should be proportional to actual damages")
        if "liquidated damages" in content_lower:
            concerns.append("Liquidated damages may be unenforceable if not a genuine pre-estimate of loss")
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="penalty",
        severity="medium" if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Ensure penalty amounts are reasonable and proportional",
            "Negotiate caps on maximum penalties",
            "Include grace periods for minor delays"
        ] if detected else []
    )


# ============ Indemnity Clause Analyzer ============
def analyze_indemnity_clause(text: str) -> ClauseAnalysis:
    """Analyze text for indemnification clauses."""
    content_lower = text.lower()
    
    # Indemnity scope patterns
    broad_indemnity_patterns = [
        r'indemnify\s+(?:and\s+)?(?:hold\s+)?harmless\s+(?:from\s+)?(?:any\s+and\s+)?all',
        r'defend,?\s+indemnify,?\s+(?:and\s+)?hold\s+harmless',
        r'any\s+(?:and\s+all\s+)?(?:claims?|losses?|damages?|liabilities?)',
    ]
    
    limited_patterns = [
        r'except\s+(?:for|to\s+the\s+extent)',
        r'arising\s+(?:out\s+of|from)\s+(?:the\s+)?breach',
        r'direct\s+damages?\s+only',
        r'cap(?:ped)?\s+at',
    ]
    
    details = {
        "is_mutual": "mutual" in content_lower or "each party" in content_lower,
        "is_broad": any(re.search(p, content_lower) for p in broad_indemnity_patterns),
        "has_limitations": any(re.search(p, content_lower) for p in limited_patterns),
        "includes_defense_costs": "defend" in content_lower or "attorney" in content_lower,
    }
    
    concerns = []
    severity = "low"
    
    if details["is_broad"]:
        concerns.append("Broad indemnification scope may expose you to unlimited liability")
        severity = "high"
    
    if not details["is_mutual"]:
        concerns.append("One-sided indemnification creates imbalanced risk allocation")
        severity = "high" if severity != "high" else severity
    
    if details["includes_defense_costs"]:
        concerns.append("Defense cost obligation can be expensive regardless of claim validity")
    
    if not details["has_limitations"]:
        concerns.append("No cap or limitation on indemnification amounts")
        severity = "high"
    
    detected = "indemnif" in content_lower or "hold harmless" in content_lower
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="indemnity",
        severity=severity if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Limit indemnification to breaches of contract or negligence",
            "Cap indemnification at contract value or insurance coverage",
            "Require timely notice of claims",
            "Ensure right to participate in defense",
            "Make indemnification mutual"
        ] if detected else []
    )


# ============ Termination Clause Analyzer ============
def analyze_termination_clause(text: str) -> ClauseAnalysis:
    """Analyze text for termination clause terms."""
    content_lower = text.lower()
    
    details = {
        "mutual_termination": any(phrase in content_lower for phrase in 
                                   ["either party may terminate", "mutual termination"]),
        "termination_for_cause": "for cause" in content_lower or "material breach" in content_lower,
        "termination_without_cause": any(phrase in content_lower for phrase in 
                                          ["without cause", "for convenience", "at will"]),
        "notice_period": None,
        "cure_period": None,
        "exit_fee": "exit fee" in content_lower or "termination fee" in content_lower,
    }
    
    # Extract notice period
    notice_match = re.search(r'(\d+)\s*(?:days?|months?)\s*(?:prior\s+)?(?:written\s+)?notice', content_lower)
    if notice_match:
        details["notice_period"] = f"{notice_match.group(1)} {notice_match.group(0).split()[-2]}"
    
    # Extract cure period
    cure_match = re.search(r'cure\s+(?:period\s+)?(?:of\s+)?(\d+)\s*(?:days?)', content_lower)
    if cure_match:
        details["cure_period"] = f"{cure_match.group(1)} days"
    
    concerns = []
    severity = "low"
    
    if details["termination_without_cause"] and not details["mutual_termination"]:
        concerns.append("One-sided termination without cause creates business uncertainty")
        severity = "high"
    
    if not details["notice_period"]:
        concerns.append("No notice period specified for termination")
        severity = "medium"
    
    if not details["cure_period"] and details["termination_for_cause"]:
        concerns.append("No cure period for breaches before termination")
        severity = "medium" if severity != "high" else severity
    
    if details["exit_fee"]:
        concerns.append("Exit fee may be imposed for early termination")
    
    detected = "terminat" in content_lower
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="termination",
        severity=severity if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Ensure mutual termination rights",
            "Request minimum 30-day notice period",
            "Include cure period for termination for cause",
            "Negotiate transition assistance period",
            "Cap or eliminate exit fees"
        ] if detected else []
    )


# ============ Arbitration/Jurisdiction Analyzer ============
def analyze_jurisdiction_clause(text: str) -> ClauseAnalysis:
    """Analyze text for arbitration and jurisdiction terms."""
    content_lower = text.lower()
    
    details = {
        "has_arbitration": any(phrase in content_lower for phrase in 
                               ["arbitration", "arbitrator", "arbitral"]),
        "arbitration_institution": None,
        "jurisdiction": None,
        "governing_law": None,
        "exclusive_jurisdiction": "exclusive jurisdiction" in content_lower,
    }
    
    # Extract arbitration institution
    institutions = ["icc", "siac", "lcia", "adr", "icadr", 
                   "indian council of arbitration", "international chamber of commerce"]
    for inst in institutions:
        if inst in content_lower:
            details["arbitration_institution"] = inst.upper()
            break
    
    # Extract jurisdiction city
    city_match = re.search(r'(?:courts?\s+(?:of|in|at)|jurisdiction\s+(?:of|in|at))\s+([A-Za-z]+)', text)
    if city_match:
        details["jurisdiction"] = city_match.group(1)
    
    # Extract governing law
    law_match = re.search(r'(?:governed\s+by|laws?\s+of)\s+([A-Za-z]+)', text)
    if law_match:
        details["governing_law"] = law_match.group(1)
    
    concerns = []
    severity = "low"
    
    if details["exclusive_jurisdiction"]:
        concerns.append("Exclusive jurisdiction may limit dispute resolution options")
        severity = "medium"
    
    if details["has_arbitration"] and not details["arbitration_institution"]:
        concerns.append("Arbitration rules and institution not specified")
    
    detected = details["has_arbitration"] or "jurisdiction" in content_lower
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="jurisdiction",
        severity=severity if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Specify arbitration institution and rules clearly",
            "Choose convenient jurisdiction location",
            "Consider cost implications of chosen forum",
            "Include language requirements for proceedings"
        ] if detected else []
    )


# ============ Auto-Renewal/Lock-in Analyzer ============
def analyze_renewal_clause(text: str) -> ClauseAnalysis:
    """Analyze text for auto-renewal and lock-in terms."""
    content_lower = text.lower()
    
    details = {
        "has_auto_renewal": any(phrase in content_lower for phrase in 
                                ["auto-renew", "automatically renew", "deemed renewed"]),
        "renewal_period": None,
        "lock_in_period": None,
        "cancellation_notice": None,
        "exit_penalty": "exit fee" in content_lower or "early termination" in content_lower,
    }
    
    # Extract renewal period
    renewal_match = re.search(r'renew(?:ed|al)?\s+(?:for\s+)?(?:a\s+)?(?:further\s+)?(\d+)\s*(year|month|day)s?', content_lower)
    if renewal_match:
        details["renewal_period"] = f"{renewal_match.group(1)} {renewal_match.group(2)}(s)"
    
    # Extract lock-in period
    lockin_match = re.search(r'(?:lock-?in|minimum\s+term)\s+(?:of\s+)?(\d+)\s*(year|month)s?', content_lower)
    if lockin_match:
        details["lock_in_period"] = f"{lockin_match.group(1)} {lockin_match.group(2)}(s)"
    
    # Extract cancellation notice requirement
    cancel_match = re.search(r'(\d+)\s*(?:days?|months?)\s+(?:prior\s+)?(?:to\s+)?(?:expiry|renewal|termination)', content_lower)
    if cancel_match:
        details["cancellation_notice"] = cancel_match.group(0)
    
    concerns = []
    severity = "low"
    
    if details["has_auto_renewal"]:
        concerns.append("Auto-renewal may lock you into unfavorable terms")
        severity = "medium"
        
        if not details["cancellation_notice"]:
            concerns.append("No clear cancellation notice window specified")
            severity = "high"
    
    if details["lock_in_period"]:
        # Check if lock-in is long (>12 months)
        if "year" in (details["lock_in_period"] or ""):
            concerns.append("Long lock-in period limits flexibility")
            severity = "high"
    
    if details["exit_penalty"]:
        concerns.append("Exit penalty may apply for early termination")
    
    detected = details["has_auto_renewal"] or details["lock_in_period"] is not None
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="renewal_lockin",
        severity=severity if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Set calendar reminders before renewal dates",
            "Negotiate shorter lock-in periods",
            "Request opt-out rather than opt-in renewal",
            "Clarify price adjustment terms for renewals"
        ] if detected else []
    )


# ============ Non-Compete/IP Analyzer ============
def analyze_restrictive_covenant(text: str) -> ClauseAnalysis:
    """Analyze text for non-compete and IP clauses."""
    content_lower = text.lower()
    
    details = {
        "has_non_compete": any(phrase in content_lower for phrase in 
                               ["non-compete", "non compete", "shall not compete"]),
        "has_non_solicitation": "non-solicitation" in content_lower or "not solicit" in content_lower,
        "has_ip_assignment": any(phrase in content_lower for phrase in 
                                  ["assigns all", "transfer of ip", "work for hire", 
                                   "intellectual property shall vest"]),
        "restriction_period": None,
        "geographic_scope": None,
    }
    
    # Extract restriction period
    period_match = re.search(r'(?:period\s+of|for)\s+(\d+)\s*(year|month)s?\s+(?:after|following|from)', content_lower)
    if period_match:
        details["restriction_period"] = f"{period_match.group(1)} {period_match.group(2)}(s)"
    
    concerns = []
    severity = "low"
    
    if details["has_non_compete"]:
        concerns.append("Non-compete clause may restrict future business opportunities")
        severity = "high"
        
        if not details["restriction_period"]:
            concerns.append("Non-compete duration not specified")
    
    if details["has_ip_assignment"]:
        concerns.append("IP assignment may transfer valuable business assets")
        severity = "high"
    
    if details["has_non_solicitation"]:
        concerns.append("Non-solicitation may limit talent acquisition")
        severity = "medium"
    
    detected = details["has_non_compete"] or details["has_ip_assignment"]
    
    return ClauseAnalysis(
        detected=detected,
        clause_type="restrictive_covenant",
        severity=severity if detected else "low",
        details=details,
        concerns=concerns,
        recommendations=[
            "Limit non-compete to specific business segments",
            "Define geographic scope clearly and narrowly",
            "Cap restriction period at 12-24 months",
            "Retain ownership of pre-existing IP",
            "Clearly define what constitutes 'work product'"
        ] if detected else []
    )


def run_all_analyzers(text: str) -> Dict[str, ClauseAnalysis]:
    """Run all clause analyzers on the given text."""
    return {
        "penalty": analyze_penalty_clause(text),
        "indemnity": analyze_indemnity_clause(text),
        "termination": analyze_termination_clause(text),
        "jurisdiction": analyze_jurisdiction_clause(text),
        "renewal_lockin": analyze_renewal_clause(text),
        "restrictive_covenant": analyze_restrictive_covenant(text)
    }
