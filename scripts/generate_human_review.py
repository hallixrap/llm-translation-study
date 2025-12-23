#!/usr/bin/env python3
"""
Generate human review materials for bilingual reviewers.

Creates side-by-side comparisons of:
- Professional translation vs LLM translation (for bilingual review)
- Original English vs Back-translation (for semantic review)

Selects documents strategically:
- One high-scoring and one low-scoring document per language
- Focuses on documents with most variance between models
"""

import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
OUTPUT_DIR = BASE_DIR / "output" / "human_review"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model display names
MODEL_NAMES = {
    "gpt-5.1": "GPT-5.1",
    "claude-opus-4.5": "Claude Opus 4.5",
    "gemini-3-pro": "Gemini 3 Pro",
    "kimi-k2": "Kimi K2"
}


def load_data():
    """Load results and metrics."""
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        results = json.load(f)

    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        metrics = json.load(f)

    return results, metrics


def select_documents_for_review(metrics, language, n_docs=2, category='cancer'):
    """
    Select documents for review based on COMET variance across models.
    Returns one high-variance and one low-variance document.

    Args:
        category: 'cancer' for clean single-column docs, 'immunize' for VIS docs (have 2-column artifacts)
    """
    # Filter to language AND category (cancer docs have clean extraction, VIS docs have 2-column contamination)
    lang_metrics = [m for m in metrics
                    if m['language'] == language and m['doc_id'].startswith(category)]

    # Group by doc_id and calculate variance
    doc_scores = {}
    for m in lang_metrics:
        doc_id = m['doc_id']
        if doc_id not in doc_scores:
            doc_scores[doc_id] = []
        doc_scores[doc_id].append(m['same_lang_comet'])

    # Calculate variance and mean for each doc
    doc_stats = []
    for doc_id, scores in doc_scores.items():
        if len(scores) >= 2:
            import statistics
            variance = statistics.variance(scores) if len(scores) > 1 else 0
            mean = statistics.mean(scores)
            doc_stats.append({
                'doc_id': doc_id,
                'variance': variance,
                'mean_comet': mean,
                'scores': scores
            })

    # Sort by variance (descending) and pick top N
    doc_stats.sort(key=lambda x: x['variance'], reverse=True)

    # Return most interesting documents (highest variance = most disagreement between models)
    return doc_stats[:n_docs]


def generate_review_html(results, metrics, language, selected_docs, output_file):
    """Generate an HTML file for human review."""

    # Filter results for this language and selected docs
    doc_ids = [d['doc_id'] for d in selected_docs]
    lang_results = [r for r in results if r['language'] == language and r['doc_id'] in doc_ids]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human Review: {language.replace('_', ' ').title()} Translations</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 40px; }}
        h3 {{ color: #666; }}
        h4 {{ color: #777; margin-top: 20px; font-size: 14px; }}
        .instructions {{
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
        }}
        .document-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 15px 0;
        }}
        .text-box {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.6;
        }}
        .text-box.professional {{ border-left: 4px solid #28a745; }}
        .text-box.llm {{ border-left: 4px solid #007bff; }}
        .text-box.original {{ border-left: 4px solid #6c757d; }}
        .text-box.backtrans {{ border-left: 4px solid #ffc107; }}
        .label {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #495057;
        }}
        .metrics-badge {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 8px;
        }}
        .model-section {{
            border-top: 1px solid #dee2e6;
            padding-top: 20px;
            margin-top: 20px;
        }}
        .model-section:first-of-type {{
            border-top: none;
            padding-top: 0;
            margin-top: 0;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <h1>Human Review: {language.replace('_', ' ').title()} Translations</h1>

    <div class="instructions">
        <h3>Review Instructions</h3>
        <p><strong>For each document section below:</strong></p>
        <ol>
            <li><strong>Goal 2 - Compare translations:</strong> Read the Professional Translation (left) and LLM Translation (right) side by side.</li>
            <li><strong>Check for:</strong> Accuracy, fluency, medical terminology, cultural appropriateness</li>
            <li><strong>Goal 1 - LLM round-trip:</strong> Compare Original English to LLM Back-Translation to assess meaning preservation</li>
            <li><strong>Goal 3 - Professional round-trip:</strong> Compare Original English to Professional Back-Translation (baseline)</li>
            <li><strong>Note any issues:</strong> Missing information, mistranslations, awkward phrasing, errors</li>
        </ol>
        <p>These documents were selected from <strong>cancer education materials</strong> (clean single-column format) because they showed the <strong>highest variance</strong> in scores across different AI models.</p>
    </div>
"""

    # Group results by doc_id
    results_by_doc = {}
    for r in lang_results:
        doc_id = r['doc_id']
        if doc_id not in results_by_doc:
            results_by_doc[doc_id] = []
        results_by_doc[doc_id].append(r)

    for doc_id, doc_results in results_by_doc.items():
        # Get doc stats
        doc_stat = next((d for d in selected_docs if d['doc_id'] == doc_id), None)

        html_content += f"""
    <div class="document-section">
        <h2>Document: {doc_id.replace('/', ' - ').replace('_', ' ').replace('-', ' ').title()}</h2>
        <p>
            <span class="metrics-badge">Mean COMET: {doc_stat['mean_comet']:.3f}</span>
            <span class="metrics-badge">Variance: {doc_stat['variance']:.4f}</span>
        </p>

        <h3>Original English Text</h3>
        <div class="text-box original">{doc_results[0]['english_original']}</div>
"""

        # Add each model's translations
        for result in doc_results:
            model_name = MODEL_NAMES.get(result['model'], result['model'])

            # Find metrics for this result
            result_metrics = next((m for m in metrics
                                   if m['doc_id'] == doc_id
                                   and m['model'] == result['model']
                                   and m['language'] == language), None)

            metrics_html = ""
            if result_metrics:
                g3_bleu = result_metrics.get('prof_backtrans_bleu', 0)
                g3_bleu_str = f"{g3_bleu:.1f}" if g3_bleu else "N/A"
                metrics_html = f"""
            <p>
                <span class="metrics-badge">G2 BLEU: {result_metrics.get('same_lang_bleu', 0):.1f}</span>
                <span class="metrics-badge">G2 COMET: {result_metrics.get('same_lang_comet', 0):.3f}</span>
                <span class="metrics-badge">G1 BLEU: {result_metrics.get('backtrans_bleu', 0):.1f}</span>
                <span class="metrics-badge">G3 BLEU: {g3_bleu_str}</span>
            </p>
"""

            html_content += f"""
        <div class="model-section">
            <h3>{model_name}</h3>
            {metrics_html}

            <div class="comparison-grid">
                <div>
                    <div class="label">Professional Translation</div>
                    <div class="text-box professional">{result['professional_translation']}</div>
                </div>
                <div>
                    <div class="label">LLM Translation</div>
                    <div class="text-box llm">{result['llm_translation']}</div>
                </div>
            </div>

            <div class="comparison-grid">
                <div>
                    <div class="label">Original English (reference)</div>
                    <div class="text-box original">{result['english_original']}</div>
                </div>
                <div>
                    <div class="label">LLM Back-Translation (Goal 1)</div>
                    <div class="text-box backtrans">{result['llm_back_translation']}</div>
                </div>
            </div>

            <h4>Goal 3: Professional Translation Back-translated</h4>
            <div class="comparison-grid">
                <div>
                    <div class="label">Original English (reference)</div>
                    <div class="text-box original">{result['english_original']}</div>
                </div>
                <div>
                    <div class="label">Professional Back-Translation (Goal 3)</div>
                    <div class="text-box professional">{result.get('professional_back_translation', 'N/A')}</div>
                </div>
            </div>
        </div>
"""

        html_content += "    </div>\n"

    html_content += """
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated: {output_file}")


def main():
    print("Loading data...")
    results, metrics = load_data()

    # Languages for bilingual review
    review_languages = ['chinese_simplified', 'spanish']

    for language in review_languages:
        print(f"\n=== {language.replace('_', ' ').title()} ===")

        # Select documents
        selected_docs = select_documents_for_review(metrics, language, n_docs=2)

        print("Selected documents for review:")
        for doc in selected_docs:
            print(f"  - {doc['doc_id']}: mean={doc['mean_comet']:.3f}, var={doc['variance']:.4f}")

        # Generate HTML review file
        output_file = OUTPUT_DIR / f"review_{language}.html"
        generate_review_html(results, metrics, language, selected_docs, output_file)

    print(f"\nAll review files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
