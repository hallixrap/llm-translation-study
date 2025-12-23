#!/usr/bin/env python3
"""
Extract text from DOCX files converted from PDFs via Adobe Acrobat.

This script:
1. Finds all .docx files in the PDF folders
2. Extracts text with proper paragraph ordering
3. Cleans up common extraction artifacts
4. Saves as .txt files in the extracted_text folder

Usage:
    python scripts/extract_from_docx.py

The script expects DOCX files to be placed alongside the original PDFs in:
    data/pdfs/{category}/{language}/*.docx

Output will be saved to:
    data/extracted_text/{category}/{language}/*.txt
"""

import re
from pathlib import Path
from docx import Document

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
PDF_DIR = BASE_DIR / "data" / "pdfs"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_text"


def clean_text(text: str) -> str:
    """Clean up common extraction artifacts from DOCX text."""

    # Fix spaced-out letters in headers (e.g., "VACCIN E" -> "VACCINE")
    # Common patterns from PDF->DOCX conversion
    text = re.sub(r'VACCIN\s+E\s+INFORMATIO\s+N\s+STATEMENT', 'VACCINE INFORMATION STATEMENT', text)
    text = re.sub(r'INFORMATIO\s+N', 'INFORMATION', text)
    text = re.sub(r'VACCIN\s+E', 'VACCINE', text)

    # Remove excessive whitespace
    text = re.sub(r'\t+', ' ', text)  # tabs to single space
    text = re.sub(r'  +', ' ', text)  # multiple spaces to single
    text = re.sub(r'\n{3,}', '\n\n', text)  # max 2 newlines

    # Clean up lines
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def extract_docx(docx_path: Path) -> str:
    """Extract text from a DOCX file."""
    doc = Document(docx_path)

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # Join paragraphs with newlines
    full_text = '\n'.join(paragraphs)

    # Clean up the text
    full_text = clean_text(full_text)

    return full_text


def get_output_filename(docx_path: Path, category: str, language: str) -> str:
    """
    Determine the output filename based on the docx filename.

    Handles various naming conventions:
    - hepatitis_b.docx -> hepatitis_b.txt (English)
    - spanish_hepatitis_b.docx -> spanish_hepatitis_b.txt
    - after-a-breast-cancer-diagnosis.docx -> after-a-breast-cancer-diagnosis.txt
    """
    stem = docx_path.stem

    # Remove "_final" suffix if present
    stem = re.sub(r'_final$', '', stem)

    return f"{stem}.txt"


def process_all_docx():
    """Find and process all DOCX files."""

    categories = ["immunize", "cancer"]
    languages = ["english", "spanish", "chinese", "vietnamese", "russian",
                 "arabic", "korean", "tagalog", "haitian_creole"]

    total_processed = 0
    total_errors = 0

    print("=" * 60)
    print("DOCX Text Extraction")
    print("=" * 60)

    for category in categories:
        for language in languages:
            lang_dir = PDF_DIR / category / language

            if not lang_dir.exists():
                continue

            # Find all DOCX files
            docx_files = list(lang_dir.glob("*.docx"))

            if not docx_files:
                continue

            print(f"\n{category}/{language}: Found {len(docx_files)} DOCX files")

            # Create output directory
            output_dir = OUTPUT_DIR / category / language
            output_dir.mkdir(parents=True, exist_ok=True)

            for docx_path in sorted(docx_files):
                try:
                    # Extract text
                    text = extract_docx(docx_path)

                    # Determine output filename
                    output_filename = get_output_filename(docx_path, category, language)
                    output_path = output_dir / output_filename

                    # Save
                    output_path.write_text(text, encoding='utf-8')

                    print(f"  ✓ {docx_path.name} -> {output_filename} ({len(text)} chars)")
                    total_processed += 1

                except Exception as e:
                    print(f"  ✗ {docx_path.name}: ERROR - {e}")
                    total_errors += 1

    print("\n" + "=" * 60)
    print(f"Done! Processed: {total_processed}, Errors: {total_errors}")
    print("=" * 60)


def process_single_docx(docx_path: str):
    """Process a single DOCX file and print the extracted text."""
    path = Path(docx_path)

    if not path.exists():
        print(f"File not found: {path}")
        return

    text = extract_docx(path)
    print(f"Extracted {len(text)} characters from {path.name}")
    print("-" * 40)
    print(text[:2000])
    if len(text) > 2000:
        print(f"\n... ({len(text) - 2000} more characters)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Process single file
        process_single_docx(sys.argv[1])
    else:
        # Process all DOCX files
        process_all_docx()
