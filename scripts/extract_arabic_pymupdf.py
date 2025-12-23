#!/usr/bin/env python3
"""
Re-extract Arabic PDFs using pymupdf (fitz) for proper RTL text handling.
"""

import fitz  # pymupdf
from pathlib import Path
import unicodedata
import re

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
PDF_DIR = BASE_DIR / "data" / "pdfs"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_text"

def reverse_arabic_words(text: str) -> str:
    """
    Reverse Arabic text that was extracted in wrong order.
    Preserves English/numbers in correct order.
    """
    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        # Check if line has significant Arabic content
        arabic_chars = sum(1 for c in line if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')

        if arabic_chars > len(line) * 0.3:  # More than 30% Arabic
            # Split into words, reverse the order of Arabic segments
            words = line.split()
            # Reverse word order for RTL
            words = words[::-1]
            line = ' '.join(words)

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def extract_arabic_text(pdf_path: Path) -> str:
    """Extract text from Arabic PDF with proper RTL handling."""
    doc = fitz.open(pdf_path)
    text_parts = []

    for page in doc:
        # Try extracting as dict to get proper text blocks
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        page_text = []
        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text.strip():
                        page_text.append(line_text)

        text_parts.append('\n'.join(page_text))

    doc.close()

    full_text = "\n\n".join(text_parts)

    # Apply RTL word-order fix
    return reverse_arabic_words(full_text)

def main():
    # Find all Arabic PDFs
    categories = ["immunize", "cancer"]
    extracted = 0

    for category in categories:
        pdf_folder = PDF_DIR / category / "arabic"
        output_folder = OUTPUT_DIR / category / "arabic"

        if not pdf_folder.exists():
            print(f"Folder not found: {pdf_folder}")
            continue

        output_folder.mkdir(parents=True, exist_ok=True)

        for pdf_file in sorted(pdf_folder.glob("*.pdf")):
            print(f"Extracting: {pdf_file.name}")

            try:
                text = extract_arabic_text(pdf_file)

                # Save with same naming convention
                output_file = output_folder / f"{pdf_file.stem}.txt"
                output_file.write_text(text, encoding='utf-8')

                extracted += 1
                print(f"  -> {output_file.name} ({len(text)} chars)")

            except Exception as e:
                print(f"  ERROR: {e}")

    print(f"\nExtracted {extracted} Arabic PDFs")

if __name__ == "__main__":
    main()
