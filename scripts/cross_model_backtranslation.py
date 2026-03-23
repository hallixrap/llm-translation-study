#!/usr/bin/env python3
"""
Cross-Model Back-Translation Sensitivity Analysis

PURPOSE:
    Addresses Reviewer 1's circularity critique: using the same LLM for both
    forward and back-translation validates internal consistency, not translation
    quality. A model making systematic errors in both directions will score
    near-perfectly on LaBSE while producing reliably wrong translations.

APPROACH:
    For each existing forward translation (A→B with model M), run back-translation
    (B→A) with all OTHER models. With 4 models, each translation gets 3
    cross-model back-translators, giving 12 cross-model pairings total.

    If LaBSE scores remain high (>0.90) across cross-model pairings, this
    directly falsifies the circularity critique.

DESIGN:
    - Reuses existing forward translations from all_results.json (no re-translation)
    - Only runs back-translation step (B→A) with different models
    - Checkpoint-resumable to survive interruptions
    - Excludes Kimi K2 as back-translator by default due to its 60-90 min latency
      (can be enabled with --include-kimi)

SCOPE:
    Default: 702 successful results × 3 cross-model pairs = 2,106 back-translations
    With --include-kimi: 702 × 3 = same (Kimi is one of the forward models,
    so other 3 models back-translate its outputs too)

COST ESTIMATE:
    ~2,106 back-translations × ~$0.02 avg = ~$40-50
    Runtime: 3-6 hours (with rate limiting, excluding Kimi as back-translator)

OUTPUT:
    output/cross_model_backtranslation/
        all_cross_model_results.json     - Raw back-translations + metrics
        checkpoint.json                  - For resume capability
        summary_report.json              - Aggregated comparison vs same-model
        summary_report.txt               - Human-readable summary
"""

import json
import time
import sys
import argparse
import traceback
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ACTIVE_MODELS, LANGUAGES, EXECUTION_CONFIG, logger
)
from translation_pipeline import translate_with_retry

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path("/Users/chuka/Library/Mobile Documents/com~apple~CloudDocs/Coding/Back translation project")
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
OUTPUT_DIR = BASE_DIR / "output" / "cross_model_backtranslation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
RESULTS_OUTPUT = OUTPUT_DIR / "all_cross_model_results.json"

# =============================================================================
# DATA STRUCTURE
# =============================================================================

@dataclass
class CrossModelResult:
    """Stores a single cross-model back-translation result."""
    doc_id: str
    forward_model: str          # Model that did English → Target
    back_model: str             # Model doing Target → English (different from forward)
    language: str
    original_text: str          # Original English
    translated_text: str        # The existing forward translation (input to back-translator)
    back_translated_text: str   # New cross-model back-translation
    labse_score: Optional[float]
    bertscore_f1: Optional[float]
    timestamp: str
    back_translation_time: float
    success: bool
    error_message: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# =============================================================================
# LAZY-LOADED METRICS MODELS
# =============================================================================

_labse_model = None
_bert_scorer = None


def get_labse_model():
    global _labse_model
    if _labse_model is None:
        from sentence_transformers import SentenceTransformer
        _labse_model = SentenceTransformer('sentence-transformers/LaBSE')
        logger.info("LaBSE model loaded")
    return _labse_model


def get_bert_scorer():
    global _bert_scorer
    if _bert_scorer is None:
        import bert_score
        _bert_scorer = bert_score
        logger.info("BERTScore initialized")
    return _bert_scorer


def calculate_labse(text1: str, text2: str) -> float:
    model = get_labse_model()
    embeddings = model.encode([text1, text2])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


def calculate_bertscore(hypothesis: str, reference: str) -> float:
    bert_score = get_bert_scorer()
    P, R, F1 = bert_score.score([hypothesis], [reference], lang="en", verbose=False)
    return float(F1.item())


# =============================================================================
# CHECKPOINT HELPERS
# =============================================================================

def load_checkpoint() -> set:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
        completed = set(data.get("completed", []))
        logger.info(f"Checkpoint loaded: {len(completed)} combinations already done")
        return completed
    return set()


def save_checkpoint(completed: set):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"completed": list(completed), "timestamp": datetime.now().isoformat()}, f)


def load_existing_results() -> list:
    if RESULTS_OUTPUT.exists():
        with open(RESULTS_OUTPUT) as f:
            return json.load(f)
    return []


def save_results(results: list):
    with open(RESULTS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} results to {RESULTS_OUTPUT}")


def combo_key(doc_id: str, forward_model: str, back_model: str, language: str) -> str:
    return f"{doc_id}|{forward_model}|{back_model}|{language}"


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_cross_model_backtranslation(
    include_kimi_as_backtranslator: bool = False,
    dry_run: bool = False,
    pilot_n: int = None
):
    """
    Run cross-model back-translation on all existing forward translations.

    Args:
        include_kimi_as_backtranslator: Whether to use Kimi K2 as back-translator.
            Disabled by default due to 60-90 min latency per document.
        dry_run: Print plan without making API calls.
        pilot_n: If set, only process first N source records (for testing).
    """

    # -------------------------------------------------------------------------
    # Load existing forward translations
    # -------------------------------------------------------------------------
    logger.info(f"Loading existing forward translations from {RESULTS_FILE}")
    with open(RESULTS_FILE) as f:
        all_results = json.load(f)

    # Only use successful translations that have a translated_text
    source_records = [
        r for r in all_results
        if r.get("success") and r.get("llm_translation")
    ]
    logger.info(f"Found {len(source_records)} successful forward translations")

    if pilot_n:
        source_records = source_records[:pilot_n]
        logger.info(f"Pilot mode: using first {pilot_n} records")

    # -------------------------------------------------------------------------
    # Build work list: all cross-model pairings
    # -------------------------------------------------------------------------
    # By default, exclude Kimi K2 as back-translator (too slow)
    all_models = ACTIVE_MODELS  # ['gpt-5.1', 'claude-opus-4.5', 'gemini-3-pro', 'kimi-k2']

    if include_kimi_as_backtranslator:
        back_translators = all_models
        logger.info("Kimi K2 included as back-translator (will be slow)")
    else:
        back_translators = [m for m in all_models if m != "kimi-k2"]
        logger.info(f"Back-translators (Kimi excluded): {back_translators}")

    # Each source record: back-translate with all models EXCEPT the forward model
    work_items = []
    for record in source_records:
        fwd_model = record["model"]
        for back_model in back_translators:
            if back_model == fwd_model:
                continue  # Skip same-model (that's the original study)
            work_items.append({
                "doc_id": record["doc_id"],
                "forward_model": fwd_model,
                "back_model": back_model,
                "language": record["language"],
                "original_text": record["english_original"],
                "translated_text": record["llm_translation"],
            })

    total = len(work_items)
    logger.info(f"Total cross-model back-translations to run: {total}")

    # Summary by pairing
    from collections import Counter
    pairing_counts = Counter(
        f"{w['forward_model']} → {w['back_model']}" for w in work_items
    )
    for pairing, count in sorted(pairing_counts.items()):
        logger.info(f"  {pairing}: {count} back-translations")

    if dry_run:
        print(f"\nDRY RUN - Would run {total} back-translations")
        print("Pairings:")
        for pairing, count in sorted(pairing_counts.items()):
            print(f"  {pairing}: {count}")
        return

    # -------------------------------------------------------------------------
    # Load checkpoint and existing results
    # -------------------------------------------------------------------------
    completed = load_checkpoint()
    results = load_existing_results()
    completed_count = len(completed)

    logger.info(f"Starting: {total - completed_count} remaining of {total}")

    # -------------------------------------------------------------------------
    # Run back-translations
    # -------------------------------------------------------------------------
    for i, item in enumerate(work_items):
        key = combo_key(
            item["doc_id"], item["forward_model"],
            item["back_model"], item["language"]
        )

        if key in completed:
            continue

        lang_key = item["language"]
        language_name = LANGUAGES[lang_key]["name"]

        logger.info(
            f"[{completed_count + 1}/{total}] "
            f"{item['doc_id']} | fwd={item['forward_model']} | "
            f"back={item['back_model']} | {lang_key}"
        )

        start_time = time.time()
        back_translated_text = ""
        error_msg = None
        success = False

        try:
            back_translated_text = translate_with_retry(
                text=item["translated_text"],
                target_language="English",
                model_name=item["back_model"],
                is_back_translation=True,
                source_language=language_name
            )
            success = True
            elapsed = time.time() - start_time
            logger.info(f"  Back-translation done ({elapsed:.1f}s)")

        except Exception as e:
            error_msg = str(e)
            elapsed = time.time() - start_time
            logger.error(f"  Back-translation failed: {e}")
            logger.error(traceback.format_exc())

        # -----------------------------------------------------------------------
        # Compute metrics (only if back-translation succeeded)
        # -----------------------------------------------------------------------
        labse_score = None
        bertscore_f1 = None

        if success and back_translated_text:
            try:
                labse_score = calculate_labse(
                    item["original_text"], back_translated_text
                )
                logger.info(f"  LaBSE: {labse_score:.4f}")
            except Exception as e:
                logger.warning(f"  LaBSE calculation failed: {e}")

            try:
                bertscore_f1 = calculate_bertscore(
                    back_translated_text, item["original_text"]
                )
                logger.info(f"  BERTScore F1: {bertscore_f1:.4f}")
            except Exception as e:
                logger.warning(f"  BERTScore calculation failed: {e}")

        # -----------------------------------------------------------------------
        # Save result
        # -----------------------------------------------------------------------
        result = CrossModelResult(
            doc_id=item["doc_id"],
            forward_model=item["forward_model"],
            back_model=item["back_model"],
            language=lang_key,
            original_text=item["original_text"],
            translated_text=item["translated_text"],
            back_translated_text=back_translated_text,
            labse_score=labse_score,
            bertscore_f1=bertscore_f1,
            timestamp=datetime.now().isoformat(),
            back_translation_time=elapsed,
            success=success,
            error_message=error_msg
        )
        results.append(result.to_dict())
        completed.add(key)
        completed_count += 1

        # Periodic save (every 10 completions)
        if completed_count % 10 == 0:
            save_results(results)
            save_checkpoint(completed)
            progress = (completed_count / total) * 100
            logger.info(f"Progress: {completed_count}/{total} ({progress:.1f}%)")

        # Rate limiting
        time.sleep(EXECUTION_CONFIG["rate_limit_delay"])

    # Final save
    save_results(results)
    save_checkpoint(completed)
    logger.info(f"Done! {len(results)} cross-model results saved.")

    return results


# =============================================================================
# SUMMARY ANALYSIS
# =============================================================================

def generate_summary_report():
    """
    Compare cross-model vs same-model LaBSE scores.

    This is the key analysis for addressing Reviewer 1's circularity critique.
    If cross-model LaBSE ≈ same-model LaBSE, then circularity is not driving
    the results.
    """
    # Load cross-model results
    if not RESULTS_OUTPUT.exists():
        logger.error(f"No results found at {RESULTS_OUTPUT}. Run the pipeline first.")
        return

    with open(RESULTS_OUTPUT) as f:
        cross_results = json.load(f)

    # Load same-model results (original study)
    with open(RESULTS_FILE) as f:
        orig_results = json.load(f)

    # Build same-model LaBSE lookup
    # Need to load from metrics file for same-model LaBSE
    metrics_file = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
    same_model_labse = {}

    if metrics_file.exists():
        with open(metrics_file) as f:
            metrics = json.load(f)
        for m in metrics:
            key = f"{m['doc_id']}|{m['model']}|{m['language']}"
            same_model_labse[key] = m.get("cross_lang_labse") or m.get("labse_score")

    # Aggregate cross-model scores
    successful = [r for r in cross_results if r.get("success") and r.get("labse_score") is not None]
    logger.info(f"Analyzing {len(successful)} successful cross-model back-translations")

    if not successful:
        logger.warning("No successful results with LaBSE scores yet. Run more back-translations first.")
        print("No results with LaBSE scores yet. Run the pipeline first.")
        return

    # Overall comparison
    cross_labse_all = [r["labse_score"] for r in successful]
    cross_labse_mean = np.mean(cross_labse_all)
    cross_labse_std = np.std(cross_labse_all)

    # By pairing
    from collections import defaultdict
    by_pairing = defaultdict(list)
    by_language = defaultdict(list)
    by_resource_level = defaultdict(list)

    for r in successful:
        pairing = f"{r['forward_model']} → {r['back_model']}"
        by_pairing[pairing].append(r["labse_score"])
        by_language[r["language"]].append(r["labse_score"])
        resource = LANGUAGES[r["language"]]["resource_level"]
        by_resource_level[resource].append(r["labse_score"])

    # Build report
    report = {
        "generated": datetime.now().isoformat(),
        "total_cross_model_results": len(cross_results),
        "successful_with_labse": len(successful),
        "overall_labse": {
            "mean": round(cross_labse_mean, 4),
            "std": round(cross_labse_std, 4),
            "min": round(min(cross_labse_all), 4),
            "max": round(max(cross_labse_all), 4),
        },
        "by_pairing": {
            pairing: {
                "mean": round(np.mean(scores), 4),
                "std": round(np.std(scores), 4),
                "n": len(scores),
            }
            for pairing, scores in sorted(by_pairing.items())
        },
        "by_language": {
            lang: {
                "mean": round(np.mean(scores), 4),
                "std": round(np.std(scores), 4),
                "n": len(scores),
                "resource_level": LANGUAGES[lang]["resource_level"],
            }
            for lang, scores in sorted(by_language.items())
        },
        "by_resource_level": {
            level: {
                "mean": round(np.mean(scores), 4),
                "std": round(np.std(scores), 4),
                "n": len(scores),
            }
            for level, scores in sorted(by_resource_level.items())
        },
    }

    # Compare with same-model LaBSE if available
    if same_model_labse:
        matched_same = []
        matched_cross = []
        for r in successful:
            sm_key = f"{r['doc_id']}|{r['forward_model']}|{r['language']}"
            if sm_key in same_model_labse and same_model_labse[sm_key] is not None:
                matched_same.append(same_model_labse[sm_key])
                matched_cross.append(r["labse_score"])

        if matched_same:
            delta = [c - s for c, s in zip(matched_cross, matched_same)]
            report["same_vs_cross_comparison"] = {
                "n_matched_pairs": len(matched_same),
                "same_model_labse_mean": round(np.mean(matched_same), 4),
                "cross_model_labse_mean": round(np.mean(matched_cross), 4),
                "mean_delta": round(np.mean(delta), 4),
                "std_delta": round(np.std(delta), 4),
                "interpretation": (
                    "Cross-model LaBSE scores are comparable to same-model scores, "
                    "suggesting results are not driven by circularity."
                    if abs(np.mean(delta)) < 0.02 else
                    "Notable difference between same-model and cross-model scores — "
                    "review carefully."
                ),
            }

    # Save JSON report
    report_json_path = OUTPUT_DIR / "summary_report.json"
    with open(report_json_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Summary report saved to {report_json_path}")

    # Write human-readable text report
    report_txt_path = OUTPUT_DIR / "summary_report.txt"
    with open(report_txt_path, "w") as f:
        f.write("CROSS-MODEL BACK-TRANSLATION SENSITIVITY ANALYSIS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {report['generated']}\n")
        f.write(f"Total cross-model results: {report['total_cross_model_results']}\n")
        f.write(f"Successful with LaBSE: {report['successful_with_labse']}\n\n")

        f.write("OVERALL LaBSE (Cross-Model)\n")
        f.write("-" * 40 + "\n")
        o = report["overall_labse"]
        f.write(f"  Mean ± SD:  {o['mean']:.4f} ± {o['std']:.4f}\n")
        f.write(f"  Range:      {o['min']:.4f} – {o['max']:.4f}\n\n")

        f.write("BY MODEL PAIRING (forward → back)\n")
        f.write("-" * 40 + "\n")
        for pairing, stats in report["by_pairing"].items():
            f.write(f"  {pairing:<45} {stats['mean']:.4f} ± {stats['std']:.4f}  (n={stats['n']})\n")
        f.write("\n")

        f.write("BY LANGUAGE\n")
        f.write("-" * 40 + "\n")
        for lang, stats in report["by_language"].items():
            level = stats["resource_level"]
            f.write(f"  {lang:<22} [{level:<6}]  {stats['mean']:.4f} ± {stats['std']:.4f}  (n={stats['n']})\n")
        f.write("\n")

        f.write("BY RESOURCE LEVEL\n")
        f.write("-" * 40 + "\n")
        for level, stats in report["by_resource_level"].items():
            f.write(f"  {level:<10}  {stats['mean']:.4f} ± {stats['std']:.4f}  (n={stats['n']})\n")
        f.write("\n")

        if "same_vs_cross_comparison" in report:
            comp = report["same_vs_cross_comparison"]
            f.write("SAME-MODEL vs CROSS-MODEL COMPARISON\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Matched pairs:          {comp['n_matched_pairs']}\n")
            f.write(f"  Same-model LaBSE mean:  {comp['same_model_labse_mean']:.4f}\n")
            f.write(f"  Cross-model LaBSE mean: {comp['cross_model_labse_mean']:.4f}\n")
            f.write(f"  Mean delta (cross-same): {comp['mean_delta']:.4f} ± {comp['std_delta']:.4f}\n")
            f.write(f"\n  Interpretation: {comp['interpretation']}\n")

    logger.info(f"Text report saved to {report_txt_path}")
    print(f"\nReport saved to:\n  {report_json_path}\n  {report_txt_path}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("CROSS-MODEL BACK-TRANSLATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Overall cross-model LaBSE: {cross_labse_mean:.4f} ± {cross_labse_std:.4f}")
    print("\nBy pairing:")
    for pairing, stats in report["by_pairing"].items():
        print(f"  {pairing:<45} {stats['mean']:.4f}")
    if "same_vs_cross_comparison" in report:
        comp = report["same_vs_cross_comparison"]
        print(f"\nSame-model mean: {comp['same_model_labse_mean']:.4f}")
        print(f"Cross-model mean: {comp['cross_model_labse_mean']:.4f}")
        print(f"Delta: {comp['mean_delta']:+.4f}")

    return report


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cross-model back-translation sensitivity analysis"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Run cross-model back-translations"
    )
    parser.add_argument(
        "--summarize", action="store_true",
        help="Generate summary report from completed results"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be run without making API calls"
    )
    parser.add_argument(
        "--pilot", type=int, default=None, metavar="N",
        help="Run only first N source records (for testing)"
    )
    parser.add_argument(
        "--include-kimi", action="store_true",
        help="Include Kimi K2 as back-translator (very slow)"
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Start fresh, ignore checkpoint"
    )

    args = parser.parse_args()

    if args.no_resume and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        logger.info("Checkpoint cleared — starting fresh")

    if args.dry_run:
        run_cross_model_backtranslation(
            include_kimi_as_backtranslator=args.include_kimi,
            dry_run=True,
            pilot_n=args.pilot
        )
    elif args.run:
        run_cross_model_backtranslation(
            include_kimi_as_backtranslator=args.include_kimi,
            dry_run=False,
            pilot_n=args.pilot
        )
        generate_summary_report()
    elif args.summarize:
        generate_summary_report()
    else:
        print("""
Cross-Model Back-Translation Sensitivity Analysis
Addresses Reviewer 1's circularity critique.

SETUP (required before running):
  export OPENAI_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  export GOOGLE_API_KEY="..."
  export MOONSHOT_API_KEY="..."   # only needed if --include-kimi

Usage (always use backtranslation_env/bin/python3):
  # See what would run (no API calls):
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --dry-run

  # Run pilot (first 4 source records, ~8 back-translations - no Kimi fwd in first 4):
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --run --pilot 4

  # Run full analysis (~1,576 back-translations, ~$30-40, 3-5 hours):
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --run

  # Include Kimi K2 as back-translator (adds ~522 more, very slow):
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --run --include-kimi

  # Generate/refresh summary report from completed results:
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --summarize

  # Start fresh (ignore checkpoint):
  backtranslation_env/bin/python3 scripts/cross_model_backtranslation.py --run --no-resume

Output: output/cross_model_backtranslation/
        """)
