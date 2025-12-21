"""
Book parsing utilities for Text To BOOK.
Supports EPUB, PDF, and TXT file formats.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def parse_txt(path: Path) -> str:
    """Parse a plain text file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to parse TXT: {e}")
        raise ValueError(f"Could not read TXT file: {e}")


def parse_epub(path: Path) -> str:
    """
    Parse an EPUB file and extract text content.
    Returns concatenated text from all chapters.
    """
    try:
        from ebooklib import epub, ITEM_DOCUMENT
        from bs4 import BeautifulSoup  # ebooklib uses html content
    except ImportError:
        raise ImportError("ebooklib and beautifulsoup4 are required for EPUB parsing")
    
    try:
        book = epub.read_epub(str(path))
        chapters = []
        
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                # Parse HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                if text:
                    chapters.append(text)
        
        full_text = '\n\n'.join(chapters)
        logger.info(f"Parsed EPUB: {len(chapters)} chapters, {len(full_text)} chars")
        return full_text
    except Exception as e:
        logger.error(f"Failed to parse EPUB: {e}")
        raise ValueError(f"Could not parse EPUB file: {e}")


def parse_pdf(path: Path) -> str:
    """
    Parse a PDF file and extract text content.
    Returns concatenated text from all pages.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing")
    
    try:
        pages_text = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        
        full_text = '\n\n'.join(pages_text)
        logger.info(f"Parsed PDF: {len(pages_text)} pages, {len(full_text)} chars")
        return full_text
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise ValueError(f"Could not parse PDF file: {e}")


def parse_book(path: Path) -> str:
    """
    Auto-detect file type and parse accordingly.
    
    Args:
        path: Path to the book file
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file type is not supported or parsing fails
    """
    suffix = path.suffix.lower()
    
    if suffix == '.txt':
        return parse_txt(path)
    elif suffix == '.epub':
        return parse_epub(path)
    elif suffix == '.pdf':
        return parse_pdf(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
