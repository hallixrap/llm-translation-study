#!/usr/bin/env python3
"""
Inter-Model Translation Concordance Analysis

PURPOSE:
    Measures CONVERGENT VALIDITY of LLM medical translations by comparing
    translations ACROSS models for the same document-language pair. If four
    independently trained models converge on similar translations, it is strong
    evidence that the translations are correct — not an artifact of any single
    model's training data or biases.

APPROACH:
    For each (doc_id, language) pair, we have up to 4 translations (one per
    model). We compute pairwise LaBSE similarity and BERTScore between all
    model pairs (4 choose 2 = 6 comparisons per group). This yields an
    inter-model concordance score for each pair.

AGGREGATIONS:
    - Overall mean inter-model concordance
    - By language
    - By resource level (high / medium / low)
    - By model pair (e.g., GPT-5.1 vs Claude Opus 4.5)
    - By document category (cancer vs vaccine)

SCOPE:
    704 translations -> 176 (doc_id, language) groups -> ~1,054 pairwise
    comparisons (174 groups x 6 + 2 groups x 3).

OUTPUT:
    output/inter_model_concordance/
        inter_model_concordance_results.json   - All pairwise scores
        inter_model_concordance_summary.json   - Aggregated summary stats
        inter_model_concordance_summary.txt    - Human-readable report
"""

import json
import sys
import time
import argparse
import numpy as np
from pathlib import Path
from itertools import combinations
from collections import defaultdict
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import LANGUAGES, ACTIVE_MODELS, logger

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
OUTPUT_DIR = BASE_DIR / "output" / "inter_model_concordance"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LANGUAGE CONFIG
# =============================================================================

RESOURCE_LEVELS = {lang: info["resource_level"] for lang, info in LANGUAGES.items()}

# BERTScore language codes (ISO 639-1 or "multilingual" for unsupported)
BERTSCORE_LANG_CODES = {
    "spanish": "es",
    "chinese_simplified": "zh",
    "vietnamese": "vi",    # not natively supported by BERTScore -> falls back
    "russian": "ru",
    "arabic": "ar",
    "korean": "ko",
    "tagalog": "tl",       # not natively supported -> falls back
    "haitian_creole": "ht", # not natively supported -> falls back
}

# =============================================================================
# LAZY-LOADED MODELS
# =============================================================================

_labse_model = None
_bert_scorer = None


def get_labse_model():
    """Lazy-load LaBSE model."""
    global _labse_model
    if _labse_model is None:
        from sentence_transformers import SentenceTransformer
        _labse_model = SentenceTransformer('sentence-transformers/LaBSE')
        logger.info("LaBSE model initialized")
    return _labse_model


def get_bert_scorer():
    """Lazy-load BERTScore module. Returns None if unavailable."""
    global _bert_scorer
    if _bert_scorer is None:
        try:
            import bert_score
            _bert_scorer = bert_score
            logger.info("BERTScore initialized")
        except Exception as e:
            logger.warning(f"BERTScore unavailable ({e}), skipping BERTScore metrics")
            _bert_scorer = "unavailable"
    if _bert_scorer == "unavailable":
        return None
    return _bert_scorer


# =============================================================================
# METRIC CALCULATIONS
# =============================================================================

def calculate_labse_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts using LaBSE embeddings."""
    model = get_labse_model()
    embeddings = model.encode([text1, text2])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


def calculate_bertscore(text1: str, text2: str, lang: str = "multilingual") -> float:
    """Compute BERTScore F1 between two texts. Returns None if BERTScore unavailable."""
    scorer = get_bert_scorer()
    if scorer is None:
        return None
    P, R, F1 = scorer.score(
        [text1], [text2],
        lang=lang,
        verbose=False,
    )
    return float(F1.item())


def make_model_pair_key(model_a: str, model_b: str) -> str:
    """Create a canonical (sorted) model pair key."""
    return " vs ".join(sorted([model_a, model_b]))


def get_doc_category(doc_id: str) -> str:
    """Classify document as 'vaccine' or 'cancer' based on doc_id prefix."""
    if doc_id.startswith("immunize/"):
        return "vaccine"
    else:
        return "cancer"


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def load_and_group_data(results_file: Path) -> dict:
    """Load all_results.json and group by (doc_id, language).

    Returns:
        dict mapping (doc_id, language) -> list of result dicts
    """
    with open(results_file, 'r') as f:
        all_results = json.load(f)

    groups = defaultdict(list)
    skipped = 0
    for entry in all_results:
        if not entry.get("success", True):
            skipped += 1
            continue
        if not entry.get("llm_translation"):
            skipped += 1
            continue
        key = (entry["doc_id"], entry["language"])
        groups[key].append(entry)

    logger.info(f"Loaded {len(all_results)} entries, skipped {skipped}, "
                f"formed {len(groups)} (doc_id, language) groups")

    # Log group size distribution
    sizes = defaultdict(int)
    for entries in groups.values():
        sizes[len(entries)] += 1
    for size, count in sorted(sizes.items()):
        logger.info(f"  Groups with {size} models: {count}")

    return dict(groups)


def compute_pairwise_concordance(groups: dict, batch_size: int = 50) -> list:
    """Compute pairwise LaBSE and BERTScore for all model pairs.

    Args:
        groups: dict mapping (doc_id, language) -> list of result dicts
        batch_size: log progress every N groups

    Returns:
        List of pairwise result dicts
    """
    pairwise_results = []
    total_groups = len(groups)
    total_pairs = sum(
        len(list(combinations(entries, 2))) for entries in groups.values()
    )

    logger.info(f"Computing pairwise concordance for {total_groups} groups, "
                f"{total_pairs} total pairs")

    pair_count = 0
    group_count = 0
    start_time = time.time()

    for (doc_id, language), entries in sorted(groups.items()):
        group_count += 1

        # Get BERTScore language code
        bert_lang = BERTSCORE_LANG_CODES.get(language, "multilingual")

        for entry_a, entry_b in combinations(entries, 2):
            pair_count += 1
            model_a = entry_a["model"]
            model_b = entry_b["model"]
            text_a = entry_a["llm_translation"]
            text_b = entry_b["llm_translation"]

            # Compute metrics
            labse_sim = calculate_labse_similarity(text_a, text_b)
            bert_f1 = calculate_bertscore(text_a, text_b, lang=bert_lang)

            result = {
                "doc_id": doc_id,
                "language": language,
                "resource_level": RESOURCE_LEVELS.get(language, "unknown"),
                "doc_category": get_doc_category(doc_id),
                "model_a": model_a,
                "model_b": model_b,
                "model_pair": make_model_pair_key(model_a, model_b),
                "labse_similarity": labse_sim,
                "bertscore_f1": bert_f1,
            }
            pairwise_results.append(result)

        # Progress logging
        if group_count % batch_size == 0 or group_count == total_groups:
            elapsed = time.time() - start_time
            rate = pair_count / elapsed if elapsed > 0 else 0
            eta = (total_pairs - pair_count) / rate if rate > 0 else 0
            logger.info(
                f"  Progress: {group_count}/{total_groups} groups, "
                f"{pair_count}/{total_pairs} pairs "
                f"({pair_count/total_pairs*100:.1f}%) - "
                f"{rate:.1f} pairs/sec - ETA: {eta/60:.1f} min"
            )

    elapsed = time.time() - start_time
    logger.info(f"Completed {pair_count} pairwise comparisons in {elapsed:.1f}s")

    return pairwise_results


# =============================================================================
# AGGREGATION
# =============================================================================

def compute_summary(pairwise_results: list) -> dict:
    """Compute aggregated summary statistics from pairwise results.

    Returns nested dict with overall, by_language, by_resource_level,
    by_model_pair, and by_doc_category breakdowns.
    """

    def aggregate(results_subset: list) -> dict:
        """Compute mean, std, median, min, max for a list of result dicts."""
        if not results_subset:
            return {
                "n": 0,
                "labse_mean": None, "labse_std": None,
                "labse_median": None, "labse_min": None, "labse_max": None,
                "bertscore_mean": None, "bertscore_std": None,
                "bertscore_median": None, "bertscore_min": None, "bertscore_max": None,
            }
        labse_vals = [r["labse_similarity"] for r in results_subset]
        bert_vals = [r["bertscore_f1"] for r in results_subset if r.get("bertscore_f1") is not None]
        result = {
            "n": len(results_subset),
            "labse_mean": float(np.mean(labse_vals)),
            "labse_std": float(np.std(labse_vals)),
            "labse_median": float(np.median(labse_vals)),
            "labse_min": float(np.min(labse_vals)),
            "labse_max": float(np.max(labse_vals)),
        }
        if bert_vals:
            result.update({
                "bertscore_mean": float(np.mean(bert_vals)),
                "bertscore_std": float(np.std(bert_vals)),
                "bertscore_median": float(np.median(bert_vals)),
                "bertscore_min": float(np.min(bert_vals)),
                "bertscore_max": float(np.max(bert_vals)),
            })
        else:
            result.update({
                "bertscore_mean": None, "bertscore_std": None,
                "bertscore_median": None, "bertscore_min": None, "bertscore_max": None,
            })
        return result

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_pairwise_comparisons": len(pairwise_results),
    }

    # Overall
    summary["overall"] = aggregate(pairwise_results)

    # By language
    by_language = defaultdict(list)
    for r in pairwise_results:
        by_language[r["language"]].append(r)
    summary["by_language"] = {
        lang: aggregate(results) for lang, results in sorted(by_language.items())
    }

    # By resource level
    by_resource = defaultdict(list)
    for r in pairwise_results:
        by_resource[r["resource_level"]].append(r)
    summary["by_resource_level"] = {
        level: aggregate(results)
        for level, results in sorted(by_resource.items())
    }

    # By model pair
    by_model_pair = defaultdict(list)
    for r in pairwise_results:
        by_model_pair[r["model_pair"]].append(r)
    summary["by_model_pair"] = {
        pair: aggregate(results)
        for pair, results in sorted(by_model_pair.items())
    }

    # By document category
    by_category = defaultdict(list)
    for r in pairwise_results:
        by_category[r["doc_category"]].append(r)
    summary["by_doc_category"] = {
        cat: aggregate(results) for cat, results in sorted(by_category.items())
    }

    # By language x model pair (for detailed analysis)
    by_lang_model = defaultdict(list)
    for r in pairwise_results:
        by_lang_model[(r["language"], r["model_pair"])].append(r)
    summary["by_language_model_pair"] = {
        f"{lang} | {pair}": aggregate(results)
        for (lang, pair), results in sorted(by_lang_model.items())
    }

    return summary


def format_summary_text(summary: dict) -> str:
    """Generate a human-readable text report from the summary."""
    lines = []
    lines.append("=" * 78)
    lines.append("INTER-MODEL TRANSLATION CONCORDANCE ANALYSIS")
    lines.append("=" * 78)
    lines.append(f"Generated: {summary['timestamp']}")
    lines.append(f"Total pairwise comparisons: {summary['total_pairwise_comparisons']}")
    lines.append("")

    # --- Overall ---
    lines.append("-" * 78)
    lines.append("OVERALL CONCORDANCE")
    lines.append("-" * 78)
    o = summary["overall"]
    lines.append(f"  N comparisons:     {o['n']}")
    lines.append(f"  LaBSE similarity:  {o['labse_mean']:.4f} +/- {o['labse_std']:.4f}  "
                 f"(median {o['labse_median']:.4f}, range {o['labse_min']:.4f}-{o['labse_max']:.4f})")
    lines.append(f"  BERTScore F1:      {o['bertscore_mean']:.4f} +/- {o['bertscore_std']:.4f}  "
                 f"(median {o['bertscore_median']:.4f}, range {o['bertscore_min']:.4f}-{o['bertscore_max']:.4f})")
    lines.append("")

    # --- By Language ---
    lines.append("-" * 78)
    lines.append("BY LANGUAGE")
    lines.append("-" * 78)
    lines.append(f"  {'Language':<22} {'N':>5}  {'LaBSE Mean':>11} {'LaBSE SD':>9}  "
                 f"{'BERT Mean':>10} {'BERT SD':>8}")
    lines.append(f"  {'-'*22} {'-'*5}  {'-'*11} {'-'*9}  {'-'*10} {'-'*8}")
    for lang, stats in sorted(summary["by_language"].items()):
        resource = RESOURCE_LEVELS.get(lang, "?")
        lines.append(
            f"  {lang:<22} {stats['n']:>5}  "
            f"{stats['labse_mean']:>11.4f} {stats['labse_std']:>9.4f}  "
            f"{stats['bertscore_mean']:>10.4f} {stats['bertscore_std']:>8.4f}  "
            f"[{resource}]"
        )
    lines.append("")

    # --- By Resource Level ---
    lines.append("-" * 78)
    lines.append("BY RESOURCE LEVEL")
    lines.append("-" * 78)
    lines.append(f"  {'Level':<10} {'N':>5}  {'LaBSE Mean':>11} {'LaBSE SD':>9}  "
                 f"{'BERT Mean':>10} {'BERT SD':>8}")
    lines.append(f"  {'-'*10} {'-'*5}  {'-'*11} {'-'*9}  {'-'*10} {'-'*8}")
    for level in ["high", "medium", "low"]:
        if level in summary["by_resource_level"]:
            stats = summary["by_resource_level"][level]
            lines.append(
                f"  {level:<10} {stats['n']:>5}  "
                f"{stats['labse_mean']:>11.4f} {stats['labse_std']:>9.4f}  "
                f"{stats['bertscore_mean']:>10.4f} {stats['bertscore_std']:>8.4f}"
            )
    lines.append("")

    # --- By Model Pair ---
    lines.append("-" * 78)
    lines.append("BY MODEL PAIR")
    lines.append("-" * 78)
    lines.append(f"  {'Model Pair':<40} {'N':>5}  {'LaBSE Mean':>11} {'LaBSE SD':>9}  "
                 f"{'BERT Mean':>10} {'BERT SD':>8}")
    lines.append(f"  {'-'*40} {'-'*5}  {'-'*11} {'-'*9}  {'-'*10} {'-'*8}")
    for pair, stats in sorted(summary["by_model_pair"].items()):
        lines.append(
            f"  {pair:<40} {stats['n']:>5}  "
            f"{stats['labse_mean']:>11.4f} {stats['labse_std']:>9.4f}  "
            f"{stats['bertscore_mean']:>10.4f} {stats['bertscore_std']:>8.4f}"
        )
    lines.append("")

    # --- By Document Category ---
    lines.append("-" * 78)
    lines.append("BY DOCUMENT CATEGORY")
    lines.append("-" * 78)
    lines.append(f"  {'Category':<12} {'N':>5}  {'LaBSE Mean':>11} {'LaBSE SD':>9}  "
                 f"{'BERT Mean':>10} {'BERT SD':>8}")
    lines.append(f"  {'-'*12} {'-'*5}  {'-'*11} {'-'*9}  {'-'*10} {'-'*8}")
    for cat, stats in sorted(summary["by_doc_category"].items()):
        lines.append(
            f"  {cat:<12} {stats['n']:>5}  "
            f"{stats['labse_mean']:>11.4f} {stats['labse_std']:>9.4f}  "
            f"{stats['bertscore_mean']:>10.4f} {stats['bertscore_std']:>8.4f}"
        )
    lines.append("")

    # --- Interpretation Guide ---
    lines.append("-" * 78)
    lines.append("INTERPRETATION")
    lines.append("-" * 78)
    lines.append("  LaBSE similarity: 1.0 = identical embeddings, >0.90 = very high convergence")
    lines.append("  BERTScore F1:     1.0 = identical, >0.85 = strong agreement")
    lines.append("")
    lines.append("  High inter-model concordance indicates convergent validity:")
    lines.append("  independently trained models agree on translation content,")
    lines.append("  suggesting the translations are accurate rather than reflecting")
    lines.append("  any single model's idiosyncrasies.")
    lines.append("")
    lines.append("  Lower concordance for low-resource languages would be expected,")
    lines.append("  as models have less training data to converge on standard translations.")
    lines.append("=" * 78)

    return "\n".join(lines)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Inter-model translation concordance analysis"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50,
        help="Log progress every N groups (default: 50)"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit to first N groups (for testing)"
    )
    args = parser.parse_args()

    logger.info("Starting inter-model concordance analysis")

    # Load data
    groups = load_and_group_data(RESULTS_FILE)

    # Optionally limit for testing
    if args.limit:
        limited = dict(list(groups.items())[:args.limit])
        logger.info(f"Limiting to {len(limited)} groups (--limit {args.limit})")
        groups = limited

    # Compute pairwise concordance
    pairwise_results = compute_pairwise_concordance(groups, batch_size=args.batch_size)

    # Save pairwise results
    results_file = OUTPUT_DIR / "inter_model_concordance_results.json"
    with open(results_file, 'w') as f:
        json.dump(pairwise_results, f, indent=2)
    logger.info(f"Saved {len(pairwise_results)} pairwise results to {results_file}")

    # Compute and save summary
    summary = compute_summary(pairwise_results)

    summary_json_file = OUTPUT_DIR / "inter_model_concordance_summary.json"
    with open(summary_json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_json_file}")

    summary_text = format_summary_text(summary)
    summary_txt_file = OUTPUT_DIR / "inter_model_concordance_summary.txt"
    with open(summary_txt_file, 'w') as f:
        f.write(summary_text)
    logger.info(f"Saved human-readable summary to {summary_txt_file}")

    # Print summary to console
    print()
    print(summary_text)


if __name__ == "__main__":
    main()
