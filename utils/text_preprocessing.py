"""
Text Preprocessing Utilities for Contract Analysis
"""
import re
from typing import List, Tuple
from langdetect import detect, LangDetectException


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers (common patterns)
    text = re.sub(r'\bPage\s*\d+\s*(of\s*\d+)?\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\s*/\s*\d+\b', '', text)
    
    # Remove common headers/footers
    text = re.sub(r'(CONFIDENTIAL|DRAFT|PRIVILEGED)', '', text, flags=re.IGNORECASE)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def segment_paragraphs(text: str) -> List[str]:
    """
    Segment text into paragraphs.
    
    Args:
        text: Input text
        
    Returns:
        List of paragraphs
    """
    # Split by double newlines or numbered sections
    paragraphs = re.split(r'\n\n+|\n(?=\d+\.)', text)
    
    # Clean and filter empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs


def detect_language(text: str) -> str:
    """
    Detect the primary language of the text.
    
    Args:
        text: Input text
        
    Returns:
        Language code ('en', 'hi', or 'unknown')
    """
    try:
        # Use a sample of text for detection
        sample = text[:1000] if len(text) > 1000 else text
        lang = detect(sample)
        
        if lang in ['en', 'hi']:
            return lang
        return 'en'  # Default to English for unsupported languages
    except LangDetectException:
        return 'unknown'


def is_hindi_text(text: str) -> bool:
    """
    Check if text contains Hindi/Devanagari script.
    
    Args:
        text: Input text
        
    Returns:
        True if text contains Hindi
    """
    # Check for Devanagari Unicode range
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    return bool(devanagari_pattern.search(text))


def extract_sections(text: str) -> List[Tuple[str, str]]:
    """
    Extract sections/clauses from contract text.
    
    Args:
        text: Contract text
        
    Returns:
        List of tuples (section_header, section_content)
    """
    sections = []
    
    # Common section patterns
    patterns = [
        # Numbered sections: 1. Section Name, 1) Section Name
        r'(?:^|\n)\s*(\d+[\.\)]\s*[A-Z][A-Za-z\s]+)',
        # Lettered sections: (a) Section Name, a. Section Name
        r'(?:^|\n)\s*\(([a-z])\)\s*([A-Z][A-Za-z\s]+)',
        # Roman numerals: (i) Section, (ii) Section
        r'(?:^|\n)\s*\((i{1,3}|iv|v|vi{0,3}|ix|x)\)\s*([A-Z][A-Za-z\s]+)',
        # Article/Section/Clause headers
        r'(?:^|\n)\s*((?:Article|Section|Clause|ARTICLE|SECTION|CLAUSE)\s*\d*[:\.\s]*[A-Za-z\s]*)',
    ]
    
    # Find all potential section headers
    all_matches = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        for match in matches:
            all_matches.append((match.start(), match.group(0).strip()))
    
    # Sort by position
    all_matches.sort(key=lambda x: x[0])
    
    # Extract sections with content
    for i, (pos, header) in enumerate(all_matches):
        # Get content until next section or end
        if i + 1 < len(all_matches):
            next_pos = all_matches[i + 1][0]
            content = text[pos:next_pos].strip()
        else:
            content = text[pos:].strip()
        
        # Remove header from content
        content = content[len(header):].strip()
        sections.append((header, content))
    
    return sections


def normalize_dates(text: str) -> str:
    """
    Normalize various date formats to standard format.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized dates
    """
    # Common Indian date formats
    patterns = [
        # DD/MM/YYYY or DD-MM-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', r'\3-\2-\1'),
        # DD Month YYYY
        (r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', 
         lambda m: f"{m.group(3)}-{_month_to_num(m.group(2)):02d}-{int(m.group(1)):02d}"),
    ]
    
    for pattern, replacement in patterns:
        if callable(replacement):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        else:
            text = re.sub(pattern, replacement, text)
    
    return text


def _month_to_num(month: str) -> int:
    """Convert month name to number."""
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    return months.get(month.lower(), 1)


def extract_monetary_values(text: str) -> List[dict]:
    """
    Extract monetary values from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted monetary values with context
    """
    values = []
    
    # Patterns for Indian currency
    patterns = [
        # Rs. 1,00,000 or INR 1,00,000
        r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:(?:lakhs?|lacs?|crores?|thousands?|L|Cr|K))?',
        # 1,00,000 Rs or rupees
        r'([\d,]+(?:\.\d{2})?)\s*(?:Rs\.?|INR|₹|rupees?)',
        # Words: One Lakh, Ten Crore
        r'((?:one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|hundred)\s*(?:lakh|lac|crore|thousand)s?)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get context (surrounding text)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            values.append({
                "value": match.group(0),
                "raw_amount": match.group(1) if match.lastindex else match.group(0),
                "context": context,
                "position": match.start()
            })
    
    return values
