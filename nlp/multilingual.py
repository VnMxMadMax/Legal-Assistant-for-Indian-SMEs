"""
Multilingual Support Module
Handles Hindi text detection and translation
"""
import re
from typing import Tuple, List, Optional
from langdetect import detect, LangDetectException


# Devanagari Unicode range
DEVANAGARI_RANGE = (0x0900, 0x097F)

# Common Hindi legal terms with English translations
HINDI_LEGAL_TERMS = {
    "अनुबंध": "contract",
    "समझौता": "agreement",
    "पक्ष": "party",
    "नियम": "terms",
    "शर्तें": "conditions",
    "भुगतान": "payment",
    "राशि": "amount",
    "अवधि": "duration",
    "समाप्ति": "termination",
    "विवाद": "dispute",
    "मध्यस्थता": "arbitration",
    "क्षेत्राधिकार": "jurisdiction",
    "गोपनीयता": "confidentiality",
    "दायित्व": "liability",
    "क्षतिपूर्ति": "indemnity",
    "हस्ताक्षर": "signature",
    "साक्षी": "witness",
    "कार्यकाल": "tenure",
    "वेतन": "salary",
    "मालिक": "owner",
    "किरायेदार": "tenant",
    "किराया": "rent",
    "जमानत": "security deposit",
    "नोटिस": "notice",
    "संपत्ति": "property",
    "अधिकार": "rights",
    "कर्तव्य": "duties",
    "प्रतिबंध": "restrictions",
    "उल्लंघन": "breach",
    "दंड": "penalty"
}


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of the text.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (language_code, confidence)
    """
    # Check for Devanagari characters
    hindi_char_count = sum(1 for char in text if DEVANAGARI_RANGE[0] <= ord(char) <= DEVANAGARI_RANGE[1])
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return ('unknown', 0.0)
    
    hindi_ratio = hindi_char_count / total_chars if total_chars > 0 else 0
    
    if hindi_ratio > 0.5:
        return ('hi', hindi_ratio)
    elif hindi_ratio > 0:
        return ('mixed', max(hindi_ratio, 1 - hindi_ratio))
    
    try:
        lang = detect(text[:1000])
        return (lang, 0.8)
    except LangDetectException:
        return ('unknown', 0.0)


def is_hindi(text: str) -> bool:
    """Check if text contains significant Hindi content."""
    lang, conf = detect_language(text)
    return lang in ['hi', 'mixed'] and conf > 0.3


def contains_devanagari(text: str) -> bool:
    """Check if text contains Devanagari script."""
    pattern = re.compile(r'[\u0900-\u097F]')
    return bool(pattern.search(text))


def extract_hindi_segments(text: str) -> List[dict]:
    """
    Extract Hindi segments from mixed language text.
    
    Args:
        text: Input text
        
    Returns:
        List of segments with language info
    """
    segments = []
    current_segment = ""
    current_lang = None
    
    words = text.split()
    
    for word in words:
        is_hindi_word = contains_devanagari(word)
        word_lang = 'hi' if is_hindi_word else 'en'
        
        if current_lang is None:
            current_lang = word_lang
            current_segment = word
        elif word_lang == current_lang:
            current_segment += " " + word
        else:
            segments.append({
                'text': current_segment.strip(),
                'language': current_lang
            })
            current_lang = word_lang
            current_segment = word
    
    if current_segment:
        segments.append({
            'text': current_segment.strip(),
            'language': current_lang
        })
    
    return segments


def replace_common_hindi_terms(text: str) -> str:
    """
    Replace common Hindi legal terms with English equivalents.
    
    Args:
        text: Hindi text
        
    Returns:
        Text with common terms translated
    """
    result = text
    for hindi, english in HINDI_LEGAL_TERMS.items():
        result = result.replace(hindi, f"{hindi} ({english})")
    return result


def prepare_for_translation(text: str) -> str:
    """
    Prepare Hindi text for LLM translation.
    
    Args:
        text: Hindi text
        
    Returns:
        Preprocessed text
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Add markers for numbers and amounts to preserve during translation
    text = re.sub(r'₹\s*(\d+)', r'[AMOUNT: ₹\1]', text)
    text = re.sub(r'(\d+)\s*रुपये', r'[AMOUNT: \1 rupees]', text)
    
    # Mark dates
    text = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', r'[DATE: \1]', text)
    
    return text.strip()


def get_translation_prompt(hindi_text: str) -> str:
    """
    Generate a prompt for LLM translation.
    
    Args:
        hindi_text: Hindi text to translate
        
    Returns:
        Translation prompt
    """
    preprocessed = prepare_for_translation(hindi_text)
    
    prompt = f"""Translate the following Hindi legal contract text to English. 
Maintain legal terminology accuracy and preserve:
- All dates (marked as [DATE: ...])
- All amounts (marked as [AMOUNT: ...])
- Party names
- Proper nouns

Hindi Text:
{preprocessed}

Provide a clear, professional English translation suitable for legal review:"""
    
    return prompt


def format_bilingual_output(english_text: str, hindi_text: Optional[str] = None) -> dict:
    """
    Format output for bilingual display.
    
    Args:
        english_text: English text
        hindi_text: Optional Hindi original
        
    Returns:
        Formatted output dictionary
    """
    return {
        "english": english_text,
        "hindi": hindi_text,
        "has_hindi_original": hindi_text is not None and len(hindi_text) > 0
    }


def get_language_stats(text: str) -> dict:
    """
    Get language statistics for a document.
    
    Args:
        text: Document text
        
    Returns:
        Language statistics
    """
    lang, confidence = detect_language(text)
    
    segments = extract_hindi_segments(text)
    hindi_words = sum(len(s['text'].split()) for s in segments if s['language'] == 'hi')
    english_words = sum(len(s['text'].split()) for s in segments if s['language'] == 'en')
    total_words = hindi_words + english_words
    
    return {
        "primary_language": lang,
        "confidence": confidence,
        "hindi_word_count": hindi_words,
        "english_word_count": english_words,
        "total_words": total_words,
        "hindi_percentage": (hindi_words / total_words * 100) if total_words > 0 else 0,
        "english_percentage": (english_words / total_words * 100) if total_words > 0 else 0,
        "is_bilingual": lang == 'mixed',
        "requires_translation": hindi_words > 0
    }
