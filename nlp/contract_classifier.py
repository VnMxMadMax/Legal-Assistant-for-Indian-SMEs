"""
Contract Type Classification Module
Classifies contracts into predefined categories
"""
import re
from typing import Dict, List, Tuple
from config import CONTRACT_TYPES


# Keywords and patterns for each contract type
CONTRACT_PATTERNS = {
    "Employment Agreement": {
        "keywords": [
            "employment", "employee", "employer", "salary", "wages", "designation",
            "probation", "termination of employment", "notice period", "resignation",
            "working hours", "leave", "benefits", "provident fund", "gratuity",
            "job description", "reporting", "compensation", "appraisal"
        ],
        "phrases": [
            r"terms? of employment",
            r"employment contract",
            r"letter of appointment",
            r"offer letter",
            r"joining date",
            r"employee handbook"
        ],
        "weight": 1.0
    },
    "Vendor Contract": {
        "keywords": [
            "vendor", "supplier", "purchase order", "procurement", "delivery",
            "goods", "materials", "supply", "invoice", "payment terms",
            "quality", "inspection", "warranty", "defects", "returns"
        ],
        "phrases": [
            r"purchase agreement",
            r"supply agreement",
            r"vendor agreement",
            r"master service agreement",
            r"goods and services"
        ],
        "weight": 1.0
    },
    "Lease Agreement": {
        "keywords": [
            "lease", "lessor", "lessee", "tenant", "landlord", "rent",
            "premises", "property", "deposit", "maintenance", "utilities",
            "eviction", "sub-lease", "renewal", "possession", "occupation"
        ],
        "phrases": [
            r"lease agreement",
            r"rental agreement",
            r"tenancy agreement",
            r"leave and license",
            r"demised premises"
        ],
        "weight": 1.0
    },
    "Partnership Deed": {
        "keywords": [
            "partner", "partnership", "firm", "capital contribution", "profit sharing",
            "loss sharing", "dissolution", "retirement", "admission", "goodwill",
            "partners' meeting", "voting rights", "management"
        ],
        "phrases": [
            r"partnership deed",
            r"partnership agreement",
            r"partner(?:s)?\s+(?:of|in)",
            r"capital account",
            r"profit and loss ratio"
        ],
        "weight": 1.0
    },
    "Service Contract": {
        "keywords": [
            "service", "services", "scope of work", "deliverables", "milestones",
            "professional", "consultant", "contractor", "engagement", "project",
            "fee", "rate", "billing", "invoice", "completion"
        ],
        "phrases": [
            r"service agreement",
            r"service level agreement",
            r"statement of work",
            r"professional services",
            r"consulting agreement"
        ],
        "weight": 1.0
    },
    "Non-Disclosure Agreement": {
        "keywords": [
            "confidential", "confidentiality", "proprietary", "trade secret",
            "disclosure", "non-disclosure", "nda", "secret", "protected information"
        ],
        "phrases": [
            r"non-disclosure agreement",
            r"confidentiality agreement",
            r"mutual nda",
            r"confidential information",
            r"receiving party"
        ],
        "weight": 1.2  # Higher weight for NDA-specific terms
    }
}


def classify_contract(text: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Classify a contract into one of the predefined categories.
    
    Args:
        text: The contract text to classify
        
    Returns:
        Tuple of (contract_type, confidence_score, all_scores)
    """
    text_lower = text.lower()
    scores = {}
    
    for contract_type, patterns in CONTRACT_PATTERNS.items():
        score = 0.0
        
        # Check keywords
        keyword_matches = 0
        for keyword in patterns["keywords"]:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            if count > 0:
                keyword_matches += min(count, 5)  # Cap per-keyword contribution
        
        # Normalize keyword score (0-50 points)
        score += min(keyword_matches * 2, 50)
        
        # Check phrases (higher weight)
        phrase_matches = 0
        for phrase in patterns["phrases"]:
            if re.search(phrase, text_lower):
                phrase_matches += 1
        
        # Phrase score (0-30 points, higher weight)
        score += phrase_matches * 10
        
        # Apply type-specific weight
        score *= patterns["weight"]
        
        scores[contract_type] = score
    
    # Determine the best match
    if not scores:
        return "Unknown", 0.0, scores
    
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    
    # Calculate confidence (normalize to 0-1)
    max_possible = 80 * 1.2  # Maximum possible score
    confidence = min(best_score / max_possible, 1.0)
    
    # If confidence is too low, mark as Unknown
    if confidence < 0.15:
        return "Unknown", confidence, scores
    
    return best_type, confidence, scores


def get_contract_type_features(text: str, contract_type: str) -> Dict[str, List[str]]:
    """
    Get the features (keywords, phrases) that led to a contract classification.
    
    Args:
        text: The contract text
        contract_type: The classified contract type
        
    Returns:
        Dictionary with matched keywords and phrases
    """
    if contract_type not in CONTRACT_PATTERNS:
        return {"keywords": [], "phrases": []}
    
    text_lower = text.lower()
    patterns = CONTRACT_PATTERNS[contract_type]
    
    matched_keywords = []
    for keyword in patterns["keywords"]:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            matched_keywords.append(keyword)
    
    matched_phrases = []
    for phrase in patterns["phrases"]:
        match = re.search(phrase, text_lower)
        if match:
            matched_phrases.append(match.group(0))
    
    return {
        "keywords": matched_keywords,
        "phrases": matched_phrases
    }


def get_all_contract_types() -> List[str]:
    """Get list of all supported contract types."""
    return list(CONTRACT_PATTERNS.keys()) + ["Unknown"]
