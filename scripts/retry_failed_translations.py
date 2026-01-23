#!/usr/bin/env python3
"""
Retry Failed Translations

Retries the 3 translations that returned empty results:
1. immunize/tdap | kimi-k2 | tagalog
2. immunize/hepatitis_b | claude-opus-4.5 | arabic
3. immunize/mmr | kimi-k2 | arabic
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import BASE_DIR, TRANSLATIONS_DIR, METRICS_DIR, logger
from translation_pipeline import translate_with_retry

# Failed translations to retry
# Note: User mentioned tagalog/kimi-k2 was manually copied, so only retry these 2:
FAILED_TRANSLATIONS = [
    ("immunize/hepatitis_b", "claude-opus-4.5", "arabic"),
    ("immunize/mmr", "kimi-k2", "arabic"),
]

def load_original_text(doc_id: str) -> str:
    """Load the original English text for a document."""
    doc_path = BASE_DIR / "data" / "extracted_text" / doc_id / "english.txt"
    if not doc_path.exists():
        # Try alternate path structure
        parts = doc_id.split("/")
        doc_path = BASE_DIR / "data" / "extracted_text" / parts[0] / "english" / f"{parts[1]}.txt"

    with open(doc_path, 'r') as f:
        return f.read()

def main():
    # Load existing results
    results_file = TRANSLATIONS_DIR / "all_results.json"
    with open(results_file, 'r') as f:
        all_results = json.load(f)

    print(f"Loaded {len(all_results)} existing results")

    # Create index for quick lookup
    results_index = {
        (r['doc_id'], r['model'], r['language']): i
        for i, r in enumerate(all_results)
    }

    # Retry each failed translation
    for doc_id, model, language in FAILED_TRANSLATIONS:
        print(f"\n{'='*60}")
        print(f"Retrying: {doc_id} | {model} | {language}")
        print('='*60)

        try:
            # Load original text
            original_text = load_original_text(doc_id)
            print(f"Loaded original text: {len(original_text)} chars")

            # Perform translation
            translation = translate_with_retry(
                text=original_text,
                target_language=language,
                model_name=model,
                is_back_translation=False,
                source_language="English",
                max_retries=3
            )

            if translation and len(translation) > 0:
                print(f"✓ Translation successful: {len(translation)} chars")
                print(f"  Preview: {translation[:100]}...")

                # Perform back-translation
                back_translation = translate_with_retry(
                    text=translation,
                    target_language="english",
                    model_name=model,
                    is_back_translation=True,
                    source_language=language,
                    max_retries=3
                )

                if back_translation and len(back_translation) > 0:
                    print(f"✓ Back-translation successful: {len(back_translation)} chars")

                    # Update the result in our list
                    key = (doc_id, model, language)
                    if key in results_index:
                        idx = results_index[key]
                        all_results[idx]['llm_translation'] = translation
                        all_results[idx]['back_translation'] = back_translation
                        print(f"✓ Updated result at index {idx}")
                    else:
                        print(f"✗ Could not find result to update")
                else:
                    print(f"✗ Back-translation failed")
            else:
                print(f"✗ Translation failed or returned empty")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    # Save updated results
    print(f"\n{'='*60}")
    print("Saving updated results...")
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to {results_file}")

    # Verify the updates
    print("\nVerifying updates:")
    for doc_id, model, language in FAILED_TRANSLATIONS:
        key = (doc_id, model, language)
        if key in results_index:
            idx = results_index[key]
            r = all_results[idx]
            trans_len = len(r.get('llm_translation', '') or '')
            back_len = len(r.get('back_translation', '') or '')
            status = "✓" if trans_len > 0 and back_len > 0 else "✗"
            print(f"  {status} {doc_id} | {model} | {language}: trans={trans_len}, back={back_len}")

if __name__ == "__main__":
    main()
