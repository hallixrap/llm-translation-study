#!/usr/bin/env python3
"""
Add Statistical Significance Tests to Main Results

Addresses April's Comment #1: "probably need some sort of significance test here."

Performs:
1. Kruskal-Wallis test (non-parametric ANOVA) for comparing models
2. Dunn's post-hoc test for pairwise model comparisons
3. Mann-Whitney U test for language resource level comparisons
4. Generates tables with p-values and significance annotations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.stats import kruskal, mannwhitneyu
import scikit_posthocs as sp

BASE_DIR = Path(__file__).parent.parent
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
OUTPUT_DIR = BASE_DIR / "output" / "statistical_tests"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model and language configurations
MODELS = ["gpt-5.1", "claude-opus-4.5", "gemini-3-pro", "kimi-k2"]
LANGUAGES = {
    "spanish": "high",
    "chinese_simplified": "high",
    "vietnamese": "high",     # 1.08% CommonCrawl (>1% threshold)
    "russian": "high",
    "arabic": "medium",
    "korean": "medium",       # 0.80% CommonCrawl (0.1-1% threshold)
    "tagalog": "low",
    "haitian_creole": "low"
}

# Key metrics for the manuscript
KEY_METRICS = {
    # Goal 1: Back-translation fidelity
    "cross_lang_labse": "LaBSE (Goal 1)",
    "backtrans_bleu": "BLEU Back-trans (Goal 1)",

    # Goal 2: LLM vs Professional
    "same_lang_comet": "COMET (Goal 2)",
    "same_lang_bleu": "BLEU (Goal 2)",
    "same_lang_bertscore": "BERTScore (Goal 2)",

    # Goal 3: Professional back-translation
    "prof_backtrans_labse": "LaBSE Prof (Goal 3)"
}


def load_data():
    """Load metrics data."""
    with open(METRICS_FILE, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df


def kruskal_wallis_by_model(df, metric_name):
    """
    Test if there are significant differences between models.

    H0: All models perform equally on this metric
    Ha: At least one model performs differently
    """
    groups = []
    model_names = []

    for model in MODELS:
        model_data = df[df['model'] == model][metric_name].dropna()
        if len(model_data) > 0:
            groups.append(model_data.values)
            model_names.append(model)

    if len(groups) < 2:
        return None, None, model_names

    # Kruskal-Wallis test
    h_stat, p_value = kruskal(*groups)

    return h_stat, p_value, model_names


def dunn_post_hoc(df, metric_name):
    """
    Dunn's post-hoc test for pairwise model comparisons.

    Shows which specific models differ from each other.
    """
    # Prepare data for Dunn's test
    model_values = []
    model_labels = []

    for model in MODELS:
        values = df[df['model'] == model][metric_name].dropna().values
        model_values.extend(values)
        model_labels.extend([model] * len(values))

    if len(set(model_labels)) < 2:
        return None

    # Create dataframe for scikit-posthocs
    test_df = pd.DataFrame({
        'metric': model_values,
        'model': model_labels
    })

    # Dunn's test with Bonferroni correction
    try:
        dunn_results = sp.posthoc_dunn(test_df, val_col='metric', group_col='model', p_adjust='bonferroni')
        return dunn_results
    except:
        return None


def compare_language_resource_levels(df, metric_name):
    """
    Compare high-resource vs low-resource languages.

    H0: High and low-resource languages perform equally
    Ha: Performance differs by resource level
    """
    # Get scores by resource level
    high_resource = []
    low_resource = []

    for lang, resource_level in LANGUAGES.items():
        lang_scores = df[df['language'] == lang][metric_name].dropna().values

        if resource_level == "high":
            high_resource.extend(lang_scores)
        elif resource_level == "low":
            low_resource.extend(lang_scores)

    if len(high_resource) < 2 or len(low_resource) < 2:
        return None, None, None, None

    # Mann-Whitney U test
    u_stat, p_value = mannwhitneyu(high_resource, low_resource, alternative='two-sided')

    high_mean = np.mean(high_resource)
    low_mean = np.mean(low_resource)

    return u_stat, p_value, high_mean, low_mean


def generate_model_comparison_table(df):
    """
    Table 1: Model Comparisons with Statistical Tests

    For each metric, shows:
    - Mean ± SD for each model
    - Kruskal-Wallis p-value
    - Dunn's post-hoc results
    """
    results = []

    for metric_key, metric_label in KEY_METRICS.items():
        if metric_key not in df.columns:
            continue

        # Calculate means and SDs for each model
        model_stats = {}
        for model in MODELS:
            model_data = df[df['model'] == model][metric_key].dropna()
            if len(model_data) > 0:
                model_stats[model] = {
                    'mean': model_data.mean(),
                    'std': model_data.std(),
                    'n': len(model_data)
                }

        # Kruskal-Wallis test
        h_stat, kw_p, tested_models = kruskal_wallis_by_model(df, metric_key)

        # Dunn's post-hoc
        dunn_results = dunn_post_hoc(df, metric_key)

        result = {
            'Metric': metric_label,
            'metric_key': metric_key,
            'model_stats': model_stats,
            'kruskal_wallis_H': h_stat,
            'kruskal_wallis_p': kw_p,
            'significant': kw_p < 0.05 if kw_p is not None else False,
            'dunn_results': dunn_results.to_dict() if dunn_results is not None else None
        }

        results.append(result)

    return results


def generate_language_comparison_table(df):
    """
    Table 2: Language Resource Level Comparisons

    For each metric, compares:
    - High-resource languages
    - Low-resource languages
    - Statistical significance
    """
    results = []

    for metric_key, metric_label in KEY_METRICS.items():
        if metric_key not in df.columns:
            continue

        u_stat, p_value, high_mean, low_mean = compare_language_resource_levels(df, metric_key)

        if p_value is not None:
            result = {
                'Metric': metric_label,
                'High-Resource Mean': high_mean,
                'Low-Resource Mean': low_mean,
                'Difference': low_mean - high_mean,
                'Mann-Whitney U': u_stat,
                'p-value': p_value,
                'Significant': p_value < 0.05,
                'Interpretation': 'Low-resource BETTER' if low_mean > high_mean and p_value < 0.05
                                  else 'High-resource BETTER' if high_mean > low_mean and p_value < 0.05
                                  else 'No significant difference'
            }
            results.append(result)

    return results


def format_stat_annotation(p_value):
    """Convert p-value to significance annotation."""
    if p_value is None:
        return ""
    elif p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return "ns"


def generate_markdown_tables(model_results, language_results):
    """Generate markdown tables for manuscript."""

    md = "# Statistical Test Results\n\n"
    md += "Generated automatically to address April's Comment #1\n\n"

    md += "## Table 1: Model Performance Comparisons\n\n"
    md += "*Kruskal-Wallis test with Dunn's post-hoc (Bonferroni correction)*\n\n"

    for result in model_results:
        md += f"\n### {result['Metric']}\n\n"

        # Model means table
        md += "| Model | Mean ± SD | n |\n"
        md += "|-------|-----------|---|\n"

        for model, stats in result['model_stats'].items():
            mean = stats['mean']
            std = stats['std']
            n = stats['n']
            md += f"| {model} | {mean:.4f} ± {std:.4f} | {n} |\n"

        # Kruskal-Wallis result
        kw_p = result['kruskal_wallis_p']
        sig_annotation = format_stat_annotation(kw_p)

        md += f"\n**Kruskal-Wallis test**: H = {result['kruskal_wallis_H']:.2f}, "
        md += f"p = {kw_p:.4f} {sig_annotation}\n\n"

        if result['significant']:
            md += "*Significant difference detected between models (p < 0.05)*\n\n"

            if result['dunn_results']:
                md += "**Dunn's post-hoc pairwise comparisons** (corrected p-values):\n\n"
                # Format Dunn's results as a matrix
                md += "| | " + " | ".join(result['dunn_results'].keys()) + " |\n"
                md += "|" + "-|" * (len(result['dunn_results']) + 1) + "\n"

                for model1, comparisons in result['dunn_results'].items():
                    row = f"| {model1} |"
                    for model2 in result['dunn_results'].keys():
                        p_val = comparisons.get(model2, None)
                        if p_val is not None and not np.isnan(p_val):
                            row += f" {p_val:.4f} {format_stat_annotation(p_val)} |"
                        else:
                            row += " - |"
                    md += row + "\n"
                md += "\n"
        else:
            md += "*No significant difference between models*\n\n"

    md += "\n## Table 2: Language Resource Level Comparisons\n\n"
    md += "*Mann-Whitney U test comparing high-resource vs low-resource languages*\n\n"

    md += "| Metric | High-Resource | Low-Resource | Difference | p-value | Interpretation |\n"
    md += "|--------|---------------|--------------|------------|---------|----------------|\n"

    for result in language_results:
        metric = result['Metric']
        high_mean = result['High-Resource Mean']
        low_mean = result['Low-Resource Mean']
        diff = result['Difference']
        p_val = result['p-value']
        sig = format_stat_annotation(p_val)
        interp = result['Interpretation']

        md += f"| {metric} | {high_mean:.4f} | {low_mean:.4f} | "
        md += f"{diff:+.4f} | {p_val:.4f} {sig} | {interp} |\n"

    md += "\n## Significance Key\n\n"
    md += "- *** : p < 0.001\n"
    md += "- ** : p < 0.01\n"
    md += "- * : p < 0.05\n"
    md += "- ns : not significant (p ≥ 0.05)\n"

    return md


def main():
    print("="*80)
    print("ADDING STATISTICAL SIGNIFICANCE TESTS")
    print("="*80)
    print()

    # Load data
    print("Loading metrics data...")
    df = load_data()
    print(f"Loaded {len(df)} metric records")
    print()

    # Model comparisons
    print("Performing model comparisons (Kruskal-Wallis + Dunn)...")
    model_results = generate_model_comparison_table(df)
    print(f"  Analyzed {len(model_results)} metrics")

    # Language resource level comparisons
    print("Performing language resource level comparisons (Mann-Whitney U)...")
    language_results = generate_language_comparison_table(df)
    print(f"  Analyzed {len(language_results)} metrics")
    print()

    # Save JSON results
    output_json = OUTPUT_DIR / "statistical_tests.json"
    with open(output_json, 'w') as f:
        json.dump({
            'model_comparisons': model_results,
            'language_comparisons': language_results
        }, f, indent=2, default=str)
    print(f"Saved JSON results: {output_json}")

    # Generate markdown tables
    markdown = generate_markdown_tables(model_results, language_results)
    output_md = OUTPUT_DIR / "statistical_tests.md"
    with open(output_md, 'w') as f:
        f.write(markdown)
    print(f"Saved markdown tables: {output_md}")

    # Print key findings
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)

    print("\nModel Comparisons:")
    for result in model_results:
        if result['significant']:
            print(f"  ✓ {result['Metric']}: SIGNIFICANT difference (p={result['kruskal_wallis_p']:.4f})")
        else:
            print(f"    {result['Metric']}: No significant difference (p={result['kruskal_wallis_p']:.4f})")

    print("\nLanguage Resource Level:")
    for result in language_results:
        print(f"  {result['Metric']}: {result['Interpretation']} (p={result['p-value']:.4f})")

    print("\n" + "="*80)
    print("Complete! Add these tables to your manuscript.")


if __name__ == "__main__":
    main()
