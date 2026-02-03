"""
Risk Scoring Module
Calculates clause-level and contract-level risk scores
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskFactor:
    """Represents a risk factor found in a clause."""
    name: str
    category: str
    severity: int  # 1-10
    description: str
    recommendation: str
    text_excerpt: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation,
            "text_excerpt": self.text_excerpt
        }


@dataclass
class ClauseRisk:
    """Risk assessment for a single clause."""
    clause_id: str
    clause_title: str
    clause_type: str
    risk_level: RiskLevel
    risk_score: float  # 0-10
    risk_factors: List[RiskFactor] = field(default_factory=list)
    is_favorable: bool = True
    alternatives: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "clause_id": self.clause_id,
            "clause_title": self.clause_title,
            "clause_type": self.clause_type,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "risk_factors": [rf.to_dict() for rf in self.risk_factors],
            "is_favorable": self.is_favorable,
            "alternatives": self.alternatives
        }


@dataclass
class ContractRisk:
    """Overall contract risk assessment."""
    overall_score: float  # 0-10
    risk_level: RiskLevel
    clause_risks: List[ClauseRisk] = field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    summary: str = ""
    top_concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "risk_level": self.risk_level.value,
            "clause_risks": [cr.to_dict() for cr in self.clause_risks],
            "high_risk_count": self.high_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "low_risk_count": self.low_risk_count,
            "summary": self.summary,
            "top_concerns": self.top_concerns,
            "recommendations": self.recommendations
        }


# Risk weights for different clause types
CLAUSE_RISK_WEIGHTS = {
    "indemnity": 2.0,
    "liability_limitation": 1.8,
    "termination": 1.5,
    "non_compete": 1.5,
    "intellectual_property": 1.5,
    "confidentiality": 1.3,
    "payment": 1.2,
    "warranty": 1.2,
    "dispute": 1.2,
    "force_majeure": 1.0,
    "definitions": 0.5,
    "notices": 0.5,
    "amendment": 0.5,
    "severability": 0.3
}


def score_to_level(score: float) -> RiskLevel:
    """Convert numeric score to risk level."""
    if score >= 7:
        return RiskLevel.HIGH
    elif score >= 4:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def calculate_clause_risk(clause_id: str, 
                          clause_title: str,
                          clause_content: str,
                          clause_type: Optional[str] = None) -> ClauseRisk:
    """
    Calculate risk score for a single clause.
    
    Args:
        clause_id: Unique clause identifier
        clause_title: Title of the clause
        clause_content: Content of the clause
        clause_type: Type of clause (if identified)
        
    Returns:
        ClauseRisk assessment
    """
    risk_factors = []
    base_score = 0.0
    
    content_lower = clause_content.lower()
    
    # Analyze for risky patterns
    risk_patterns = _get_risk_patterns()
    
    for pattern_name, pattern_info in risk_patterns.items():
        if any(keyword in content_lower for keyword in pattern_info["keywords"]):
            risk_factors.append(RiskFactor(
                name=pattern_name,
                category=pattern_info["category"],
                severity=pattern_info["severity"],
                description=pattern_info["description"],
                recommendation=pattern_info["recommendation"],
                text_excerpt=""
            ))
            base_score += pattern_info["severity"] * pattern_info.get("weight", 1.0)
    
    # Apply clause type weight
    if clause_type and clause_type in CLAUSE_RISK_WEIGHTS:
        base_score *= CLAUSE_RISK_WEIGHTS[clause_type]
    
    # Normalize score to 0-10 range
    final_score = min(10, base_score / 3)
    
    # Determine if clause is favorable
    is_favorable = final_score < 5
    
    # Get alternatives for high-risk clauses
    alternatives = []
    if not is_favorable and clause_type:
        alternatives = _get_alternative_suggestions(clause_type, risk_factors)
    
    return ClauseRisk(
        clause_id=clause_id,
        clause_title=clause_title,
        clause_type=clause_type or "unknown",
        risk_level=score_to_level(final_score),
        risk_score=round(final_score, 2),
        risk_factors=risk_factors,
        is_favorable=is_favorable,
        alternatives=alternatives
    )


def calculate_contract_risk(clause_risks: List[ClauseRisk]) -> ContractRisk:
    """
    Calculate overall contract risk from clause risks.
    
    Args:
        clause_risks: List of individual clause risk assessments
        
    Returns:
        ContractRisk overall assessment
    """
    if not clause_risks:
        return ContractRisk(
            overall_score=0,
            risk_level=RiskLevel.LOW,
            summary="No clauses analyzed"
        )
    
    # Count risk levels
    high_count = sum(1 for cr in clause_risks if cr.risk_level == RiskLevel.HIGH)
    medium_count = sum(1 for cr in clause_risks if cr.risk_level == RiskLevel.MEDIUM)
    low_count = sum(1 for cr in clause_risks if cr.risk_level == RiskLevel.LOW)
    
    # Calculate weighted average score
    total_score = sum(cr.risk_score for cr in clause_risks)
    weighted_score = total_score / len(clause_risks)
    
    # Boost score if many high-risk clauses
    if high_count > 2:
        weighted_score = min(10, weighted_score * 1.3)
    
    # Generate summary
    summary = _generate_risk_summary(clause_risks, weighted_score)
    
    # Get top concerns
    top_concerns = _get_top_concerns(clause_risks)
    
    # Get recommendations
    recommendations = _get_contract_recommendations(clause_risks)
    
    return ContractRisk(
        overall_score=round(weighted_score, 2),
        risk_level=score_to_level(weighted_score),
        clause_risks=clause_risks,
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        summary=summary,
        top_concerns=top_concerns,
        recommendations=recommendations
    )


def _get_risk_patterns() -> Dict[str, dict]:
    """Get patterns that indicate risk."""
    return {
        "unlimited_liability": {
            "keywords": ["unlimited liability", "all damages", "any and all losses", "full liability"],
            "category": "liability",
            "severity": 9,
            "weight": 1.5,
            "description": "Clause imposes unlimited liability which could expose you to significant financial risk",
            "recommendation": "Negotiate a liability cap based on contract value or annual fees"
        },
        "broad_indemnification": {
            "keywords": ["indemnify and hold harmless", "any and all claims", "defend at own cost", 
                        "full indemnification", "gross negligence", "willful misconduct excepted"],
            "category": "indemnity",
            "severity": 8,
            "weight": 1.5,
            "description": "Broad indemnification clause may require you to cover losses beyond your control",
            "recommendation": "Limit indemnification to direct damages caused by your breach"
        },
        "unilateral_termination": {
            "keywords": ["terminate at will", "terminate without cause", "sole discretion", 
                        "immediate termination", "without notice"],
            "category": "termination",
            "severity": 7,
            "weight": 1.3,
            "description": "One-sided termination rights create business continuity risk",
            "recommendation": "Request mutual termination rights with reasonable notice period"
        },
        "auto_renewal": {
            "keywords": ["automatically renew", "auto-renewal", "deemed renewed", 
                        "unless terminated prior", "tacit renewal"],
            "category": "term",
            "severity": 5,
            "weight": 1.0,
            "description": "Auto-renewal may lock you into unfavorable terms",
            "recommendation": "Add calendar reminders for renewal dates and negotiate opt-out clause"
        },
        "long_lock_in": {
            "keywords": ["lock-in period", "minimum term", "cannot terminate before", 
                        "exit fee", "early termination fee", "liquidated damages"],
            "category": "term",
            "severity": 6,
            "weight": 1.2,
            "description": "Lock-in period limits flexibility and may incur exit costs",
            "recommendation": "Negotiate shorter lock-in or performance-based exit clauses"
        },
        "one_sided_ip": {
            "keywords": ["all intellectual property", "work for hire", "assigns all rights",
                        "transfer of ip", "exclusive ownership"],
            "category": "intellectual_property",
            "severity": 7,
            "weight": 1.4,
            "description": "IP transfer clause may cause loss of valuable business assets",
            "recommendation": "Retain ownership of pre-existing IP and limit assignment scope"
        },
        "strict_non_compete": {
            "keywords": ["non-compete", "shall not compete", "restrictive covenant",
                        "prohibited from engaging", "exclusive dealing"],
            "category": "non_compete",
            "severity": 7,
            "weight": 1.3,
            "description": "Non-compete clause may limit future business opportunities",
            "recommendation": "Limit geographic scope, duration, and industry definition"
        },
        "unfavorable_jurisdiction": {
            "keywords": ["exclusive jurisdiction", "shall be governed by the laws of",
                        "courts of", "arbitration in"],
            "category": "dispute",
            "severity": 5,
            "weight": 1.0,
            "description": "Unfavorable jurisdiction may increase dispute resolution costs",
            "recommendation": "Negotiate jurisdiction in your business location"
        },
        "penalty_clause": {
            "keywords": ["penalty", "liquidated damages", "forfeit", "payable immediately",
                        "interest at"],
            "category": "payment",
            "severity": 6,
            "weight": 1.2,
            "description": "Penalty clauses may result in disproportionate costs",
            "recommendation": "Ensure penalties are proportional to actual damages"
        },
        "no_warranty": {
            "keywords": ["as is", "no warranty", "no representation", "disclaims all",
                        "without warranty"],
            "category": "warranty",
            "severity": 5,
            "weight": 1.0,
            "description": "Lack of warranties provides no recourse for defective goods/services",
            "recommendation": "Request basic warranties for fitness and quality"
        }
    }


def _get_alternative_suggestions(clause_type: str, risk_factors: List[RiskFactor]) -> List[str]:
    """Get alternative language suggestions for risky clauses."""
    alternatives = {
        "indemnity": [
            "Limit indemnification to direct damages arising from material breach",
            "Cap indemnification at the total contract value",
            "Exclude consequential and indirect damages",
            "Require timely notice and cooperation in defense"
        ],
        "termination": [
            "Require 30-60 days written notice for termination without cause",
            "Include cure period for termination for cause",
            "Add mutual termination rights",
            "Include transition assistance provisions"
        ],
        "non_compete": [
            "Limit non-compete to specific business segment",
            "Restrict geographic scope to operating regions",
            "Limit duration to 12-24 months post-termination",
            "Define competition narrowly"
        ],
        "intellectual_property": [
            "Retain ownership of pre-existing IP",
            "License IP specifically for contract purposes",
            "Define work product clearly",
            "Include joint ownership provisions where appropriate"
        ],
        "liability_limitation": [
            "Cap liability at 12-24 months of fees paid",
            "Carve out specific exclusions for gross negligence",
            "Include insurance requirements",
            "Mutual limitation of liability"
        ]
    }
    
    return alternatives.get(clause_type, [
        "Consider negotiating more balanced terms",
        "Seek legal counsel for alternative language",
        "Request clarification on ambiguous terms"
    ])


def _generate_risk_summary(clause_risks: List[ClauseRisk], score: float) -> str:
    """Generate a human-readable risk summary."""
    high_risks = [cr for cr in clause_risks if cr.risk_level == RiskLevel.HIGH]
    
    if score >= 7:
        summary = f"This contract contains significant risk factors. {len(high_risks)} clause(s) require immediate attention. "
        summary += "Legal review is strongly recommended before signing."
    elif score >= 4:
        summary = f"This contract has moderate risk levels. Some clauses may need negotiation. "
        summary += "Consider reviewing highlighted concerns."
    else:
        summary = "This contract appears to have balanced terms with manageable risk levels. "
        summary += "Standard precautions apply."
    
    return summary


def _get_top_concerns(clause_risks: List[ClauseRisk], limit: int = 5) -> List[str]:
    """Get the top concerns from clause risks."""
    concerns = []
    sorted_risks = sorted(clause_risks, key=lambda x: x.risk_score, reverse=True)
    
    for cr in sorted_risks[:limit]:
        if cr.risk_factors:
            concerns.append(f"{cr.clause_title}: {cr.risk_factors[0].description}")
    
    return concerns


def _get_contract_recommendations(clause_risks: List[ClauseRisk]) -> List[str]:
    """Generate contract-level recommendations."""
    recommendations = set()
    
    for cr in clause_risks:
        if cr.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
            for rf in cr.risk_factors:
                recommendations.add(rf.recommendation)
    
    return list(recommendations)[:7]  # Limit to top 7 recommendations
