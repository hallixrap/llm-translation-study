#!/usr/bin/env python3
"""
MedlinePlus Back-Translation Pipeline

This script runs the full back-translation evaluation pipeline on the extracted
MedlinePlus documents (vaccine VIS + cancer materials).

Pipeline:
1. Load English source documents from extracted_text/
2. Load professional translations for comparison
3. Run LLM translations (English → Target Language)
4. Run back-translations (Target Language → English)
5. Calculate metrics

Documents: 22 topics × 9 languages (English + 8 translations) = 198 PDFs
Translation pairs: 22 topics × 8 languages × 4 models = 704 pairs
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ACTIVE_MODELS, ACTIVE_LANGUAGES, LANGUAGES,
    TRANSLATIONS_DIR, logger
)
from translation_pipeline import (
    run_translation_pipeline, translate_with_retry,
    save_checkpoint, load_checkpoint, TranslationResult
)

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
EXTRACTED_DIR = BASE_DIR / "data" / "extracted_text"
OUTPUT_DIR = BASE_DIR / "output" / "medlineplus_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LANGUAGE MAPPING
# =============================================================================

# Map folder names to config language keys
FOLDER_TO_LANG_KEY = {
    "spanish": "spanish",
    "chinese": "chinese_simplified",
    "vietnamese": "vietnamese",
    "russian": "russian",
    "arabic": "arabic",
    "korean": "korean",
    "tagalog": "tagalog",
    "haitian_creole": "haitian_creole",
}

LANG_KEY_TO_FOLDER = {v: k for k, v in FOLDER_TO_LANG_KEY.items()}

# Topic name variations (English filename -> translation filename base)
TOPIC_VARIATIONS = {
    "meningococcal_acwy": "meningococcal",  # English has _acwy suffix, translations don't
}

# File prefix mapping for VIS translations
LANG_FILE_PREFIX = {
    "spanish": "spanish",
    "chinese": "chinese_simplified",
    "vietnamese": "vietnamese",
    "russian": "russian",
    "arabic": "arabic",
    "korean": "korean",
    "tagalog": "tagalog",
    "haitian_creole": "haitian_creole",
}

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MedlinePlusDocument:
    """Represents a single document with all language versions."""
    doc_id: str              # e.g., "immunize/hepatitis_b" or "cancer/breast-cancer"
    category: str            # "immunize" or "cancer"
    topic: str               # e.g., "hepatitis_b"
    english_text: str        # Original English text
    professional_translations: dict  # {lang_key: text}

    def to_dict(self):
        return asdict(self)


@dataclass
class ComparisonResult:
    """Stores comparison between LLM and professional translations."""
    doc_id: str
    model: str
    language: str
    english_original: str
    llm_translation: str
    professional_translation: str
    llm_back_translation: str
    professional_back_translation: str  # NEW: Back-translation of professional translation
    translation_time: float
    back_translation_time: float
    professional_back_translation_time: float  # NEW: Time for professional back-translation
    timestamp: str
    success: bool
    error_message: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# =============================================================================
# DOCUMENT LOADING
# =============================================================================

def load_all_documents() -> list[MedlinePlusDocument]:
    """Load all documents from the extracted_text directory."""
    documents = []

    for category in ["immunize", "cancer"]:
        category_dir = EXTRACTED_DIR / category
        if not category_dir.exists():
            logger.warning(f"Category directory not found: {category_dir}")
            continue

        # Get English documents
        english_dir = category_dir / "english"
        if not english_dir.exists():
            logger.warning(f"English directory not found: {english_dir}")
            continue

        for english_file in sorted(english_dir.glob("*.txt")):
            topic = english_file.stem
            doc_id = f"{category}/{topic}"

            # Load English text
            english_text = english_file.read_text(encoding='utf-8')

            # Load professional translations
            professional_translations = {}
            for folder_name, lang_key in FOLDER_TO_LANG_KEY.items():
                lang_dir = category_dir / folder_name

                # Get the file prefix for this language
                file_prefix = LANG_FILE_PREFIX.get(folder_name, folder_name)

                # Get topic name variation if exists
                trans_topic = TOPIC_VARIATIONS.get(topic, topic)

                # Handle filename variations for translations
                # VIS files have language prefix, cancer files don't
                possible_names = [
                    f"{file_prefix}_{trans_topic}.txt",  # e.g., spanish_meningococcal.txt
                    f"{file_prefix}_{topic}.txt",        # e.g., spanish_hepatitis_b.txt
                    f"{folder_name}_{trans_topic}.txt",  # e.g., haitian_creole_meningococcal.txt
                    f"{folder_name}_{topic}.txt",        # e.g., haitian_creole_hepatitis_b.txt
                    f"{trans_topic}.txt",                # e.g., meningococcal.txt (cancer style)
                    f"{topic}.txt",                      # e.g., hepatitis_b.txt (cancer style)
                ]

                trans_file = None
                for name in possible_names:
                    candidate = lang_dir / name
                    if candidate.exists():
                        trans_file = candidate
                        break

                if trans_file and trans_file.exists():
                    professional_translations[lang_key] = trans_file.read_text(encoding='utf-8')
                else:
                    logger.debug(f"No {lang_key} translation for {doc_id}")

            doc = MedlinePlusDocument(
                doc_id=doc_id,
                category=category,
                topic=topic,
                english_text=english_text,
                professional_translations=professional_translations
            )
            documents.append(doc)
            logger.info(f"Loaded: {doc_id} ({len(professional_translations)} translations)")

    logger.info(f"Loaded {len(documents)} documents total")
    return documents


# =============================================================================
# TRANSLATION PIPELINE
# =============================================================================

def run_comparison_pipeline(
    doc: MedlinePlusDocument,
    model_name: str,
    lang_key: str
) -> ComparisonResult:
    """
    Run translation and compare with professional translation.

    Steps:
    1. English → Target (LLM translation)
    2. Target → English (LLM back-translation)
    3. Professional Target → English (Professional back-translation) [NEW]
    4. Store all for metric calculation

    This enables three comparison angles:
    - Goal 1: LLM back-translation vs Original English
    - Goal 2: LLM translation vs Professional translation
    - Goal 3: Professional back-translation vs Original English (and vs LLM back-translation)
    """
    timestamp = datetime.now().isoformat()
    language_name = LANGUAGES[lang_key]["name"]

    logger.info(f"Processing: {doc.doc_id} | {model_name} | {language_name}")

    try:
        # Step 1: Forward translation (English → Target)
        start_time = time.time()
        llm_translation = translate_with_retry(
            text=doc.english_text,
            target_language=language_name,
            model_name=model_name,
            is_back_translation=False
        )
        translation_time = time.time() - start_time
        logger.info(f"  Forward translation: {translation_time:.2f}s")

        # Rate limiting
        time.sleep(1)

        # Step 2: Back translation of LLM output (Target → English)
        start_time = time.time()
        llm_back_translation = translate_with_retry(
            text=llm_translation,
            target_language="English",
            model_name=model_name,
            is_back_translation=True,
            source_language=language_name
        )
        back_translation_time = time.time() - start_time
        logger.info(f"  LLM back-translation: {back_translation_time:.2f}s")

        # Get professional translation for comparison
        professional_translation = doc.professional_translations.get(lang_key, "")

        # Step 3: Back translation of PROFESSIONAL translation (Target → English) [NEW]
        professional_back_translation = ""
        professional_back_translation_time = 0.0

        if professional_translation:
            time.sleep(1)  # Rate limiting
            start_time = time.time()
            professional_back_translation = translate_with_retry(
                text=professional_translation,
                target_language="English",
                model_name=model_name,
                is_back_translation=True,
                source_language=language_name
            )
            professional_back_translation_time = time.time() - start_time
            logger.info(f"  Professional back-translation: {professional_back_translation_time:.2f}s")

        return ComparisonResult(
            doc_id=doc.doc_id,
            model=model_name,
            language=lang_key,
            english_original=doc.english_text,
            llm_translation=llm_translation,
            professional_translation=professional_translation,
            llm_back_translation=llm_back_translation,
            professional_back_translation=professional_back_translation,
            translation_time=translation_time,
            back_translation_time=back_translation_time,
            professional_back_translation_time=professional_back_translation_time,
            timestamp=timestamp,
            success=True
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {doc.doc_id} | {model_name} | {language_name}: {e}")
        return ComparisonResult(
            doc_id=doc.doc_id,
            model=model_name,
            language=lang_key,
            english_original=doc.english_text,
            llm_translation="",
            professional_translation=doc.professional_translations.get(lang_key, ""),
            llm_back_translation="",
            professional_back_translation="",
            translation_time=0,
            back_translation_time=0,
            professional_back_translation_time=0,
            timestamp=timestamp,
            success=False,
            error_message=str(e)
        )


def save_results(results: list[ComparisonResult], filename: str):
    """Save results to JSON."""
    filepath = OUTPUT_DIR / filename
    data = [r.to_dict() for r in results]

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(results)} results to {filepath}")
    return filepath


def load_results(filename: str) -> list[ComparisonResult]:
    """Load results from JSON."""
    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [ComparisonResult(**d) for d in data]


# =============================================================================
# BATCH PROCESSING WITH RESUME
# =============================================================================

def get_checkpoint_key(doc_id: str, model: str, lang: str) -> str:
    """Create unique key for checkpoint tracking."""
    return f"{doc_id}|{model}|{lang}"


def run_full_pipeline(
    models: list[str] = None,
    languages: list[str] = None,
    resume: bool = True
):
    """
    Run the full translation pipeline on all documents.

    Args:
        models: List of model names (defaults to ACTIVE_MODELS)
        languages: List of language keys (defaults to ACTIVE_LANGUAGES)
        resume: Whether to resume from checkpoint
    """
    models = models or ACTIVE_MODELS
    languages = languages or ACTIVE_LANGUAGES

    # Load documents
    documents = load_all_documents()

    # Calculate total work
    total = len(documents) * len(models) * len(languages)
    logger.info(f"Total combinations: {total}")
    logger.info(f"  Documents: {len(documents)}")
    logger.info(f"  Models: {models}")
    logger.info(f"  Languages: {languages}")

    # Load checkpoint if resuming
    checkpoint_file = OUTPUT_DIR / "checkpoint.json"
    completed = set()
    results = []

    if resume and checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        completed = set(checkpoint.get("completed", []))
        results = load_results("all_results.json")
        logger.info(f"Resuming: {len(completed)} already completed")

    # Process each combination
    completed_count = len(completed)

    for doc in documents:
        for model in models:
            for lang in languages:
                key = get_checkpoint_key(doc.doc_id, model, lang)

                # Skip if already done
                if key in completed:
                    continue

                # Run pipeline
                result = run_comparison_pipeline(doc, model, lang)
                results.append(result)
                completed.add(key)
                completed_count += 1

                # Progress update
                progress = (completed_count / total) * 100
                logger.info(f"Progress: {completed_count}/{total} ({progress:.1f}%)")

                # Save checkpoint periodically
                if completed_count % 5 == 0:
                    save_results(results, "all_results.json")
                    with open(checkpoint_file, 'w') as f:
                        json.dump({"completed": list(completed)}, f)

                # Rate limiting between calls
                time.sleep(1)

    # Final save
    save_results(results, "all_results.json")
    with open(checkpoint_file, 'w') as f:
        json.dump({"completed": list(completed)}, f)

    logger.info(f"Pipeline complete! {len(results)} total results")
    return results


# =============================================================================
# SINGLE MODEL/LANGUAGE TEST
# =============================================================================

def test_single(
    model: str = "gpt-5.1",
    language: str = "spanish",
    doc_index: int = 0
):
    """Test a single document/model/language combination."""
    documents = load_all_documents()

    if doc_index >= len(documents):
        logger.error(f"Invalid doc_index: {doc_index}. Max: {len(documents)-1}")
        return None

    doc = documents[doc_index]
    logger.info(f"\n{'='*60}")
    logger.info(f"TEST: {doc.doc_id} | {model} | {language}")
    logger.info(f"{'='*60}")

    result = run_comparison_pipeline(doc, model, language)

    if result.success:
        logger.info(f"\n--- ORIGINAL (English) ---")
        logger.info(result.english_original[:500] + "...")
        logger.info(f"\n--- LLM TRANSLATION ({language}) ---")
        logger.info(result.llm_translation[:500] + "...")
        logger.info(f"\n--- PROFESSIONAL TRANSLATION ({language}) ---")
        logger.info(result.professional_translation[:500] + "...")
        logger.info(f"\n--- BACK TRANSLATION (English) ---")
        logger.info(result.llm_back_translation[:500] + "...")
    else:
        logger.error(f"Test failed: {result.error_message}")

    return result


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MedlinePlus Back-Translation Pipeline")
    parser.add_argument("--test", action="store_true", help="Run single test")
    parser.add_argument("--model", default="gpt-5.1", help="Model for test")
    parser.add_argument("--language", default="spanish", help="Language for test")
    parser.add_argument("--doc", type=int, default=0, help="Document index for test")
    parser.add_argument("--run", action="store_true", help="Run full pipeline")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh (don't resume)")
    parser.add_argument("--models", nargs="+", help="Specific models to run")
    parser.add_argument("--languages", nargs="+", help="Specific languages to run")
    parser.add_argument("--list-docs", action="store_true", help="List all documents")

    args = parser.parse_args()

    if args.list_docs:
        docs = load_all_documents()
        for i, doc in enumerate(docs):
            langs = list(doc.professional_translations.keys())
            print(f"{i}: {doc.doc_id} ({len(langs)} translations)")
    elif args.test:
        test_single(args.model, args.language, args.doc)
    elif args.run:
        run_full_pipeline(
            models=args.models,
            languages=args.languages,
            resume=not args.no_resume
        )
    else:
        print("""
MedlinePlus Back-Translation Pipeline

Usage:
  python run_medlineplus_pipeline.py --list-docs           # List all documents
  python run_medlineplus_pipeline.py --test               # Test single translation
  python run_medlineplus_pipeline.py --test --model claude-opus-4.5 --language chinese_simplified
  python run_medlineplus_pipeline.py --run                # Run full pipeline
  python run_medlineplus_pipeline.py --run --models gpt-5.1 claude-opus-4.5
  python run_medlineplus_pipeline.py --run --no-resume    # Start fresh

Models: gpt-5.1, claude-opus-4.5, gemini-3-pro, kimi-k2
Languages: spanish, chinese_simplified, vietnamese, russian, arabic, korean, tagalog, haitian_creole
        """)
