"""
Ambiguity Detection Module
Detects vague, unclear, or ambiguous language in contracts
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
import re


@dataclass
class AmbiguityFlag:
    """Represents an ambiguity found in the text."""
    term: str
    category: str
    severity: str  # low, medium, high
    context: str
    position: int
    suggestion: str
    
    def to_dict(self) -> dict:
        return {
            "term": self.term,
            "category": self.category,
            "severity": self.severity,
            "context": self.context,
            "position": self.position,
            "suggestion": self.suggestion
        }


@dataclass
class AmbiguityReport:
    """Overall ambiguity analysis report."""
    total_flags: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    clarity_score: float  # 0-100, higher is clearer
    flags: List[AmbiguityFlag] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> dict:
        return {
            "total_flags": self.total_flags,
            "high_severity_count": self.high_severity_count,
            "medium_severity_count": self.medium_severity_count,
            "low_severity_count": self.low_severity_count,
            "clarity_score": self.clarity_score,
            "flags": [f.to_dict() for f in self.flags],
            "summary": self.summary
        }


# Ambiguous terms and patterns categorized by type
AMBIGUOUS_PATTERNS = {
    "vague_qualifiers": {
        "terms": [
            "reasonable", "reasonably", "unreasonable",
            "appropriate", "appropriately", "inappropriate",
            "adequate", "adequately", "inadequate",
            "sufficient", "sufficiently", "insufficient",
            "satisfactory", "unsatisfactory",
            "acceptable", "unacceptable",
            "proper", "properly", "improper",
            "suitable", "unsuitable",
            "fair", "fairly", "unfair"
        ],
        "severity": "medium",
        "description": "Subjective qualifier without clear definition",
        "suggestion": "Define specific measurable criteria"
    },
    "indefinite_quantities": {
        "terms": [
            "approximately", "about", "around",
            "substantial", "substantially",
            "significant", "significantly",
            "material", "materially",
            "considerable", "considerably",
            "minor", "major",
            "some", "several", "various",
            "numerous", "many", "few"
        ],
        "severity": "medium",
        "description": "Indefinite quantity that could be disputed",
        "suggestion": "Specify exact numbers or percentages"
    },
    "time_uncertainty": {
        "terms": [
            "promptly", "soon", "timely",
            "without delay", "as soon as possible",
            "within a reasonable time", "reasonable period",
            "from time to time", "periodically",
            "occasionally", "regularly", "frequently"
        ],
        "severity": "high",
        "description": "Vague time reference that creates uncertainty",
        "suggestion": "Specify exact number of days/hours/weeks"
    },
    "conditional_uncertainty": {
        "terms": [
            "may", "might", "could",
            "if deemed necessary", "if appropriate",
            "at its discretion", "sole discretion",
            "in its judgment", "as it sees fit",
            "reserves the right", "option to"
        ],
        "severity": "high",
        "description": "Discretionary language creating one-sided flexibility",
        "suggestion": "Define specific conditions or make obligations mutual"
    },
    "scope_ambiguity": {
        "terms": [
            "including but not limited to",
            "such as", "for example", "e.g.",
            "among other things", "inter alia",
            "and/or", "etc.", "et cetera",
            "any and all", "whatsoever"
        ],
        "severity": "low",
        "description": "Open-ended scope that could expand obligations",
        "suggestion": "Provide exhaustive list or clear boundaries"
    },
    "best_efforts": {
        "terms": [
            "best efforts", "reasonable efforts",
            "commercially reasonable efforts",
            "good faith efforts", "diligent efforts",
            "endeavour", "endeavor", "strive to"
        ],
        "severity": "medium",
        "description": "Effort-based standard without clear metrics",
        "suggestion": "Define specific deliverables or success criteria"
    },
    "undefined_standards": {
        "terms": [
            "industry standard", "market standard",
            "customary", "usual", "normal",
            "professional manner", "workmanlike manner",
            "state of the art", "best practice"
        ],
        "severity": "medium",
        "description": "Reference to external undefined standard",
        "suggestion": "Define specific quality standards or benchmarks"
    }
}


def detect_ambiguities(text: str) -> AmbiguityReport:
    """
    Detect ambiguous language in contract text.
    
    Args:
        text: Contract text to analyze
        
    Returns:
        AmbiguityReport with all detected ambiguities
    """
    flags = []
    text_lower = text.lower()
    
    for category, pattern_info in AMBIGUOUS_PATTERNS.items():
        for term in pattern_info["terms"]:
            # Find all occurrences
            term_pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(term_pattern, text_lower, re.IGNORECASE):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                flags.append(AmbiguityFlag(
                    term=term,
                    category=category,
                    severity=pattern_info["severity"],
                    context=f"...{context}...",
                    position=match.start(),
                    suggestion=pattern_info["suggestion"]
                ))
    
    # Remove duplicates based on position (keep first occurrence of overlapping)
    flags = _deduplicate_flags(flags)
    
    # Count severities
    high_count = sum(1 for f in flags if f.severity == "high")
    medium_count = sum(1 for f in flags if f.severity == "medium")
    low_count = sum(1 for f in flags if f.severity == "low")
    
    # Calculate clarity score (0-100)
    # Penalize based on ambiguity count and severity
    text_length = len(text.split())
    penalty = (high_count * 3 + medium_count * 2 + low_count * 1) * 5
    clarity_score = max(0, min(100, 100 - (penalty / max(1, text_length / 100))))
    
    # Generate summary
    summary = _generate_summary(flags, clarity_score)
    
    return AmbiguityReport(
        total_flags=len(flags),
        high_severity_count=high_count,
        medium_severity_count=medium_count,
        low_severity_count=low_count,
        clarity_score=round(clarity_score, 1),
        flags=flags,
        summary=summary
    )


def _deduplicate_flags(flags: List[AmbiguityFlag]) -> List[AmbiguityFlag]:
    """Remove overlapping flags, keeping the first occurrence."""
    if not flags:
        return []
    
    # Sort by position
    sorted_flags = sorted(flags, key=lambda f: f.position)
    
    # Keep non-overlapping
    result = [sorted_flags[0]]
    for flag in sorted_flags[1:]:
        # Keep if position is different enough (not same match)
        if flag.position - result[-1].position > len(result[-1].term):
            result.append(flag)
    
    return result


def _generate_summary(flags: List[AmbiguityFlag], clarity_score: float) -> str:
    """Generate a human-readable summary of ambiguity analysis."""
    if clarity_score >= 80:
        level = "clear and well-defined"
    elif clarity_score >= 60:
        level = "moderately clear with some vague terms"
    elif clarity_score >= 40:
        level = "contains significant ambiguous language"
    else:
        level = "highly ambiguous with many undefined terms"
    
    summary = f"This contract is {level} (Clarity Score: {clarity_score:.0f}/100). "
    
    if flags:
        # Count categories
        categories = {}
        for f in flags:
            categories[f.category] = categories.get(f.category, 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        category_text = ", ".join([c[0].replace("_", " ") for c in top_categories])
        
        summary += f"Main areas of concern: {category_text}. "
        
        high_flags = [f for f in flags if f.severity == "high"]
        if high_flags:
            summary += f"Found {len(high_flags)} high-severity ambiguities requiring attention."
    else:
        summary += "No significant ambiguities detected."
    
    return summary


def get_ambiguity_by_clause(text: str, clauses: List[Dict]) -> Dict[str, List[AmbiguityFlag]]:
    """
    Group ambiguities by clause.
    
    Args:
        text: Full contract text
        clauses: List of clause dictionaries with 'id' and 'content'
        
    Returns:
        Dictionary mapping clause IDs to their ambiguity flags
    """
    result = {}
    
    for clause in clauses:
        clause_id = clause.get("id", "unknown")
        clause_content = clause.get("content", "")
        
        if clause_content:
            report = detect_ambiguities(clause_content)
            if report.flags:
                result[clause_id] = report.flags
    
    return result


def get_top_ambiguities(report: AmbiguityReport, limit: int = 10) -> List[Dict]:
    """Get the top ambiguities sorted by severity."""
    severity_order = {"high": 0, "medium": 1, "low": 2}
    sorted_flags = sorted(report.flags, key=lambda f: severity_order[f.severity])
    
    return [f.to_dict() for f in sorted_flags[:limit]]
