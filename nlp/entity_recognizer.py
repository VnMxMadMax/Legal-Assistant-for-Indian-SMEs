"""
Named Entity Recognition Module for Contracts
Extracts parties, dates, amounts, and other legal entities
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Entity:
    """Represents an extracted entity."""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float = 1.0
    normalized_value: Any = None
    context: str = ""
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "normalized_value": self.normalized_value,
            "context": self.context
        }


# Entity patterns
ENTITY_PATTERNS = {
    "PARTY": [
        # Company names with common suffixes
        r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+(?:Private|Pvt\.?|Public|Ltd\.?|Limited|LLP|Inc\.?|Corp\.?|Corporation|Company|Co\.?|Associates|Enterprises|Solutions|Services|Technologies|Tech|Industries|Group)(?:\s+(?:Private|Pvt\.?|Ltd\.?|Limited))?)\b',
        # Quoted party names
        r'"([^"]+)"(?:\s*\([^)]*\))?(?=\s*(?:hereinafter|hereunder|referred to as|called))',
        # Party definitions: "ABC" (hereinafter referred to as)
        r'(?:hereinafter\s+(?:referred\s+to\s+as|called)\s*)["\'"]?([A-Za-z ]+)["\'"]?',
    ],
    "DATE": [
        # DD/MM/YYYY, DD-MM-YYYY
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
        # DD Month YYYY
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
        # Month DD, YYYY
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b',
        # YYYY-MM-DD (ISO format)
        r'\b(\d{4}-\d{2}-\d{2})\b',
    ],
    "MONEY": [
        # Symbols and Abbreviations
        r'(?:Rs\.?|INR|₹|Rupees?)\s*([\d,]*\d[\d,.]*)(?:/-)?(?:\s*\([^)]+\))?',
        r'(?:Rs\.?|INR|₹|Rupees?)\.\s*([\d,]*\d[\d,.]*)',
        
        # Suffix format: 1000 Rs, 500 Rupees
        r'([\d,]*\d[\d,.]*)\s*(?:Rs\.?|INR|₹|rupees?|rupee)',
        
        # Text Units: 5 Lakhs, 10 Crores
        r'(?:Rs\.?|INR|₹)?\s*([\d,.]*)\s*(?:lakhs?|lacs?|crores?|thousands?|millions?|billions?)(?:\s+rupees?)?',
        
        # Combined: Rs. 5 Lakhs, INR 10 Crores
        r'(?:Rs\.?|INR|₹)\s*([\d,.]*)\s*(?:lakhs?|lacs?|crores?|thousands?|millions?)',
        
        # Written amounts start with Rupees
        r'(?:Rupees?|Indian Rupees?)\s+([A-Za-z\s\-]+(?:Lakh|Lac|Crore|Thousand|Hundred|Only)[A-Za-z\s\-]*)',
        
        # Amounts in words followed by (Rs. X)
        r'([A-Za-z\s\-]+(?:Lakh|Lac|Crore|Thousand|Hundred)[A-Za-z\s\-]*)\s*\((?:Rs\.?|INR|₹)?\s*[\d,.]+\)',
    ],
    "JURISDICTION": [
        # Courts - limit to 4 words to avoid capturing full sentences
        r'(?:courts?\s+(?:of|in|at)\s+)([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})',
        r'(?:High Court of\s+)([A-Z][A-Za-z]+)',
        r'(?:District Court\s+(?:of|at)\s+)([A-Z][A-Za-z]+)',
        # Governing law - limit to 4 words
        r'(?:laws?\s+of\s+)([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})',
        r'(?:governed by\s+(?:the\s+)?laws?\s+of\s+)([A-Z][A-Za-z]+)',
        # City names for jurisdiction
        r'(?:jurisdiction\s+(?:of|in|at)\s+)([A-Z][A-Za-z]+)',
    ],
    "DURATION": [
        # X years/months/days
        r'\b(\d+)\s*(years?|months?|days?|weeks?)\b',
        # Period of X
        r'(?:period\s+of\s+)(\d+)\s*(years?|months?|days?)',
        # From X to Y
        r'(?:from\s+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s+(?:to|until|till)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    ],
    "PERCENTAGE": [
        r'\b(\d+(?:\.\d+)?)\s*(?:%|percent|per\s*cent)\b',
    ],
    "ADDRESS": [
        # Indian address patterns
        r'(?:at|located at|situated at|registered office at)\s+([^,]+,\s*[^,]+,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*[-–]\s*\d{6})',
        r'(?:having its\s+(?:registered\s+)?(?:office|address)\s+at)\s+([^.]+(?:\d{6}))',
    ]
}

# Indian states and cities for location matching
INDIAN_LOCATIONS = {
    "states": ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", 
               "Uttar Pradesh", "West Bengal", "Andhra Pradesh", "Telangana", "Kerala",
               "Madhya Pradesh", "Bihar", "Punjab", "Haryana", "Odisha", "Jharkhand"],
    "cities": ["Mumbai", "Delhi", "Bangalore", "Bengaluru", "Chennai", "Hyderabad", 
               "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh",
               "Noida", "Gurgaon", "Gurugram", "Kochi", "Thiruvananthapuram"]
}


def extract_entities(text: str) -> Dict[str, List[Entity]]:
    """
    Extract all named entities from contract text.
    
    Args:
        text: The contract text
        
    Returns:
        Dictionary mapping entity types to lists of extracted entities
    """
    entities = {entity_type: [] for entity_type in ENTITY_PATTERNS.keys()}
    
    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity_text = match.group(1) if match.lastindex else match.group(0)
                
                # Validation filters
                clean_text = entity_text.strip().strip(".,;:\"'")
                
                # Filter out garbage matches
                if len(clean_text) < 2:
                    continue
                    
                # Fix for JURISDICTION noise
                if entity_type == "JURISDICTION":
                    lower_text = clean_text.lower()
                    if any(x in lower_text for x in ["India including the Indian","law", "contract", "agreement", "party", "parties", "court", "courts", "place", "order", "the Land and there"]):
                        continue
                    # Reject if it looks like a sentence (too many spaces)
                    if clean_text.count(" ") > 3:
                        continue
                        
                # Fix for MONEY noise - Mandatory currency indicator check
                if entity_type == "MONEY":
                    if clean_text.strip() in [",", ".", "-"]:
                        continue
                        
                    # Strict check: Must contain at least one currency indicator
                    # This filters out random numbers like "500" or "10,000" that aren't explicitly money
                    lower_val = clean_text.lower()
                    indicators = ["rs", "inr", "₹", "rupee", "lakh", "lac", "crore","rs.","Rs.","INR","Rs","Rs."]
                    if not any(ind in lower_val for ind in indicators):
                        continue
                
                # Get context
                start_ctx = max(0, match.start() - 30)
                end_ctx = min(len(text), match.end() + 30)
                context = text[start_ctx:end_ctx].strip()
                
                entity = Entity(
                    text=clean_text,
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    context=context
                )
                
                # Add normalized value for certain types
                if entity_type == "MONEY":
                    entity.normalized_value = _normalize_money(clean_text)
                    # Skip if normalization fails or yields 0/tiny values (likely noise)
                    if not entity.normalized_value or entity.normalized_value < 1:
                         continue
                elif entity_type == "DATE":
                    entity.normalized_value = _normalize_date(clean_text)
                
                entities[entity_type].append(entity)
    
    # Deduplicate entities
    for entity_type in entities:
        entities[entity_type] = _deduplicate_entities(entities[entity_type])
    
    return entities


def _normalize_money(money_str: str) -> Optional[float]:
    """Normalize monetary value to a float."""
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[Rs\.₹INR,\s]', '', money_str)
        cleaned = re.sub(r'/\-', '', cleaned)
        
        # Handle lakhs/crores
        multiplier = 1
        lower = money_str.lower()
        if 'crore' in lower:
            multiplier = 10000000
        elif 'lakh' in lower or 'lac' in lower:
            multiplier = 100000
        elif 'thousand' in lower:
            multiplier = 1000
        
        # Extract number
        num_match = re.search(r'[\d.]+', cleaned)
        if num_match:
            return float(num_match.group()) * multiplier
    except:
        pass
    return None


def _normalize_date(date_str: str) -> Optional[str]:
    """Normalize date to ISO format (YYYY-MM-DD)."""
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
        "%d %B %Y", "%B %d, %Y", "%B %d %Y",
        "%dst %B %Y", "%dnd %B %Y", "%drd %B %Y", "%dth %B %Y"
    ]
    
    # Clean ordinal suffixes
    cleaned = re.sub(r'(\d)(st|nd|rd|th)', r'\1', date_str)
    cleaned = cleaned.replace(',', '')
    
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None


def _deduplicate_entities(entities: List[Entity]) -> List[Entity]:
    """Remove duplicate entities (same text and type)."""
    seen = set()
    unique = []
    
    for entity in entities:
        key = (entity.text.lower().strip(), entity.entity_type)
        if key not in seen:
            seen.add(key)
            unique.append(entity)
    
    return unique


def get_parties(entities: Dict[str, List[Entity]]) -> List[str]:
    """Extract unique party names from entities."""
    parties = []
    for entity in entities.get("PARTY", []):
        name = entity.text.strip()
        if len(name) > 2 and name not in parties:
            parties.append(name)
    return parties


def get_key_dates(entities: Dict[str, List[Entity]]) -> List[dict]:
    """Extract and categorize key dates."""
    dates = []
    for entity in entities.get("DATE", []):
        dates.append({
            "date": entity.text,
            "normalized": entity.normalized_value,
            "context": entity.context
        })
    return dates


def get_financial_amounts(entities: Dict[str, List[Entity]]) -> List[dict]:
    """Extract financial amounts with context."""
    amounts = []
    for entity in entities.get("MONEY", []):
        amounts.append({
            "amount_text": entity.text,
            "normalized_value": entity.normalized_value,
            "context": entity.context
        })
    return sorted(amounts, key=lambda x: x.get("normalized_value") or 0, reverse=True)


def entities_to_dict(entities: Dict[str, List[Entity]]) -> Dict[str, List[dict]]:
    """Convert all entities to dictionary format."""
    return {
        entity_type: [e.to_dict() for e in entity_list]
        for entity_type, entity_list in entities.items()
    }
