"""
Obligation Analyzer Module
Identifies obligations, rights, and prohibitions in contract clauses
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ObligationType(Enum):
    OBLIGATION = "obligation"  # Must do something
    RIGHT = "right"            # May do something
    PROHIBITION = "prohibition"  # Must not do something


@dataclass
class Obligation:
    """Represents an obligation, right, or prohibition."""
    text: str
    obligation_type: ObligationType
    subject: str  # Who has the obligation/right
    action: str   # What they must/may/cannot do
    condition: str = ""  # Any conditions attached
    deadline: str = ""   # Any time constraints
    consequence: str = ""  # What happens if violated
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "type": self.obligation_type.value,
            "subject": self.subject,
            "action": self.action,
            "condition": self.condition,
            "deadline": self.deadline,
            "consequence": self.consequence,
            "confidence": self.confidence
        }


# Modal verb patterns
OBLIGATION_PATTERNS = {
    ObligationType.OBLIGATION: [
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>shall|must|will|agrees? to|undertakes? to|is required to|is obligated to|covenants? to)\s+(?P<action>[^.]+)',
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>has|have)\s+(?:the\s+)?(?:duty|obligation)\s+to\s+(?P<action>[^.]+)',
        r'it\s+(?P<modal>shall be|is)\s+(?:the\s+)?(?:duty|obligation|responsibility)\s+of\s+(?P<subject>[A-Za-z\s]+?)\s+to\s+(?P<action>[^.]+)',
    ],
    ObligationType.RIGHT: [
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>may|can|is entitled to|has the right to|is permitted to|is authorized to)\s+(?P<action>[^.]+)',
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>has|have)\s+(?:the\s+)?(?:right|option|discretion)\s+to\s+(?P<action>[^.]+)',
        r'(?P<modal>nothing\s+(?:herein|in this agreement)\s+shall\s+prevent)\s+(?P<subject>[A-Za-z\s]+?)\s+from\s+(?P<action>[^.]+)',
    ],
    ObligationType.PROHIBITION: [
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>shall not|must not|may not|cannot|will not|is prohibited from|is not permitted to|is not authorized to)\s+(?P<action>[^.]+)',
        r'(?P<subject>[A-Za-z\s]+?)\s+(?P<modal>agrees? not to|undertakes? not to|covenants? not to)\s+(?P<action>[^.]+)',
        r'(?P<modal>under no circumstances)\s+(?:shall|may|will)\s+(?P<subject>[A-Za-z\s]+?)\s+(?P<action>[^.]+)',
    ]
}

# Condition patterns
CONDITION_PATTERNS = [
    r'(?:subject to|provided that|on condition that|if|unless|in the event (?:that|of)|upon)\s+([^,]+)',
    r'(?:so long as|as long as|during)\s+([^,]+)',
]

# Deadline patterns
DEADLINE_PATTERNS = [
    r'within\s+(\d+\s+(?:days?|weeks?|months?|years?))',
    r'(?:by|before|no later than|on or before)\s+([^,]+(?:\d+|January|February|March|April|May|June|July|August|September|October|November|December)[^,]*)',
    r'(?:not\s+(?:less|more)\s+than)\s+(\d+\s+(?:days?|weeks?|months?|years?))',
]

# Consequence patterns
CONSEQUENCE_PATTERNS = [
    r'(?:failing which|otherwise|in default of which|upon failure to do so)\s*,?\s+([^.]+)',
    r'(?:in such event|in that case)\s*,?\s+([^.]+)',
    r'(?:shall be liable for|shall pay|shall forfeit)\s+([^.]+)',
]


def analyze_obligations(text: str) -> List[Obligation]:
    """
    Analyze text to identify obligations, rights, and prohibitions.
    
    Args:
        text: Contract text or clause content
        
    Returns:
        List of identified obligations
    """
    obligations = []
    sentences = _split_sentences(text)
    
    for sentence in sentences:
        for obligation_type, patterns in OBLIGATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    groups = match.groupdict()
                    subject = _clean_subject(groups.get('subject', ''))
                    action = groups.get('action', '').strip()
                    
                    if not subject or not action:
                        continue
                    
                    # Extract additional context
                    condition = _extract_condition(sentence)
                    deadline = _extract_deadline(sentence)
                    consequence = _extract_consequence(sentence)
                    
                    obligation = Obligation(
                        text=sentence.strip(),
                        obligation_type=obligation_type,
                        subject=subject,
                        action=action[:200],  # Limit action length
                        condition=condition,
                        deadline=deadline,
                        consequence=consequence,
                        confidence=0.8 if len(subject) > 3 else 0.5
                    )
                    obligations.append(obligation)
    
    return _deduplicate_obligations(obligations)


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _clean_subject(subject: str) -> str:
    """Clean and normalize the subject."""
    subject = subject.strip()
    
    # Remove common prefixes
    prefixes = ['the ', 'each ', 'every ', 'any ', 'either ', 'neither ']
    lower = subject.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            subject = subject[len(prefix):]
            break
    
    # Capitalize first letter
    if subject:
        subject = subject[0].upper() + subject[1:] if len(subject) > 1 else subject.upper()
    
    return subject.strip()


def _extract_condition(sentence: str) -> str:
    """Extract conditions from a sentence."""
    for pattern in CONDITION_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:150]
    return ""


def _extract_deadline(sentence: str) -> str:
    """Extract deadline/time constraints from a sentence."""
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_consequence(sentence: str) -> str:
    """Extract consequence of non-compliance from a sentence."""
    for pattern in CONSEQUENCE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:150]
    return ""


def _deduplicate_obligations(obligations: List[Obligation]) -> List[Obligation]:
    """Remove duplicate obligations."""
    seen = set()
    unique = []
    
    for obligation in obligations:
        key = (obligation.subject.lower(), obligation.action[:50].lower(), obligation.obligation_type)
        if key not in seen:
            seen.add(key)
            unique.append(obligation)
    
    return unique


def get_obligations_summary(obligations: List[Obligation]) -> Dict[str, any]:
    """
    Get a summary of obligations by type and subject.
    
    Args:
        obligations: List of obligations
        
    Returns:
        Summary dictionary
    """
    summary = {
        "total": len(obligations),
        "by_type": {
            "obligations": 0,
            "rights": 0,
            "prohibitions": 0
        },
        "by_subject": {},
        "with_deadlines": 0,
        "with_consequences": 0
    }
    
    for obligation in obligations:
        # Count by type
        if obligation.obligation_type == ObligationType.OBLIGATION:
            summary["by_type"]["obligations"] += 1
        elif obligation.obligation_type == ObligationType.RIGHT:
            summary["by_type"]["rights"] += 1
        elif obligation.obligation_type == ObligationType.PROHIBITION:
            summary["by_type"]["prohibitions"] += 1
        
        # Count by subject
        subject = obligation.subject
        if subject not in summary["by_subject"]:
            summary["by_subject"][subject] = 0
        summary["by_subject"][subject] += 1
        
        # Count deadlines and consequences
        if obligation.deadline:
            summary["with_deadlines"] += 1
        if obligation.consequence:
            summary["with_consequences"] += 1
    
    return summary


def obligations_to_dict(obligations: List[Obligation]) -> List[dict]:
    """Convert list of obligations to list of dictionaries."""
    return [o.to_dict() for o in obligations]


def get_high_risk_obligations(obligations: List[Obligation]) -> List[Obligation]:
    """
    Identify obligations that may pose higher risk.
    
    Risk indicators:
    - Prohibitions
    - Obligations without clear deadlines
    - Obligations with consequences
    """
    high_risk = []
    
    for obligation in obligations:
        is_high_risk = (
            obligation.obligation_type == ObligationType.PROHIBITION or
            obligation.consequence or
            (obligation.obligation_type == ObligationType.OBLIGATION and 
             any(word in obligation.action.lower() for word in 
                 ['indemnify', 'liable', 'penalty', 'forfeit', 'terminate', 'immediate']))
        )
        
        if is_high_risk:
            high_risk.append(obligation)
    
    return high_risk
