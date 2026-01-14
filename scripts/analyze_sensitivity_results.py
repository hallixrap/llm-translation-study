#!/usr/bin/env python3
"""
Analyze existing sensitivity analysis results.

This script loads the already-completed translations and metrics,
runs statistical analysis, and generates the report.

Use this when you have results but the analysis step failed.
"""

import json
import sys
from pathlib import Path
import numpy as np
from scipy import stats
from dataclasses import dataclass, asdict
from typing import List

# Add scripts directory
sys.path.insert(0, str(Path(__file__).parent))

from sentence_reordering_sensitivity import (
    ComparisonStats, SensitivityResult,
    calculate_comparison_stats, generate_summary_report,
    OUTPUT_DIR, SELECTED_MODELS, SELECTED_LANGUAGES
)

def load_results_from_file():
    """Load results with metrics from checkpoint file."""
    results_file = OUTPUT_DIR / "all_sensitivity_results_with_metrics.json"

    if not results_file.exists():
        print(f"ERROR: Results file not found: {results_file}")
        print("Run the full analysis first with:")
        print("  python sentence_reordering_sensitivity.py --run")
        sys.exit(1)

    with open(results_file, 'r') as f:
        data = json.load(f)

    # Convert dicts back to SensitivityResult objects
    results = []
    for d in data:
        # Create SensitivityResult with all fields
        result = SensitivityResult(
            doc_id=d['doc_id'],
            model=d['model'],
            language=d['language'],
            category=d['category'],
            source_text=d['source_text'],
            translation=d['translation'],
            back_translation=d['back_translation'],
            shuffle_indices=d.get('shuffle_indices', []),
            num_sentences=d.get('num_sentences', 0),
            labse_score=d.get('labse_score', 0.0),
            bleu_score=d.get('bleu_score', 0.0),
            xlm_roberta_score=d.get('xlm_roberta_score', 0.0),
            mbert_score=d.get('mbert_score', 0.0),
            translation_time=d.get('translation_time', 0.0),
            back_translation_time=d.get('back_translation_time', 0.0),
            timestamp=d.get('timestamp', '')
        )
        results.append(result)

    print(f"Loaded {len(results)} results from checkpoint")
    return results

def main():
    print("="*80)
    print("ANALYZING EXISTING SENSITIVITY RESULTS")
    print("="*80)
    print()

    # Load results
    results = load_results_from_file()

    # Separate by category
    original_results = [r for r in results if r.category == "original"]
    shuffled_results = [r for r in results if r.category == "shuffled"]

    print(f"Original results: {len(original_results)}")
    print(f"Shuffled results: {len(shuffled_results)}")
    print()

    # Statistical analysis
    print("Performing statistical analysis...")
    all_stats = []
    for metric in ["labse_score", "bleu_score", "xlm_roberta_score", "mbert_score"]:
        print(f"  Analyzing {metric}...")
        stats_results = calculate_comparison_stats(original_results, shuffled_results, metric)
        all_stats.extend(stats_results)

    # Save statistics
    stats_file = OUTPUT_DIR / "statistical_comparison.json"
    with open(stats_file, 'w') as f:
        json.dump([s.to_dict() for s in all_stats], f, indent=2)

    print(f"Saved statistical comparison to {stats_file}")

    # Generate summary report
    generate_summary_report(all_stats)

    # Print quick summary
    print("\n" + "="*80)
    print("QUICK SUMMARY")
    print("="*80)
    for stat in all_stats:
        if stat.metric_name == "labse_score":  # Focus on main semantic metric
            sig_marker = "**" if stat.significant else "  "
            print(f"{sig_marker} {stat.model} | {stat.language}")
            print(f"   Original: {stat.original_mean:.4f}")
            print(f"   Shuffled: {stat.shuffled_mean:.4f}")
            print(f"   Change: {stat.percent_change:+.1f}% (p={stat.p_value:.3f})")
            if stat.significant:
                print(f"   ⚠️  SIGNIFICANT DIFFERENCE - may indicate memorization")
            else:
                print(f"   ✓ No significant change - suggests true translation")
            print()

    print("="*80)
    print("Analysis complete!")
    print(f"\nResults:")
    print(f"  - Statistics: output/sensitivity_analysis/statistical_comparison.json")
    print(f"  - Report: output/sensitivity_analysis/sensitivity_analysis_report.txt")

if __name__ == "__main__":
    main()
