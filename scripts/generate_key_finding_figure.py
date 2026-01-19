#!/usr/bin/env python3
"""
Generate Figure 2: Semantic vs Lexical Fidelity by Language Resource Level

This figure visualizes the key finding: low-resource languages achieve
comparable semantic fidelity (LaBSE) but lower lexical overlap (BLEU)
compared to high-resource languages.
"""

import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path("/Users/chukanya/Library/Mobile Documents/com~apple~CloudDocs/Coding/Back translation project")
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
OUTPUT_DIR = BASE_DIR / "Images"

# Language metadata with resource levels based on CommonCrawl %
LANGUAGES = {
    "spanish": {"name": "Spanish", "resource": "High", "cc_pct": 4.41},
    "chinese_simplified": {"name": "Chinese", "resource": "High", "cc_pct": 6.18},
    "vietnamese": {"name": "Vietnamese", "resource": "High", "cc_pct": 1.08},
    "russian": {"name": "Russian", "resource": "High", "cc_pct": 6.48},
    "korean": {"name": "Korean", "resource": "Medium", "cc_pct": 0.80},
    "arabic": {"name": "Arabic", "resource": "Medium", "cc_pct": 0.67},
    "tagalog": {"name": "Tagalog", "resource": "Low", "cc_pct": 0.008},
    "haitian_creole": {"name": "Haitian Creole", "resource": "Low", "cc_pct": 0.003},
}

def load_data():
    with open(METRICS_FILE, 'r') as f:
        return json.load(f)

def aggregate_by_language(data):
    """Aggregate metrics by language across all models and documents."""
    lang_metrics = {lang: {"labse": [], "bleu": []} for lang in LANGUAGES}

    for record in data:
        lang = record["language"]
        if lang in lang_metrics:
            # Back-translation LaBSE (semantic) - need to get from cross_lang_labse
            labse_val = record.get("cross_lang_labse")
            if labse_val is not None:
                lang_metrics[lang]["labse"].append(labse_val)
            # vs Professional BLEU (lexical overlap with human translation)
            bleu_val = record.get("same_lang_bleu")
            if bleu_val is not None:
                lang_metrics[lang]["bleu"].append(bleu_val)

    # Calculate means
    results = {}
    for lang, metrics in lang_metrics.items():
        labse_clean = [x for x in metrics["labse"] if x is not None]
        bleu_clean = [x for x in metrics["bleu"] if x is not None]
        results[lang] = {
            "labse_mean": np.mean(labse_clean) if labse_clean else 0,
            "labse_std": np.std(labse_clean) if labse_clean else 0,
            "bleu_mean": np.mean(bleu_clean) if bleu_clean else 0,
            "bleu_std": np.std(bleu_clean) if bleu_clean else 0,
        }
    return results

def create_figure(lang_data):
    """Create a two-panel figure comparing semantic vs lexical fidelity."""

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Sort languages by resource level for consistent ordering
    resource_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_langs = sorted(LANGUAGES.keys(),
                          key=lambda x: (resource_order[LANGUAGES[x]["resource"]],
                                        -LANGUAGES[x]["cc_pct"]))

    # Colors by resource level
    colors = {
        "High": "#2E86AB",      # Blue
        "Medium": "#A23B72",    # Purple
        "Low": "#F18F01",       # Orange
    }

    lang_names = [LANGUAGES[l]["name"] for l in sorted_langs]
    lang_colors = [colors[LANGUAGES[l]["resource"]] for l in sorted_langs]

    # Panel A: Semantic Fidelity (LaBSE)
    ax = axes[0]
    labse_vals = [lang_data[l]["labse_mean"] for l in sorted_langs]
    labse_errs = [lang_data[l]["labse_std"] for l in sorted_langs]

    bars = ax.bar(range(len(sorted_langs)), labse_vals, color=lang_colors,
                  edgecolor='black', linewidth=0.5)
    ax.errorbar(range(len(sorted_langs)), labse_vals, yerr=labse_errs,
                fmt='none', color='black', capsize=3, linewidth=1)

    ax.set_ylabel('LaBSE Score', fontsize=11)
    ax.set_title('A. Semantic Fidelity\n(meaning preservation)', fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(sorted_langs)))
    ax.set_xticklabels(lang_names, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0.85, 1.0)  # Narrow range to show actual variation
    ax.axhline(y=0.95, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.text(7.5, 0.952, 'High fidelity threshold', fontsize=8, color='gray', ha='right')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, labse_vals)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.008, f'{val:.3f}',
                ha='center', va='bottom', fontsize=8)

    # Panel B: Lexical Fidelity (BLEU vs Professional)
    ax = axes[1]
    bleu_vals = [lang_data[l]["bleu_mean"] for l in sorted_langs]
    bleu_errs = [lang_data[l]["bleu_std"] for l in sorted_langs]

    bars = ax.bar(range(len(sorted_langs)), bleu_vals, color=lang_colors,
                  edgecolor='black', linewidth=0.5)
    ax.errorbar(range(len(sorted_langs)), bleu_vals, yerr=bleu_errs,
                fmt='none', color='black', capsize=3, linewidth=1)

    ax.set_ylabel('BLEU Score', fontsize=11)
    ax.set_title('B. Lexical Fidelity\n(word choice vs. professional)', fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(sorted_langs)))
    ax.set_xticklabels(lang_names, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0, 60)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, bleu_vals)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.5, f'{val:.1f}',
                ha='center', va='bottom', fontsize=8)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors["High"], edgecolor='black', label='High-resource (>1% CommonCrawl)'),
        Patch(facecolor=colors["Medium"], edgecolor='black', label='Medium-resource (0.1-1%)'),
        Patch(facecolor=colors["Low"], edgecolor='black', label='Low-resource (<0.1%)'),
    ]
    fig.legend(handles=legend_elements, loc='upper center', ncol=3,
               bbox_to_anchor=(0.5, 0.02), frameon=True, fontsize=9)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)

    return fig

def main():
    print("Loading data...")
    data = load_data()
    print(f"Loaded {len(data)} records")

    print("Aggregating by language...")
    lang_data = aggregate_by_language(data)

    # Print summary
    print("\nLanguage Summary:")
    print("-" * 60)
    for lang in sorted(LANGUAGES.keys()):
        info = LANGUAGES[lang]
        metrics = lang_data[lang]
        print(f"{info['name']:15} ({info['resource']:6}): "
              f"LaBSE={metrics['labse_mean']:.3f}, BLEU={metrics['bleu_mean']:.1f}")

    print("\nGenerating figure...")
    fig = create_figure(lang_data)

    output_path = OUTPUT_DIR / "semantic_vs_lexical_fidelity.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to: {output_path}")

    plt.close()

if __name__ == "__main__":
    main()
