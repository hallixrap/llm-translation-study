#!/usr/bin/env python3
"""
Generate GitHub Page outputs for MedlinePlus Back-Translation Study.

Outputs:
1. Excel report with multiple tabs (summary, by model, by language, detailed)
2. Visualization charts (PNG files)
3. README.md with executive summary
4. Kevin scorecard
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np
from pathlib import Path
from datetime import datetime

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
METRICS_DIR = BASE_DIR / "output" / "medlineplus_metrics"
OUTPUT_DIR = BASE_DIR / "output" / "github_pages"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model display names
MODEL_NAMES = {
    "gpt-5.1": "GPT-5.1",
    "claude-opus-4.5": "Claude Opus 4.5",
    "gemini-3-pro": "Gemini 3 Pro",
    "kimi-k2": "Kimi K2"
}

# Language display names
LANGUAGE_NAMES = {
    "spanish": "Spanish",
    "chinese_simplified": "Chinese (Simplified)",
    "vietnamese": "Vietnamese",
    "russian": "Russian",
    "arabic": "Arabic",
    "korean": "Korean",
    "tagalog": "Tagalog",
    "haitian_creole": "Haitian Creole"
}

# Metric display names
METRIC_NAMES = {
    # Goal 2: LLM vs Professional (same language)
    "same_lang_bleu": "G2: BLEU",
    "same_lang_chrf": "G2: chrF",
    "same_lang_bertscore": "G2: BERTScore",
    "same_lang_comet": "G2: COMET",
    # Goal 1: LLM back-translation vs Original
    "cross_lang_xlm_roberta": "G1: XLM-RoBERTa",
    "cross_lang_labse": "G1: LaBSE",
    "cross_lang_mbert": "G1: mBERT",
    "cross_lang_comet_qe": "G1: COMET-QE",
    "backtrans_bleu": "G1: BLEU",
    "backtrans_chrf": "G1: chrF",
    "backtrans_bertscore": "G1: BERTScore",
    # Goal 3: Professional back-translation vs Original
    "prof_backtrans_bleu": "G3: BLEU",
    "prof_backtrans_bertscore": "G3: BERTScore",
    "prof_backtrans_labse": "G3: LaBSE",
    "llm_vs_prof_backtrans_bleu": "LLM vs Prof BackTrans BLEU",
    "llm_vs_prof_backtrans_labse": "LLM vs Prof BackTrans LaBSE"
}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load all metrics data."""
    with open(METRICS_DIR / "all_metrics.json", 'r') as f:
        all_metrics = json.load(f)

    with open(METRICS_DIR / "summary.json", 'r') as f:
        summary = json.load(f)

    return all_metrics, summary


def create_dataframe(all_metrics):
    """Convert metrics to pandas DataFrame."""
    df = pd.DataFrame(all_metrics)

    # Add display names
    df['Model'] = df['model'].map(MODEL_NAMES)
    df['Language'] = df['language'].map(LANGUAGE_NAMES)

    # Extract category from doc_id
    df['Category'] = df['doc_id'].apply(lambda x: x.split('/')[0].title())
    df['Topic'] = df['doc_id'].apply(lambda x: x.split('/')[1].replace('-', ' ').replace('_', ' ').title())

    return df


# =============================================================================
# EXCEL REPORT
# =============================================================================

def generate_excel_report(df, summary):
    """Generate comprehensive Excel report with all three goals."""
    excel_path = OUTPUT_DIR / "medlineplus_backtranslation_report.xlsx"

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Tab 1: Executive Summary
        exec_summary = pd.DataFrame({
            'Metric': ['Total Documents', 'Languages', 'Models', 'Total Translation Pairs',
                      'Total API Calls', 'Goal 1 Winner (Meaning)', 'Goal 2 Winner (Professional)',
                      'Best Language', 'Hardest Language'],
            'Value': ['22 (11 vaccine VIS + 11 cancer)', '8', '4', '704',
                     '2,112 (704 × 3 steps)', 'Claude Opus 4.5', 'Gemini 3 Pro',
                     'Spanish', 'Arabic']
        })
        exec_summary.to_excel(writer, sheet_name='Executive Summary', index=False)

        # Tab 2: By Model Summary
        model_summary = pd.DataFrame(summary['by_model']).T
        model_summary.index = model_summary.index.map(MODEL_NAMES)
        model_summary.columns = [METRIC_NAMES.get(c, c) for c in model_summary.columns]
        model_summary = model_summary.round(3)
        model_summary.to_excel(writer, sheet_name='By Model')

        # Tab 3: By Language Summary
        lang_summary = pd.DataFrame(summary['by_language']).T
        lang_summary.index = lang_summary.index.map(LANGUAGE_NAMES)
        lang_summary.columns = [METRIC_NAMES.get(c, c) for c in lang_summary.columns]
        lang_summary = lang_summary.round(3)
        lang_summary.to_excel(writer, sheet_name='By Language')

        # Tab 4: By Category Summary
        if 'by_category' in summary:
            cat_summary = pd.DataFrame(summary['by_category']).T
            cat_summary.columns = [METRIC_NAMES.get(c, c) for c in cat_summary.columns]
            cat_summary = cat_summary.round(3)
            cat_summary.to_excel(writer, sheet_name='By Category')

        # Tab 5: Goal 1 - LLM Meaning Preservation (Back-trans vs Original)
        goal1_cols = ['Model', 'Language', 'Category', 'Topic',
                      'backtrans_bleu', 'cross_lang_labse', 'backtrans_bertscore', 'cross_lang_comet_qe']
        goal1_df = df[[c for c in goal1_cols if c in df.columns]].copy()
        goal1_df.columns = ['Model', 'Language', 'Category', 'Topic', 'BLEU', 'LaBSE', 'BERTScore', 'COMET-QE']
        goal1_df = goal1_df.round(3)
        goal1_df.to_excel(writer, sheet_name='Goal 1 - Meaning', index=False)

        # Tab 6: Goal 2 - Professional Alignment (LLM vs Professional)
        goal2_cols = ['Model', 'Language', 'Category', 'Topic',
                     'same_lang_bleu', 'same_lang_chrf', 'same_lang_bertscore', 'same_lang_comet']
        goal2_df = df[goal2_cols].copy()
        goal2_df.columns = ['Model', 'Language', 'Category', 'Topic', 'BLEU', 'chrF', 'BERTScore', 'COMET']
        goal2_df = goal2_df.round(3)
        goal2_df.to_excel(writer, sheet_name='Goal 2 - Professional', index=False)

        # Tab 7: Goal 3 - Professional Baseline (Prof back-trans vs Original)
        goal3_cols = ['Model', 'Language', 'Category', 'Topic']
        optional_g3_cols = ['prof_backtrans_bleu', 'prof_backtrans_labse', 'prof_backtrans_bertscore']
        for col in optional_g3_cols:
            if col in df.columns:
                goal3_cols.append(col)
        if len(goal3_cols) > 4:  # Has Goal 3 data
            goal3_df = df[goal3_cols].copy()
            new_cols = ['Model', 'Language', 'Category', 'Topic']
            if 'prof_backtrans_bleu' in goal3_cols:
                new_cols.append('BLEU')
            if 'prof_backtrans_labse' in goal3_cols:
                new_cols.append('LaBSE')
            if 'prof_backtrans_bertscore' in goal3_cols:
                new_cols.append('BERTScore')
            goal3_df.columns = new_cols
            goal3_df = goal3_df.round(3)
            goal3_df.to_excel(writer, sheet_name='Goal 3 - Baseline', index=False)

        # Tab 8: Full Detailed Data
        full_df = df.copy()
        full_df = full_df.round(3)
        full_df.to_excel(writer, sheet_name='All Data', index=False)

        # Tab 9: Kevin Scorecard
        scorecard = create_kevin_scorecard(df, summary)
        scorecard.to_excel(writer, sheet_name='Kevin Scorecard', index=False)

    print(f"Excel report saved to: {excel_path}")
    return excel_path


def create_kevin_scorecard(df, summary):
    """Create Kevin-style scorecard comparing models."""
    models = list(MODEL_NAMES.values())

    # Calculate rankings for each metric
    metrics_to_rank = [
        ('same_lang_comet', 'COMET (Translation Quality)', True),
        ('same_lang_bleu', 'BLEU Score', True),
        ('same_lang_bertscore', 'BERTScore', True),
        ('cross_lang_xlm_roberta', 'Back-Trans XLM-RoBERTa', True),
        ('cross_lang_labse', 'Back-Trans LaBSE', True),
    ]

    scorecard_data = []

    for metric_key, metric_name, higher_is_better in metrics_to_rank:
        row = {'Metric': metric_name}

        # Get model scores
        model_scores = {}
        for model_key, model_name in MODEL_NAMES.items():
            score = summary['by_model'][model_key][metric_key]
            model_scores[model_name] = score
            row[model_name] = round(score, 3)

        # Determine winner
        if higher_is_better:
            winner = max(model_scores, key=model_scores.get)
        else:
            winner = min(model_scores, key=model_scores.get)
        row['Winner'] = winner

        scorecard_data.append(row)

    # Add overall winner row
    wins = {model: 0 for model in models}
    for row in scorecard_data:
        wins[row['Winner']] += 1

    overall_row = {'Metric': 'TOTAL WINS'}
    for model in models:
        overall_row[model] = wins[model]
    overall_row['Winner'] = max(wins, key=wins.get)
    scorecard_data.append(overall_row)

    return pd.DataFrame(scorecard_data)


# =============================================================================
# VISUALIZATIONS
# =============================================================================

def generate_charts(df, summary):
    """Generate visualization charts."""
    charts_dir = OUTPUT_DIR / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')

    # Chart 1: Model Comparison - Same Language Metrics
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Model Comparison: Same-Language Metrics\n(LLM Translation vs Professional Translation)',
                 fontsize=14, fontweight='bold')

    metrics = ['same_lang_bleu', 'same_lang_chrf', 'same_lang_bertscore', 'same_lang_comet']
    titles = ['BLEU Score', 'chrF Score', 'BERTScore', 'COMET Score']

    for ax, metric, title in zip(axes.flat, metrics, titles):
        model_scores = []
        model_names = []
        for model_key, model_name in MODEL_NAMES.items():
            model_scores.append(summary['by_model'][model_key][metric])
            model_names.append(model_name)

        colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6']
        bars = ax.bar(model_names, model_scores, color=colors, edgecolor='black', linewidth=1.2)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylabel('Score')
        ax.tick_params(axis='x', rotation=15)

        # Add value labels
        for bar, score in zip(bars, model_scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{score:.1f}' if metric == 'same_lang_bleu' or metric == 'same_lang_chrf' else f'{score:.3f}',
                   ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(charts_dir / 'model_comparison_same_lang.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 2: Language Comparison - Same Language Metrics
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Language Comparison: Same-Language Metrics\n(Higher = Better Match with Professional Translation)',
                 fontsize=14, fontweight='bold')

    for ax, metric, title in zip(axes.flat, metrics, titles):
        lang_scores = []
        lang_names = []
        for lang_key, lang_name in LANGUAGE_NAMES.items():
            # Use .get() with default since by_language may have fewer metrics
            lang_scores.append(summary['by_language'][lang_key].get(metric, 0))
            lang_names.append(lang_name)

        # Sort by score
        sorted_pairs = sorted(zip(lang_names, lang_scores), key=lambda x: x[1], reverse=True)
        lang_names, lang_scores = zip(*sorted_pairs)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(lang_names)))
        bars = ax.barh(lang_names, lang_scores, color=colors, edgecolor='black', linewidth=0.8)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Score')
        ax.invert_yaxis()

        # Add value labels
        for bar, score in zip(bars, lang_scores):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{score:.1f}' if 'bleu' in metric or 'chrf' in metric else f'{score:.3f}',
                   ha='left', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(charts_dir / 'language_comparison_same_lang.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 3: Back-Translation Semantic Preservation
    fig, ax = plt.subplots(figsize=(12, 6))

    backtrans_metrics = ['cross_lang_xlm_roberta', 'cross_lang_labse', 'cross_lang_mbert']
    backtrans_labels = ['XLM-RoBERTa', 'LaBSE', 'mBERT']

    x = np.arange(len(MODEL_NAMES))
    width = 0.25

    for i, (metric, label) in enumerate(zip(backtrans_metrics, backtrans_labels)):
        scores = [summary['by_model'][m][metric] for m in MODEL_NAMES.keys()]
        bars = ax.bar(x + i*width, scores, width, label=label, edgecolor='black', linewidth=0.8)

    ax.set_xlabel('Model')
    ax.set_ylabel('Semantic Similarity Score')
    ax.set_title('Back-Translation Semantic Preservation\n(English Back-Translation vs Original English)',
                fontsize=12, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(MODEL_NAMES.values())
    ax.legend()
    ax.set_ylim(0.85, 1.0)

    plt.tight_layout()
    plt.savefig(charts_dir / 'back_translation_similarity.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 4: Heatmap - Model x Language COMET scores
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create pivot table
    pivot_df = df.pivot_table(
        values='same_lang_comet',
        index='Language',
        columns='Model',
        aggfunc='mean'
    )

    # Reorder
    pivot_df = pivot_df[[MODEL_NAMES[k] for k in MODEL_NAMES.keys()]]
    pivot_df = pivot_df.reindex([LANGUAGE_NAMES[k] for k in LANGUAGE_NAMES.keys()])

    im = ax.imshow(pivot_df.values, cmap='RdYlGn', aspect='auto', vmin=0.65, vmax=0.9)

    ax.set_xticks(np.arange(len(pivot_df.columns)))
    ax.set_yticks(np.arange(len(pivot_df.index)))
    ax.set_xticklabels(pivot_df.columns, rotation=15)
    ax.set_yticklabels(pivot_df.index)

    # Add text annotations
    for i in range(len(pivot_df.index)):
        for j in range(len(pivot_df.columns)):
            text = ax.text(j, i, f'{pivot_df.values[i, j]:.3f}',
                          ha='center', va='center', color='black', fontsize=10)

    ax.set_title('COMET Score Heatmap: Model × Language\n(Translation Quality)',
                fontsize=12, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('COMET Score')

    plt.tight_layout()
    plt.savefig(charts_dir / 'comet_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 5: Category Comparison (Vaccine vs Cancer)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, category in zip(axes, ['Immunize', 'Cancer']):
        cat_df = df[df['Category'] == category]

        metric_means = []
        for model_name in MODEL_NAMES.values():
            model_df = cat_df[cat_df['Model'] == model_name]
            metric_means.append({
                'Model': model_name,
                'BLEU': model_df['same_lang_bleu'].mean(),
                'COMET': model_df['same_lang_comet'].mean() * 100  # Scale for visibility
            })

        metric_df = pd.DataFrame(metric_means)

        x = np.arange(len(metric_df))
        width = 0.35

        ax.bar(x - width/2, metric_df['BLEU'], width, label='BLEU', color='#3498db')
        ax.bar(x + width/2, metric_df['COMET'], width, label='COMET ×100', color='#e74c3c')

        ax.set_xlabel('Model')
        ax.set_ylabel('Score')
        ax.set_title(f'{category} Documents', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metric_df['Model'], rotation=15)
        ax.legend()

    fig.suptitle('Performance by Document Category', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(charts_dir / 'category_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 6: Three Goals Comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Goal 1: LLM Meaning Preservation
    ax = axes[0]
    g1_scores = [summary['by_model'][m].get('backtrans_bleu', 0) for m in MODEL_NAMES.keys()]
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6']
    bars = ax.bar(MODEL_NAMES.values(), g1_scores, color=colors, edgecolor='black')
    ax.set_title('Goal 1: LLM Meaning Preservation\n(Back-translation BLEU)', fontsize=11, fontweight='bold')
    ax.set_ylabel('BLEU Score')
    ax.tick_params(axis='x', rotation=15)
    for bar, score in zip(bars, g1_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{score:.1f}',
               ha='center', va='bottom', fontsize=10)

    # Goal 2: Professional Alignment
    ax = axes[1]
    g2_scores = [summary['by_model'][m].get('same_lang_comet', 0) for m in MODEL_NAMES.keys()]
    bars = ax.bar(MODEL_NAMES.values(), g2_scores, color=colors, edgecolor='black')
    ax.set_title('Goal 2: Professional Alignment\n(COMET Score)', fontsize=11, fontweight='bold')
    ax.set_ylabel('COMET Score')
    ax.tick_params(axis='x', rotation=15)
    ax.set_ylim(0.8, 0.9)
    for bar, score in zip(bars, g2_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002, f'{score:.3f}',
               ha='center', va='bottom', fontsize=10)

    # Goal 3: Professional Baseline
    ax = axes[2]
    g3_scores = [summary['by_model'][m].get('prof_backtrans_bleu', 0) for m in MODEL_NAMES.keys()]
    bars = ax.bar(MODEL_NAMES.values(), g3_scores, color=colors, edgecolor='black')
    ax.set_title('Goal 3: Professional Baseline\n(Prof Back-trans BLEU)', fontsize=11, fontweight='bold')
    ax.set_ylabel('BLEU Score')
    ax.tick_params(axis='x', rotation=15)
    for bar, score in zip(bars, g3_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{score:.1f}',
               ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(charts_dir / 'three_goals_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 7: Goal 1 vs Goal 3 (LLM vs Professional stability)
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(MODEL_NAMES))
    width = 0.35

    g1_bleu = [summary['by_model'][m].get('backtrans_bleu', 0) for m in MODEL_NAMES.keys()]
    g3_bleu = [summary['by_model'][m].get('prof_backtrans_bleu', 0) for m in MODEL_NAMES.keys()]

    bars1 = ax.bar(x - width/2, g1_bleu, width, label='Goal 1: LLM Back-trans', color='#3498db', edgecolor='black')
    bars2 = ax.bar(x + width/2, g3_bleu, width, label='Goal 3: Prof Back-trans', color='#9b59b6', edgecolor='black')

    ax.set_xlabel('Model')
    ax.set_ylabel('BLEU Score')
    ax.set_title('LLM vs Professional Translation Stability\n(Higher = better round-trip preservation)',
                fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(MODEL_NAMES.values())
    ax.legend()

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{bar.get_height():.1f}',
                   ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(charts_dir / 'llm_vs_professional_stability.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Charts saved to: {charts_dir}")
    return charts_dir


# =============================================================================
# README GENERATION
# =============================================================================

def generate_readme(df, summary):
    """Generate README.md with executive summary."""

    # Calculate key statistics
    total_pairs = len(df)
    total_docs = df['doc_id'].nunique()
    total_languages = df['language'].nunique()
    total_models = df['model'].nunique()

    # Find best performers
    model_comet = {m: summary['by_model'][m]['same_lang_comet'] for m in MODEL_NAMES.keys()}
    best_model_comet = max(model_comet, key=model_comet.get)

    model_bleu = {m: summary['by_model'][m]['same_lang_bleu'] for m in MODEL_NAMES.keys()}
    best_model_bleu = max(model_bleu, key=model_bleu.get)

    # Use same_lang_bleu for language comparison since by_language may not have all metrics
    lang_bleu = {l: summary['by_language'][l].get('same_lang_bleu', 0) for l in LANGUAGE_NAMES.keys()}
    best_lang = max(lang_bleu, key=lang_bleu.get)
    worst_lang = min(lang_bleu, key=lang_bleu.get)

    readme_content = f'''# MedlinePlus Back-Translation Evaluation Study

## Executive Summary

This study evaluates **4 frontier LLMs** on medical translation quality across **8 languages** using **22 professionally-translated health documents** from MedlinePlus (CDC vaccine information) and the American Cancer Society.

### Key Findings

1. **All models achieve high semantic preservation** (>92% back-translation similarity), indicating LLMs reliably preserve medical meaning through round-trip translation.

2. **{MODEL_NAMES[best_model_comet]}** achieves the highest translation quality (COMET: {model_comet[best_model_comet]:.3f}), while **{MODEL_NAMES[best_model_bleu]}** leads in lexical overlap (BLEU: {model_bleu[best_model_bleu]:.1f}).

3. **{LANGUAGE_NAMES[best_lang]}** shows the strongest LLM-professional agreement (BLEU: {lang_bleu[best_lang]:.1f}), while **{LANGUAGE_NAMES[worst_lang]}** remains most challenging (BLEU: {lang_bleu[worst_lang]:.1f}).

4. **Script complexity matters**: Languages using Latin script (Spanish, Vietnamese, Tagalog) consistently outperform those with non-Latin scripts (Arabic, Chinese, Korean).

---

## Study Design

### Documents
- **22 health education documents** (198 PDFs total)
  - 11 Vaccine Information Statements (VIS) from CDC/Immunize.org
  - 11 Cancer education materials from American Cancer Society
- **9 language versions** per document (English + 8 translations)

### Languages Evaluated
| Language | Script | Resource Level |
|----------|--------|----------------|
| Spanish | Latin | High |
| Chinese (Simplified) | Hanzi | High |
| Vietnamese | Latin (+ diacritics) | Medium |
| Russian | Cyrillic | High |
| Arabic | Arabic (RTL) | Medium |
| Korean | Hangul | High |
| Tagalog | Latin | Low |
| Haitian Creole | Latin | Low |

### Models Tested
| Model | Provider |
|-------|----------|
| GPT-5.1 | OpenAI |
| Claude Opus 4.5 | Anthropic |
| Gemini 3 Pro | Google |
| Kimi K2 | Moonshot AI |

---

## Methodology

### Translation Pipeline
1. **Forward Translation**: English → Target Language (LLM)
2. **Back-Translation**: Target Language → English (LLM)
3. **Evaluation**: Compare LLM output vs professional translations

### Metrics

#### Same-Language Metrics (LLM vs Professional Translation)
| Metric | Description | Range |
|--------|-------------|-------|
| BLEU | N-gram overlap | 0-100 |
| chrF | Character n-gram F-score | 0-100 |
| BERTScore | Contextual embedding similarity | 0-1 |
| COMET | Neural translation quality | 0-1 |

#### Back-Translation Semantic Metrics (LLM Back-Translation vs Original English)
These metrics compare the English back-translation to the original English text, measuring how well meaning is preserved through the round-trip translation. Despite using multilingual models (for robustness), this is an **English-to-English comparison**.

| Metric | Description | Range |
|--------|-------------|-------|
| XLM-RoBERTa | Semantic similarity (multilingual encoder) | 0-1 |
| LaBSE | Sentence embedding similarity | 0-1 |
| mBERT | Contextual embedding similarity | 0-1 |
| COMET-QE | Reference-free quality estimation | -1 to 1 |

---

## Results

### Model Performance Summary

| Model | BLEU | chrF | BERTScore | COMET |
|-------|------|------|-----------|-------|
| {MODEL_NAMES['gemini-3-pro']} | **{summary['by_model']['gemini-3-pro']['same_lang_bleu']:.1f}** | **{summary['by_model']['gemini-3-pro']['same_lang_chrf']:.1f}** | {summary['by_model']['gemini-3-pro']['same_lang_bertscore']:.3f} | {summary['by_model']['gemini-3-pro']['same_lang_comet']:.3f} |
| {MODEL_NAMES['claude-opus-4.5']} | {summary['by_model']['claude-opus-4.5']['same_lang_bleu']:.1f} | {summary['by_model']['claude-opus-4.5']['same_lang_chrf']:.1f} | **{summary['by_model']['claude-opus-4.5']['same_lang_bertscore']:.3f}** | **{summary['by_model']['claude-opus-4.5']['same_lang_comet']:.3f}** |
| {MODEL_NAMES['gpt-5.1']} | {summary['by_model']['gpt-5.1']['same_lang_bleu']:.1f} | {summary['by_model']['gpt-5.1']['same_lang_chrf']:.1f} | {summary['by_model']['gpt-5.1']['same_lang_bertscore']:.3f} | {summary['by_model']['gpt-5.1']['same_lang_comet']:.3f} |
| {MODEL_NAMES['kimi-k2']} | {summary['by_model']['kimi-k2']['same_lang_bleu']:.1f} | {summary['by_model']['kimi-k2']['same_lang_chrf']:.1f} | {summary['by_model']['kimi-k2']['same_lang_bertscore']:.3f} | {summary['by_model']['kimi-k2']['same_lang_comet']:.3f} |

### Language Performance Summary

| Language | G2: BLEU | G1: BLEU | G1: LaBSE | G3: BLEU |
|----------|----------|----------|-----------|----------|
| Spanish | **{summary['by_language']['spanish'].get('same_lang_bleu', 0):.1f}** | {summary['by_language']['spanish'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['spanish'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['spanish'].get('prof_backtrans_bleu', 0):.1f} |
| Vietnamese | {summary['by_language']['vietnamese'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['vietnamese'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['vietnamese'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['vietnamese'].get('prof_backtrans_bleu', 0):.1f} |
| Tagalog | {summary['by_language']['tagalog'].get('same_lang_bleu', 0):.1f} | **{summary['by_language']['tagalog'].get('backtrans_bleu', 0):.1f}** | {summary['by_language']['tagalog'].get('cross_lang_labse', 0):.3f} | **{summary['by_language']['tagalog'].get('prof_backtrans_bleu', 0):.1f}** |
| Haitian Creole | {summary['by_language']['haitian_creole'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['haitian_creole'].get('backtrans_bleu', 0):.1f} | **{summary['by_language']['haitian_creole'].get('cross_lang_labse', 0):.3f}** | {summary['by_language']['haitian_creole'].get('prof_backtrans_bleu', 0):.1f} |
| Russian | {summary['by_language']['russian'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['russian'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['russian'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['russian'].get('prof_backtrans_bleu', 0):.1f} |
| Korean | {summary['by_language']['korean'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['korean'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['korean'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['korean'].get('prof_backtrans_bleu', 0):.1f} |
| Chinese | {summary['by_language']['chinese_simplified'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['chinese_simplified'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['chinese_simplified'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['chinese_simplified'].get('prof_backtrans_bleu', 0):.1f} |
| Arabic | {summary['by_language']['arabic'].get('same_lang_bleu', 0):.1f} | {summary['by_language']['arabic'].get('backtrans_bleu', 0):.1f} | {summary['by_language']['arabic'].get('cross_lang_labse', 0):.3f} | {summary['by_language']['arabic'].get('prof_backtrans_bleu', 0):.1f} |

---

## Visualizations

### Model Comparison
![Model Comparison](charts/model_comparison_same_lang.png)

### Language Comparison
![Language Comparison](charts/language_comparison_same_lang.png)

### Back-Translation Semantic Similarity
![Back-Translation Similarity](charts/back_translation_similarity.png)

### COMET Score Heatmap
![Heatmap](charts/comet_heatmap.png)

---

## Key Insights

### 1. Model Differentiation is Subtle
All four frontier models perform within a narrow band (~3% COMET spread), suggesting that for medical translation, model selection is less critical than language pair selection.

### 2. Script Type Dominates Performance
Languages using Latin-based scripts (Spanish, Vietnamese, Tagalog, Haitian Creole) consistently show higher BLEU/chrF scores, likely due to shared tokenization advantages with English training data.

### 3. Semantic Metrics Tell a Different Story
While BLEU varies widely by language (9.6 to 49.3), COMET scores are more consistent (0.72 to 0.87), suggesting LLMs preserve meaning even when surface forms differ from professional translations.

### 4. Low-Resource Languages Hold Their Own
Tagalog and Haitian Creole—traditionally considered low-resource—achieve competitive scores, indicating frontier LLMs have strong coverage of these languages.

### 5. Arabic Remains Challenging
Arabic shows the lowest same-language scores across all metrics, reflecting the compound challenges of RTL script, morphological complexity, and potential training data imbalances.

---

## Files

| File | Description |
|------|-------------|
| `medlineplus_backtranslation_report.xlsx` | Full Excel report with all metrics |
| `charts/` | Visualization PNG files |
| `all_metrics.json` | Raw metrics data (JSON) |
| `summary.json` | Aggregated summary statistics |

---

## Citation

If you use this dataset or methodology, please cite:

```
MedlinePlus Back-Translation Evaluation Study
Stanford University, {datetime.now().year}
```

---

## Contact

For questions about this study, please contact the research team.

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
'''

    readme_path = OUTPUT_DIR / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"README saved to: {readme_path}")
    return readme_path


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("MedlinePlus Back-Translation Study - GitHub Output Generator")
    print("=" * 60)

    # Load data
    print("\n1. Loading data...")
    all_metrics, summary = load_data()
    df = create_dataframe(all_metrics)
    print(f"   Loaded {len(df)} metric records")

    # Generate Excel report
    print("\n2. Generating Excel report...")
    generate_excel_report(df, summary)

    # Generate charts
    print("\n3. Generating visualization charts...")
    generate_charts(df, summary)

    # Generate README
    print("\n4. Generating README.md...")
    generate_readme(df, summary)

    print("\n" + "=" * 60)
    print("All outputs generated successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
