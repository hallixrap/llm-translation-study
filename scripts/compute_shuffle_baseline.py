#!/usr/bin/env python3
"""
Compute Baseline: Direct Original vs Shuffled Document Similarity

This script addresses the reviewer comment asking:
"What's the similarity between the shuffled document itself and the original document?"

This establishes a negative control / baseline showing what score decrease to expect
if a model memorized the original and "unscrambled" shuffled input.

Output: LaBSE similarity between each original document and its shuffled version
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
SENSITIVITY_RESULTS = BASE_DIR / "output" / "sensitivity_analysis" / "all_sensitivity_results_with_metrics.json"
OUTPUT_DIR = BASE_DIR / "output" / "sensitivity_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LOAD LABSE MODEL
# =============================================================================

print("Loading LaBSE model...")
from sentence_transformers import SentenceTransformer
labse_model = SentenceTransformer('sentence-transformers/LaBSE')
print("LaBSE model loaded.")


def calculate_labse_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using LaBSE embeddings."""
    embeddings = labse_model.encode([text1, text2])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def main():
    # Load sensitivity results
    print(f"Loading sensitivity results from {SENSITIVITY_RESULTS}")
    with open(SENSITIVITY_RESULTS, 'r') as f:
        results = json.load(f)

    # Group by doc_id, model, language to find original/shuffled pairs
    # We only need the source texts, not the translations
    pairs = {}
    for r in results:
        key = (r['doc_id'], r['model'], r['language'])
        if key not in pairs:
            pairs[key] = {}
        pairs[key][r['category']] = r['source_text']

    # Calculate similarity for each pair
    print("\nCalculating direct Original vs Shuffled similarity (no translation)...")
    print("=" * 70)

    comparisons = []

    for (doc_id, model, language), texts in pairs.items():
        if 'original' in texts and 'shuffled' in texts:
            original = texts['original']
            shuffled = texts['shuffled']

            # Calculate direct similarity
            similarity = calculate_labse_similarity(original, shuffled)

            comparisons.append({
                'doc_id': doc_id,
                'model': model,  # Note: shuffling used same seed per doc, independent of model
                'language': language,
                'original_vs_shuffled_labse': similarity
            })

            print(f"  {doc_id[:30]:30s} | {model:15s} | {language:18s} | LaBSE: {similarity:.4f}")

    # Since the same document is shuffled the same way regardless of model,
    # we can aggregate by doc_id (the shuffled text is the same for each doc)
    doc_similarities = {}
    for c in comparisons:
        doc_id = c['doc_id']
        if doc_id not in doc_similarities:
            doc_similarities[doc_id] = []
        doc_similarities[doc_id].append(c['original_vs_shuffled_labse'])

    # Verify all models/languages give same score for same doc (they should, same text)
    print("\n" + "=" * 70)
    print("SUMMARY BY DOCUMENT (aggregated across models/languages)")
    print("=" * 70)

    doc_scores = []
    for doc_id, scores in doc_similarities.items():
        # All should be identical since it's same text comparison
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        doc_scores.append(mean_score)
        print(f"  {doc_id:40s} | LaBSE: {mean_score:.4f} (std: {std_score:.6f})")

    # Overall statistics
    print("\n" + "=" * 70)
    print("OVERALL STATISTICS")
    print("=" * 70)

    mean_sim = np.mean(doc_scores)
    std_sim = np.std(doc_scores)
    min_sim = np.min(doc_scores)
    max_sim = np.max(doc_scores)

    print(f"  Mean LaBSE (Original vs Shuffled):  {mean_sim:.4f}")
    print(f"  Std Dev:                            {std_sim:.4f}")
    print(f"  Range:                              {min_sim:.4f} - {max_sim:.4f}")
    print(f"  N documents:                        {len(doc_scores)}")

    # Compare with the back-translation scores from the main analysis
    # The current scores are ~0.95 for back-translation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    expected_drop = 1.0 - mean_sim
    print(f"\n  Direct shuffling causes LaBSE to drop from 1.0 to ~{mean_sim:.3f}")
    print(f"  This represents a {expected_drop*100:.1f}% decrease from perfect similarity")
    print(f"\n  Back-translation scores in the study are ~0.95 for BOTH conditions")
    print(f"  If models had memorized and 'unscrambled' shuffled input:")
    print(f"    - Shuffled→translate→back should score ~{mean_sim:.3f} (matching shuffled structure)")
    print(f"    - Original→translate→back should score ~0.95+ (matching original structure)")
    print(f"\n  The fact that BOTH conditions score ~0.95 suggests:")
    print(f"    - Models are NOT unscrambling to memorized originals")
    print(f"    - Semantic content is preserved even when structure is disrupted")
    print(f"    - LaBSE is sensitive to meaning, less sensitive to sentence order")

    # Save results
    output_data = {
        'summary': {
            'mean_original_vs_shuffled_labse': float(mean_sim),
            'std': float(std_sim),
            'min': float(min_sim),
            'max': float(max_sim),
            'n_documents': len(doc_scores),
            'interpretation': (
                f"Sentence shuffling reduces LaBSE similarity to {mean_sim:.3f}. "
                f"If models memorized originals, shuffled back-translations should score "
                f"around {mean_sim:.3f}. Both conditions scoring ~0.95 suggests models "
                f"translate content rather than recall memorized text."
            )
        },
        'by_document': {doc_id: float(np.mean(scores)) for doc_id, scores in doc_similarities.items()},
        'all_comparisons': comparisons
    }

    output_file = OUTPUT_DIR / "original_vs_shuffled_baseline.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  Results saved to: {output_file}")

    return output_data


if __name__ == "__main__":
    main()
