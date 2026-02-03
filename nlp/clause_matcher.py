"""
Clause Similarity Matching Module
Compares contract clauses against standard templates
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import os
import json
import re
from difflib import SequenceMatcher


@dataclass
class SimilarityMatch:
    """Represents a similarity match between a clause and a template."""
    clause_id: str
    clause_title: str
    template_id: str
    template_clause_title: str
    similarity_score: float  # 0-100
    match_level: str  # exact, high, moderate, low, no_match
    deviations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "clause_id": self.clause_id,
            "clause_title": self.clause_title,
            "template_id": self.template_id,
            "template_clause_title": self.template_clause_title,
            "similarity_score": self.similarity_score,
            "match_level": self.match_level,
            "deviations": self.deviations
        }


@dataclass
class SimilarityReport:
    """Overall similarity analysis report."""
    total_clauses: int
    matched_clauses: int
    average_similarity: float
    standard_compliance_score: float  # 0-100
    matches: List[SimilarityMatch] = field(default_factory=list)
    non_standard_clauses: List[str] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> dict:
        return {
            "total_clauses": self.total_clauses,
            "matched_clauses": self.matched_clauses,
            "average_similarity": self.average_similarity,
            "standard_compliance_score": self.standard_compliance_score,
            "matches": [m.to_dict() for m in self.matches],
            "non_standard_clauses": self.non_standard_clauses,
            "summary": self.summary
        }


# Standard clause patterns for common contract types
STANDARD_CLAUSES = {
    "definitions": {
        "keywords": ["definition", "means", "shall mean", "refers to", "interpret"],
        "standard_elements": [
            "Clear definition of key terms",
            "Consistent terminology throughout",
            "Reference to applicable standards"
        ],
        "expected_content": [
            "agreement", "party", "parties", "effective date", "term",
            "services", "deliverables", "confidential information"
        ]
    },
    "term_duration": {
        "keywords": ["term", "duration", "period", "commence", "effective date"],
        "standard_elements": [
            "Clear start date",
            "Defined duration or end date",
            "Renewal terms if applicable"
        ],
        "expected_content": [
            "months", "years", "days", "commenc", "terminat", "renew"
        ]
    },
    "payment": {
        "keywords": ["payment", "fee", "compensation", "invoice", "amount"],
        "standard_elements": [
            "Clear payment amount",
            "Payment schedule/timeline",
            "Late payment terms",
            "Currency specification"
        ],
        "expected_content": [
            "Rs.", "INR", "rupees", "days", "invoice", "due", "interest"
        ]
    },
    "termination": {
        "keywords": ["termination", "terminate", "end", "cancel"],
        "standard_elements": [
            "Notice period requirement",
            "Termination for cause conditions",
            "Termination for convenience terms",
            "Post-termination obligations"
        ],
        "expected_content": [
            "notice", "days", "breach", "cure", "immediately", "obligations"
        ]
    },
    "confidentiality": {
        "keywords": ["confidential", "proprietary", "secret", "non-disclosure"],
        "standard_elements": [
            "Definition of confidential information",
            "Obligations of receiving party",
            "Exceptions to confidentiality",
            "Duration of confidentiality"
        ],
        "expected_content": [
            "disclose", "protect", "third party", "exception", "years", "survive"
        ]
    },
    "indemnification": {
        "keywords": ["indemnif", "hold harmless", "defend"],
        "standard_elements": [
            "Scope of indemnification",
            "Notice requirements",
            "Defense obligations",
            "Limitation on indemnity"
        ],
        "expected_content": [
            "claims", "damages", "losses", "third party", "breach", "negligence"
        ]
    },
    "limitation_of_liability": {
        "keywords": ["limitation", "liability", "liable", "damages"],
        "standard_elements": [
            "Cap on liability",
            "Exclusion of consequential damages",
            "Carve-outs for specific situations"
        ],
        "expected_content": [
            "indirect", "consequential", "punitive", "exceed", "aggregate", "cap"
        ]
    },
    "intellectual_property": {
        "keywords": ["intellectual property", "ip", "ownership", "license", "rights"],
        "standard_elements": [
            "Ownership of pre-existing IP",
            "Ownership of work product",
            "License grants",
            "IP representations"
        ],
        "expected_content": [
            "own", "license", "work product", "deliverable", "copyright", "patent"
        ]
    },
    "dispute_resolution": {
        "keywords": ["dispute", "arbitration", "jurisdiction", "governing law"],
        "standard_elements": [
            "Governing law specification",
            "Dispute resolution mechanism",
            "Venue/jurisdiction",
            "Arbitration terms if applicable"
        ],
        "expected_content": [
            "law", "India", "court", "arbitrat", "jurisdiction", "venue"
        ]
    },
    "force_majeure": {
        "keywords": ["force majeure", "act of god", "beyond control"],
        "standard_elements": [
            "Definition of force majeure events",
            "Notice requirements",
            "Effect on obligations",
            "Termination rights if prolonged"
        ],
        "expected_content": [
            "event", "control", "prevent", "perform", "notify", "suspend"
        ]
    },
    "notices": {
        "keywords": ["notice", "notification", "communication"],
        "standard_elements": [
            "Approved methods of notice",
            "Address for notices",
            "When notice is deemed delivered"
        ],
        "expected_content": [
            "writing", "address", "email", "deliver", "received", "deemed"
        ]
    },
    "general_provisions": {
        "keywords": ["general", "miscellaneous", "entire agreement", "amendment"],
        "standard_elements": [
            "Entire agreement clause",
            "Amendment requirements",
            "Severability",
            "Waiver provisions",
            "Assignment restrictions"
        ],
        "expected_content": [
            "entire", "supersede", "amend", "writing", "sever", "waive", "assign"
        ]
    }
}


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using sequence matching.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score 0-100
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    t1 = _normalize_text(text1)
    t2 = _normalize_text(text2)
    
    # Use SequenceMatcher for similarity
    matcher = SequenceMatcher(None, t1, t2)
    return round(matcher.ratio() * 100, 1)


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove punctuation for comparison
    text = re.sub(r'[^\w\s]', '', text)
    return text


def classify_clause_type(clause_title: str, clause_content: str) -> Optional[str]:
    """
    Classify a clause into a standard category.
    
    Args:
        clause_title: Title of the clause
        clause_content: Content of the clause
        
    Returns:
        Standard clause type or None if unclassified
    """
    combined = (clause_title + " " + clause_content).lower()
    
    best_match = None
    best_score = 0
    
    for clause_type, pattern in STANDARD_CLAUSES.items():
        score = 0
        
        # Check keywords
        for keyword in pattern["keywords"]:
            if keyword.lower() in combined:
                score += 10
        
        # Check expected content
        for content in pattern["expected_content"]:
            if content.lower() in combined:
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = clause_type
    
    return best_match if best_score >= 10 else None


def check_standard_elements(clause_content: str, clause_type: str) -> Tuple[List[str], List[str]]:
    """
    Check which standard elements are present/missing in a clause.
    
    Args:
        clause_content: Content of the clause
        clause_type: Type of clause
        
    Returns:
        Tuple of (present_elements, missing_elements)
    """
    if clause_type not in STANDARD_CLAUSES:
        return [], []
    
    standard = STANDARD_CLAUSES[clause_type]
    content_lower = clause_content.lower()
    
    present = []
    missing = []
    
    for element in standard["standard_elements"]:
        # Check if element concept is present (simplified check)
        element_keywords = element.lower().split()
        
        # Count how many keywords from the element are in the content
        keyword_matches = sum(1 for kw in element_keywords if kw in content_lower)
        
        if keyword_matches >= len(element_keywords) // 2:
            present.append(element)
        else:
            missing.append(element)
    
    return present, missing


def match_clauses_to_templates(clauses: List[Dict], contract_type: str = None) -> SimilarityReport:
    """
    Match contract clauses against standard templates.
    
    Args:
        clauses: List of clause dictionaries with 'id', 'title', 'content'
        contract_type: Type of contract for template selection
        
    Returns:
        SimilarityReport with all matches and deviations
    """
    matches = []
    non_standard = []
    total_similarity = 0
    matched_count = 0
    
    for clause in clauses:
        clause_id = clause.get("id", "unknown")
        clause_title = clause.get("title", "")
        clause_content = clause.get("content", "")
        
        # Classify the clause
        clause_type = classify_clause_type(clause_title, clause_content)
        
        if clause_type:
            # Check standard elements
            present, missing = check_standard_elements(clause_content, clause_type)
            
            # Calculate similarity based on present/missing elements
            if present or missing:
                element_score = len(present) / (len(present) + len(missing)) * 100
            else:
                element_score = 50
            
            # Check expected content presence
            content_score = 0
            expected = STANDARD_CLAUSES[clause_type]["expected_content"]
            for exp in expected:
                if exp.lower() in clause_content.lower():
                    content_score += 1
            content_score = (content_score / max(1, len(expected))) * 100
            
            # Combined score
            similarity = (element_score * 0.6 + content_score * 0.4)
            
            # Determine match level
            if similarity >= 90:
                match_level = "exact"
            elif similarity >= 75:
                match_level = "high"
            elif similarity >= 50:
                match_level = "moderate"
            elif similarity >= 25:
                match_level = "low"
            else:
                match_level = "no_match"
            
            # Identify deviations (missing elements)
            deviations = [f"Missing: {m}" for m in missing]
            
            matches.append(SimilarityMatch(
                clause_id=clause_id,
                clause_title=clause_title,
                template_id=clause_type,
                template_clause_title=clause_type.replace("_", " ").title(),
                similarity_score=round(similarity, 1),
                match_level=match_level,
                deviations=deviations
            ))
            
            total_similarity += similarity
            matched_count += 1
        else:
            # Non-standard clause
            non_standard.append(clause_title or clause_id)
    
    # Calculate overall scores
    avg_similarity = total_similarity / max(1, matched_count)
    compliance_score = (matched_count / max(1, len(clauses))) * (avg_similarity / 100) * 100
    
    # Generate summary
    summary = _generate_similarity_summary(
        len(clauses), matched_count, avg_similarity, non_standard
    )
    
    return SimilarityReport(
        total_clauses=len(clauses),
        matched_clauses=matched_count,
        average_similarity=round(avg_similarity, 1),
        standard_compliance_score=round(compliance_score, 1),
        matches=matches,
        non_standard_clauses=non_standard,
        summary=summary
    )


def _generate_similarity_summary(total: int, matched: int, avg_sim: float, non_standard: List[str]) -> str:
    """Generate human-readable similarity summary."""
    if total == 0:
        return "No clauses to analyze."
    
    match_pct = (matched / total) * 100
    
    if avg_sim >= 80 and match_pct >= 80:
        summary = "This contract closely follows standard templates. "
    elif avg_sim >= 60 and match_pct >= 60:
        summary = "This contract is moderately aligned with standard templates. "
    else:
        summary = "This contract contains significant deviations from standard templates. "
    
    summary += f"{matched} of {total} clauses ({match_pct:.0f}%) matched to standard types "
    summary += f"with {avg_sim:.0f}% average similarity. "
    
    if non_standard:
        if len(non_standard) <= 3:
            summary += f"Non-standard clauses: {', '.join(non_standard)}."
        else:
            summary += f"{len(non_standard)} non-standard clauses found."
    
    return summary


def get_template_clause(clause_type: str) -> Dict:
    """
    Get standard template information for a clause type.
    
    Args:
        clause_type: Type of clause
        
    Returns:
        Template information dictionary
    """
    if clause_type in STANDARD_CLAUSES:
        template = STANDARD_CLAUSES[clause_type]
        return {
            "type": clause_type,
            "title": clause_type.replace("_", " ").title(),
            "standard_elements": template["standard_elements"],
            "expected_content": template["expected_content"]
        }
    return {}


def get_low_similarity_clauses(report: SimilarityReport, threshold: float = 50) -> List[Dict]:
    """Get clauses with similarity below threshold."""
    low_sim = []
    for match in report.matches:
        if match.similarity_score < threshold:
            low_sim.append(match.to_dict())
    return low_sim
