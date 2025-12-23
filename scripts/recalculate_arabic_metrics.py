#!/usr/bin/env python3
"""
Re-calculate Arabic metrics using the newly extracted professional translations.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import logger

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted_text"


def load_arabic_translations():
    """Load the newly extracted Arabic professional translations."""
    translations = {}

    for category in ["immunize", "cancer"]:
        arabic_dir = EXTRACTED_DIR / category / "arabic"
        if not arabic_dir.exists():
            continue

        for txt_file in arabic_dir.glob("*.txt"):
            text = txt_file.read_text(encoding='utf-8')

            # Map filename to doc_id
            # immunize: arabic_hepatitis_b.txt -> immunize/hepatitis_b
            # cancer: after-a-breast-cancer-diagnosis.txt -> cancer/after-a-breast-cancer-diagnosis
            if category == "immunize":
                # Remove arabic_ prefix
                topic = txt_file.stem.replace("arabic_", "")
            else:
                topic = txt_file.stem

            doc_id = f"{category}/{topic}"
            translations[doc_id] = text
            logger.info(f"Loaded: {doc_id} ({len(text)} chars)")

    return translations


def update_results_with_arabic():
    """Update the results file with corrected Arabic professional translations."""
    # Load existing results
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Load new Arabic translations
    arabic_translations = load_arabic_translations()
    logger.info(f"Loaded {len(arabic_translations)} Arabic translations")

    # Update Arabic entries
    updated = 0
    for result in results:
        if result['language'] == 'arabic':
            doc_id = result['doc_id']
            if doc_id in arabic_translations:
                result['professional_translation'] = arabic_translations[doc_id]
                updated += 1

    logger.info(f"Updated {updated} Arabic entries in results")

    # Save updated results
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved updated results to {RESULTS_FILE}")
    return updated


def recalculate_arabic_metrics():
    """Re-calculate metrics for Arabic entries only."""
    from calculate_medlineplus_metrics import evaluate_single, aggregate_results

    # Load results
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Load existing metrics
    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        all_metrics = json.load(f)

    # Create a map of existing metrics
    metrics_map = {}
    for m in all_metrics:
        key = f"{m['doc_id']}|{m['model']}|{m['language']}"
        metrics_map[key] = m

    # Re-calculate Arabic metrics
    arabic_count = 0
    for result in results:
        if result['language'] == 'arabic':
            key = f"{result['doc_id']}|{result['model']}|{result['language']}"
            logger.info(f"Re-calculating: {result['doc_id']} | {result['model']}")

            new_metrics = evaluate_single(result)
            metrics_map[key] = new_metrics.to_dict()
            arabic_count += 1

    logger.info(f"Re-calculated {arabic_count} Arabic metrics")

    # Convert back to list
    all_metrics = list(metrics_map.values())

    # Save updated metrics
    with open(METRICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2)

    logger.info(f"Saved updated metrics to {METRICS_FILE}")

    # Re-aggregate
    aggregate_results()


if __name__ == "__main__":
    print("Step 1: Update Arabic professional translations in results...")
    update_results_with_arabic()

    print("\nStep 2: Re-calculate Arabic metrics...")
    recalculate_arabic_metrics()

    print("\nDone!")
