#!/usr/bin/env python3
"""
Extract text from all PDFs in the data/pdfs directory.
Saves extracted text to data/extracted_text/ with same folder structure.
"""

import os
import pdfplumber
from pathlib import Path

# Paths
BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
PDF_DIR = BASE_DIR / "data" / "pdfs"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_text"

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"  ERROR extracting {pdf_path.name}: {e}")
        return ""
    return "\n\n".join(text_parts)

def process_all_pdfs():
    """Process all PDFs and save extracted text."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_pdfs = 0
    successful = 0
    failed = []

    # Process each category (immunize, cancer)
    for category in ["immunize", "cancer"]:
        category_dir = PDF_DIR / category
        if not category_dir.exists():
            continue

        # Process each language folder
        for lang_dir in sorted(category_dir.iterdir()):
            if not lang_dir.is_dir() or lang_dir.name.startswith('.'):
                continue

            language = lang_dir.name

            # Create output language folder
            output_lang_dir = OUTPUT_DIR / category / language
            output_lang_dir.mkdir(parents=True, exist_ok=True)

            # Process each PDF
            for pdf_file in sorted(lang_dir.glob("*.pdf")):
                total_pdfs += 1

                # Extract text
                print(f"Processing: {category}/{language}/{pdf_file.name}")
                text = extract_text_from_pdf(pdf_file)

                if text.strip():
                    # Save as .txt file
                    output_file = output_lang_dir / f"{pdf_file.stem}.txt"
                    output_file.write_text(text, encoding='utf-8')
                    successful += 1
                    print(f"  ✓ Saved {len(text)} chars")
                else:
                    failed.append(f"{category}/{language}/{pdf_file.name}")
                    print(f"  ✗ No text extracted")

    # Print summary
    print("\n" + "="*50)
    print(f"EXTRACTION COMPLETE")
    print(f"="*50)
    print(f"Total PDFs: {total_pdfs}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"\nFailed files:")
        for f in failed:
            print(f"  - {f}")

    return successful, failed

if __name__ == "__main__":
    process_all_pdfs()
