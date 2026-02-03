"""
Compliance Checker Module
Checks contract compliance with common Indian business practices
"""
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ComplianceIssue:
    """Represents a compliance concern."""
    category: str
    description: str
    severity: str  # low, medium, high
    recommendation: str
    reference: str = ""
    
    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "description": self.description,
            "severity": self.severity,
            "recommendation": self.recommendation,
            "reference": self.reference
        }


@dataclass
class ComplianceReport:
    """Compliance check report."""
    is_compliant: bool
    issues: List[ComplianceIssue]
    score: float  # 0-100
    summary: str
    
    def to_dict(self) -> dict:
        return {
            "is_compliant": self.is_compliant,
            "issues": [issue.to_dict() for issue in self.issues],
            "score": self.score,
            "summary": self.summary
        }


# Indian business compliance checkpoints
COMPLIANCE_CHECKS = {
    "stamp_duty": {
        "keywords": ["stamp duty", "stamp paper", "adequately stamped", "e-stamp"],
        "required_for": ["Lease Agreement", "Partnership Deed", "Service Contract"],
        "description": "Stamp duty requirements for contract enforceability",
        "recommendation": "Ensure contract is executed on appropriate stamp paper as per state requirements"
    },
    "registration": {
        "keywords": ["registered", "registration", "sub-registrar"],
        "required_for": ["Lease Agreement", "Partnership Deed"],
        "description": "Registration requirements for certain contracts",
        "recommendation": "Lease agreements over 11 months require registration"
    },
    "jurisdiction_clause": {
        "keywords": ["jurisdiction", "courts of", "governed by"],
        "required_for": ["all"],
        "description": "Jurisdiction and governing law should be specified",
        "recommendation": "Include clear jurisdiction clause for dispute resolution"
    },
    "arbitration_validity": {
        "keywords": ["arbitration", "arbitrator", "arbitral"],
        "required_for": ["all"],
        "description": "Arbitration clause validity",
        "recommendation": "Ensure arbitration clause complies with Arbitration Act requirements"
    },
    "witness_requirement": {
        "keywords": ["witness", "witnessed by", "in presence of"],
        "required_for": ["Partnership Deed", "Lease Agreement"],
        "description": "Witness requirements for contract validity",
        "recommendation": "Include at least two witnesses for important contracts"
    },
    "consideration": {
        "keywords": ["consideration", "payment", "fee", "rent", "compensation"],
        "required_for": ["all"],
        "description": "Valid consideration is essential for contract enforceability",
        "recommendation": "Ensure consideration is clearly stated and lawful"
    },
    "digital_signature": {
        "keywords": ["electronic signature", "digital signature", "e-sign"],
        "required_for": ["all"],
        "description": "Digital signature validity",
        "recommendation": "Use certified digital signatures for electronic contracts"
    },
    "force_majeure": {
        "keywords": ["force majeure", "act of god", "unforeseen circumstances"],
        "required_for": ["all"],
        "description": "Force majeure clause for risk allocation",
        "recommendation": "Include comprehensive force majeure clause post-COVID"
    },
    "dispute_timeline": {
        "keywords": ["limitation period", "within", "days from dispute"],
        "required_for": ["all"],
        "description": "Dispute resolution timeline",
        "recommendation": "Specify timeline for raising disputes and claims"
    },
    "gst_reference": {
        "keywords": ["gst", "goods and services tax", "gstin", "tax invoice"],
        "required_for": ["Vendor Contract", "Service Contract"],
        "description": "GST compliance for business contracts",
        "recommendation": "Include GSTIN and GST payment terms in commercial contracts"
    }
}

# Contract type specific requirements
CONTRACT_REQUIREMENTS = {
    "Employment Agreement": {
        "mandatory_elements": [
            "designation", "salary", "probation", "notice period", 
            "leaves", "confidentiality", "termination"
        ],
        "recommended_elements": [
            "working hours", "benefits", "appraisal", "non-compete"
        ],
        "restrictions": [
            "Non-compete clauses have limited enforceability in India"
        ]
    },
    "Vendor Contract": {
        "mandatory_elements": [
            "scope", "payment terms", "delivery", "warranty", "termination"
        ],
        "recommended_elements": [
            "quality standards", "inspection", "insurance", "indemnity"
        ],
        "restrictions": []
    },
    "Lease Agreement": {
        "mandatory_elements": [
            "rent", "deposit", "term", "maintenance", "termination", "notice"
        ],
        "recommended_elements": [
            "utilities", "sub-lease restrictions", "renewal terms"
        ],
        "restrictions": [
            "Rent Control Act provisions may override contract terms in certain states"
        ]
    },
    "Service Contract": {
        "mandatory_elements": [
            "scope of services", "fees", "timeline", "deliverables", "termination"
        ],
        "recommended_elements": [
            "milestones", "sla", "liability", "ip rights"
        ],
        "restrictions": []
    },
    "Partnership Deed": {
        "mandatory_elements": [
            "partners", "capital", "profit sharing", "management", "dissolution"
        ],
        "recommended_elements": [
            "admission", "retirement", "goodwill", "banking"
        ],
        "restrictions": []
    }
}


def check_compliance(text: str, contract_type: str) -> ComplianceReport:
    """
    Check contract text for compliance issues.
    
    Args:
        text: Contract text
        contract_type: Type of contract
        
    Returns:
        ComplianceReport with findings
    """
    issues = []
    content_lower = text.lower()
    
    # Run general compliance checks
    for check_name, check_info in COMPLIANCE_CHECKS.items():
        applies = contract_type in check_info["required_for"] or "all" in check_info["required_for"]
        
        if applies:
            has_element = any(kw in content_lower for kw in check_info["keywords"])
            
            if not has_element:
                issues.append(ComplianceIssue(
                    category=check_name,
                    description=f"Missing: {check_info['description']}",
                    severity="medium",
                    recommendation=check_info["recommendation"]
                ))
    
    # Check contract-type specific requirements
    if contract_type in CONTRACT_REQUIREMENTS:
        requirements = CONTRACT_REQUIREMENTS[contract_type]
        
        # Check mandatory elements
        for element in requirements["mandatory_elements"]:
            if element.lower() not in content_lower:
                issues.append(ComplianceIssue(
                    category="mandatory_element",
                    description=f"Missing mandatory element: {element}",
                    severity="high",
                    recommendation=f"Include {element} provisions in the contract"
                ))
        
        # Check recommended elements
        for element in requirements["recommended_elements"]:
            if element.lower() not in content_lower:
                issues.append(ComplianceIssue(
                    category="recommended_element",
                    description=f"Consider adding: {element}",
                    severity="low",
                    recommendation=f"Consider including {element} provisions"
                ))
        
        # Add relevant restrictions as notes
        for restriction in requirements["restrictions"]:
            issues.append(ComplianceIssue(
                category="legal_note",
                description=restriction,
                severity="low",
                recommendation="Be aware of this legal consideration"
            ))
    
    # Calculate compliance score
    high_issues = sum(1 for i in issues if i.severity == "high")
    medium_issues = sum(1 for i in issues if i.severity == "medium")
    low_issues = sum(1 for i in issues if i.severity == "low")
    
    score = 100 - (high_issues * 15) - (medium_issues * 7) - (low_issues * 2)
    score = max(0, min(100, score))
    
    # Generate summary
    if score >= 80:
        summary = "Contract appears to meet basic compliance requirements with minor suggestions."
    elif score >= 60:
        summary = "Contract has some compliance gaps that should be addressed before signing."
    else:
        summary = "Contract has significant compliance issues. Legal review recommended."
    
    return ComplianceReport(
        is_compliant=score >= 70,
        issues=issues,
        score=round(score, 1),
        summary=summary
    )


def get_contract_checklist(contract_type: str) -> Dict[str, List[str]]:
    """
    Get a checklist of elements for a contract type.
    
    Args:
        contract_type: Type of contract
        
    Returns:
        Checklist dictionary
    """
    if contract_type in CONTRACT_REQUIREMENTS:
        return CONTRACT_REQUIREMENTS[contract_type]
    
    return {
        "mandatory_elements": ["parties", "terms", "consideration"],
        "recommended_elements": ["jurisdiction", "termination", "force majeure"],
        "restrictions": []
    }


def get_indian_law_notes(contract_type: str) -> List[str]:
    """
    Get relevant Indian law notes for a contract type.
    
    Args:
        contract_type: Type of contract
        
    Returns:
        List of legal notes
    """
    notes = {
        "Employment Agreement": [
            "Section 27 of Indian Contract Act restricts non-compete enforcement",
            "Shops & Establishment Act governs working hours and leaves",
            "Gratuity payable after 5 years of service under Payment of Gratuity Act",
            "PF and ESI contributions mandatory above threshold"
        ],
        "Lease Agreement": [
            "Registration mandatory for leases over 11 months",
            "Stamp duty varies by state",
            "Rent Control Act may limit rent increases in certain states",
            "GST applicable on commercial property rent"
        ],
        "Service Contract": [
            "GST applicable on services",
            "TDS deduction required above threshold",
            "Service tax provisions for cross-border services"
        ],
        "Vendor Contract": [
            "Sale of Goods Act governs quality and delivery",
            "GST input credit considerations",
            "Consumer Protection Act may apply"
        ],
        "Partnership Deed": [
            "Partnership Act 1932 governs partnerships",
            "Registration optional but recommended",
            "Partners have unlimited liability unless LLP"
        ]
    }
    
    return notes.get(contract_type, [
        "Indian Contract Act 1872 governs general contract provisions",
        "Specific Relief Act governs enforcement of contracts"
    ])
