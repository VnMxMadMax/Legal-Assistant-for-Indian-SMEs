"""
File Handlers for extracting text from various document formats
Supports: PDF, DOCX, DOC, TXT
"""
import os
from typing import Optional, Tuple
import pdfplumber
from docx import Document


def extract_from_pdf(file_path: str) -> Tuple[str, dict]:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    text_content = []
    metadata = {
        "pages": 0,
        "format": "pdf"
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            metadata["pages"] = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    return "\n\n".join(text_content), metadata


def extract_from_pdf_bytes(file_bytes) -> Tuple[str, dict]:
    """
    Extract text from PDF bytes (for Streamlit uploads).
    
    Args:
        file_bytes: BytesIO object containing PDF data
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    text_content = []
    metadata = {
        "pages": 0,
        "format": "pdf"
    }
    
    try:
        with pdfplumber.open(file_bytes) as pdf:
            metadata["pages"] = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    return "\n\n".join(text_content), metadata


def extract_from_docx(file_path: str) -> Tuple[str, dict]:
    """
    Extract text from DOCX file.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    text_content = []
    metadata = {
        "paragraphs": 0,
        "format": "docx"
    }
    
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text)
        metadata["paragraphs"] = len(text_content)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    return "\n\n".join(text_content), metadata


def extract_from_docx_bytes(file_bytes) -> Tuple[str, dict]:
    """
    Extract text from DOCX bytes (for Streamlit uploads).
    
    Args:
        file_bytes: BytesIO object containing DOCX data
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    text_content = []
    metadata = {
        "paragraphs": 0,
        "format": "docx"
    }
    
    try:
        doc = Document(file_bytes)
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text)
        metadata["paragraphs"] = len(text_content)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    return "\n\n".join(text_content), metadata


def extract_from_txt(file_path: str) -> Tuple[str, dict]:
    """
    Extract text from TXT file.
    
    Args:
        file_path: Path to the TXT file
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    metadata = {
        "lines": 0,
        "format": "txt"
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        metadata["lines"] = len(content.split('\n'))
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        metadata["lines"] = len(content.split('\n'))
    except Exception as e:
        raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    return content, metadata


def extract_from_txt_bytes(file_bytes) -> Tuple[str, dict]:
    """
    Extract text from TXT bytes (for Streamlit uploads).
    
    Args:
        file_bytes: BytesIO object containing TXT data
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    metadata = {
        "lines": 0,
        "format": "txt"
    }
    
    try:
        content = file_bytes.getvalue().decode('utf-8')
        metadata["lines"] = len(content.split('\n'))
    except UnicodeDecodeError:
        content = file_bytes.getvalue().decode('latin-1')
        metadata["lines"] = len(content.split('\n'))
    except Exception as e:
        raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    return content, metadata


def extract_text(file_path: Optional[str] = None, 
                 file_bytes=None, 
                 file_extension: str = "") -> Tuple[str, dict]:
    """
    Unified text extraction from various file formats.
    
    Args:
        file_path: Path to the file (for file-based extraction)
        file_bytes: BytesIO object (for upload-based extraction)
        file_extension: File extension (required when using file_bytes)
        
    Returns:
        Tuple of (extracted_text, metadata)
    """
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return extract_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return extract_from_docx(file_path)
        elif ext == '.txt':
            return extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    elif file_bytes:
        ext = file_extension.lower()
        
        if ext == '.pdf':
            return extract_from_pdf_bytes(file_bytes)
        elif ext in ['.docx', '.doc']:
            return extract_from_docx_bytes(file_bytes)
        elif ext == '.txt':
            return extract_from_txt_bytes(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    else:
        raise ValueError("Either file_path or file_bytes must be provided")
