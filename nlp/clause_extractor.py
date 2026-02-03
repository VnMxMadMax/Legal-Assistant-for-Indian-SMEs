"""
Clause Extraction Module
Extracts clauses and sub-clauses from contract documents
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Clause:
    """Represents a contract clause."""
    id: str
    title: str
    content: str
    level: int  # 1 for main clause, 2 for sub-clause, etc.
    parent_id: Optional[str] = None
    clause_type: Optional[str] = None
    start_position: int = 0
    end_position: int = 0
    sub_clauses: List['Clause'] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert clause to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "parent_id": self.parent_id,
            "clause_type": self.clause_type,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "sub_clauses": [sc.to_dict() for sc in self.sub_clauses]
        }


# Common clause title patterns - More flexible matching
CLAUSE_PATTERNS = {
    "level_1": [
        # Numbered sections: 1. Title, 1) Title, 1: Title
        r'^(?P<num>\d+)[.\):\s]+(?P<title>[A-Z][A-Za-z\s,&\-]+)',
        # ALL CAPS headers
        r'^(?P<num>)(?P<title>[A-Z][A-Z\s,&\-]{3,})$',
        # Article/Section/Clause headers
        r'^(?:ARTICLE|Article)\s*(?P<num>\d+|[IVX]+)[:\.\s]*(?P<title>[A-Za-z\s,&\-]*)',
        r'^(?:SECTION|Section)\s*(?P<num>\d+)[:\.\s]*(?P<title>[A-Za-z\s,&\-]*)',
        r'^(?:CLAUSE|Clause)\s*(?P<num>\d+)[:\.\s]*(?P<title>[A-Za-z\s,&\-]*)',
        # Common contract section headers (without numbers)
        r'^(?P<num>)(?P<title>(?:WHEREAS|RECITALS|DEFINITIONS|TERM|SCOPE|PAYMENT|TERMINATION|CONFIDENTIALITY|INDEMNITY|WARRANTY|DISPUTE|NOTICES|GENERAL|MISCELLANEOUS|SIGNATURES)[A-Z\s]*):?$',
    ],
    "level_2": [
        # Sub-numbered: 1.1, 1.1., (a), (i), a), a.
        r'^(?P<num>\d+\.\d+)[.\):\s]*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
        r'^\((?P<num>[a-z])\)\s*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
        r'^(?P<num>[a-z])\)\s*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
        r'^\((?P<num>[ivx]+)\)\s*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
    ],
    "level_3": [
        # Sub-sub-numbered: 1.1.1, (aa), (1), i., ii.
        r'^(?P<num>\d+\.\d+\.\d+)[.\):\s]*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
        r'^\((?P<num>\d+)\)\s*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
        r'^(?P<num>[ivx]+)\.\s*(?P<title>[A-Za-z][A-Za-z\s,&\-]*)?',
    ]
}

# Common clause type keywords
CLAUSE_TYPE_KEYWORDS = {
    "definitions": ["definition", "interpret", "meaning", "shall mean"],
    "term": ["term", "duration", "period", "effective date", "commencement"],
    "obligations": ["shall", "must", "undertake", "agree to", "covenant"],
    "payment": ["payment", "fee", "price", "consideration", "invoice", "compensation"],
    "termination": ["termination", "terminate", "expiry", "cancellation"],
    "confidentiality": ["confidential", "non-disclosure", "proprietary", "secret"],
    "indemnity": ["indemnify", "indemnification", "hold harmless", "liability"],
    "warranty": ["warranty", "warrants", "representation", "guarantee"],
    "dispute": ["dispute", "arbitration", "jurisdiction", "governing law"],
    "force_majeure": ["force majeure", "act of god", "unforeseen", "beyond control"],
    "intellectual_property": ["intellectual property", "ip", "patent", "copyright", "trademark"],
    "non_compete": ["non-compete", "non-solicitation", "restriction", "covenant not to"],
    "insurance": ["insurance", "policy", "coverage", "indemnity insurance"],
    "notices": ["notice", "notification", "communication", "writing"],
    "assignment": ["assignment", "transfer", "assign", "delegate"],
    "amendment": ["amendment", "modification", "variation", "change"],
    "entire_agreement": ["entire agreement", "whole agreement", "integration"],
    "severability": ["severability", "invalid", "unenforceable", "severable"]
}


def extract_clauses(text: str) -> List[Clause]:
    """
    Extract all clauses from contract text.
    
    Args:
        text: The contract text
        
    Returns:
        List of extracted clauses
    """
    clauses = []
    lines = text.split('\n')
    current_clause = None
    current_content = []
    clause_counter = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            if current_content:
                current_content.append("")
            continue
        
        # Check for clause headers
        clause_match = _match_clause_pattern(line_stripped)
        
        if clause_match:
            # Save previous clause (even if it has no content beyond the title)
            if current_clause:
                current_clause.content = '\n'.join(current_content).strip()
                current_clause.clause_type = _identify_clause_type(
                    current_clause.title + " " + current_clause.content
                )
                clauses.append(current_clause)
            
            # Start new clause
            clause_counter += 1
            level, num, title = clause_match
            
            current_clause = Clause(
                id=f"clause_{clause_counter}",
                title=title.strip() if title else f"Clause {num}",
                content="",
                level=level,
                start_position=i
            )
            current_content = []
        else:
            # Add to current clause content
            current_content.append(line_stripped)
    
    # Save last clause
    if current_clause:
        current_clause.content = '\n'.join(current_content).strip()
        current_clause.clause_type = _identify_clause_type(
            current_clause.title + " " + current_clause.content
        )
        clauses.append(current_clause)
    
    # Build hierarchy
    clauses = _build_clause_hierarchy(clauses)
    
    return clauses


def _match_clause_pattern(line: str) -> Optional[Tuple[int, str, str]]:
    """
    Match a line against clause patterns.
    
    Returns:
        Tuple of (level, clause_number, clause_title) or None
    """
    for level, patterns in CLAUSE_PATTERNS.items():
        level_num = int(level.split('_')[1])
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                num = groups.get('num', '')
                title = groups.get('title', '')
                return (level_num, num, title or '')
    
    return None


def _identify_clause_type(text: str) -> Optional[str]:
    """
    Identify the type of clause based on content.
    
    Args:
        text: Clause title and content
        
    Returns:
        Clause type or None
    """
    text_lower = text.lower()
    
    for clause_type, keywords in CLAUSE_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return clause_type
    
    return None


def _build_clause_hierarchy(clauses: List[Clause]) -> List[Clause]:
    """
    Build parent-child relationships between clauses.
    
    Args:
        clauses: Flat list of clauses
        
    Returns:
        List of top-level clauses with sub_clauses populated
    """
    if not clauses:
        return []
    
    result = []
    parent_stack = []  # Stack of (clause, level)
    
    for clause in clauses:
        # Pop until we find a suitable parent
        while parent_stack and parent_stack[-1][1] >= clause.level:
            parent_stack.pop()
        
        if parent_stack:
            # This is a sub-clause
            parent = parent_stack[-1][0]
            clause.parent_id = parent.id
            parent.sub_clauses.append(clause)
        else:
            # This is a top-level clause
            result.append(clause)
        
        # Push current clause as potential parent
        parent_stack.append((clause, clause.level))
    
    return result


def get_clause_by_type(clauses: List[Clause], clause_type: str) -> List[Clause]:
    """
    Get all clauses of a specific type.
    
    Args:
        clauses: List of clauses
        clause_type: Type to filter by
        
    Returns:
        Filtered list of clauses
    """
    result = []
    
    def search_recursive(clause_list: List[Clause]):
        for clause in clause_list:
            if clause.clause_type == clause_type:
                result.append(clause)
            search_recursive(clause.sub_clauses)
    
    search_recursive(clauses)
    return result


def clauses_to_dict(clauses: List[Clause]) -> List[dict]:
    """Convert list of clauses to list of dictionaries."""
    return [c.to_dict() for c in clauses]


def get_clause_summary(clauses: List[Clause]) -> Dict[str, int]:
    """
    Get a summary of clause types found.
    
    Args:
        clauses: List of clauses
        
    Returns:
        Dictionary mapping clause types to counts
    """
    summary = {}
    
    def count_recursive(clause_list: List[Clause]):
        for clause in clause_list:
            if clause.clause_type:
                summary[clause.clause_type] = summary.get(clause.clause_type, 0) + 1
            count_recursive(clause.sub_clauses)
    
    count_recursive(clauses)
    return summary
