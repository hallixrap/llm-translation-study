#!/usr/bin/env python3
"""
Compute Missing Same-Language Metrics

Computes the same_lang metrics (BLEU, chrF, BERTScore, COMET) for the
hepatitis_b/claude-opus-4.5/arabic entry that was retried.

The professional Arabic translation exists at:
data/extracted_text/immunize/arabic/arabic_hepatitis_b.txt
"""

import json
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
PROF_TRANSLATION_FILE = BASE_DIR / "data" / "extracted_text" / "immunize" / "arabic" / "arabic_hepatitis_b.txt"

# =============================================================================
# METRIC FUNCTIONS (from calculate_medlineplus_metrics.py)
# =============================================================================

_bleu_scorer = None
_chrf_scorer = None
_bert_scorer = None
_comet_model = None

def get_bleu_scorer():
    global _bleu_scorer
    if _bleu_scorer is None:
        from sacrebleu.metrics import BLEU
        _bleu_scorer = BLEU(effective_order=True)
    return _bleu_scorer

def get_chrf_scorer():
    global _chrf_scorer
    if _chrf_scorer is None:
        from sacrebleu.metrics import CHRF
        _chrf_scorer = CHRF()
    return _chrf_scorer

def get_bert_scorer():
    global _bert_scorer
    if _bert_scorer is None:
        import bert_score
        _bert_scorer = bert_score
    return _bert_scorer

def get_comet_model():
    global _comet_model
    if _comet_model is None:
        try:
            from comet import download_model, load_from_checkpoint
            model_path = download_model("Unbabel/wmt22-comet-da")
            _comet_model = load_from_checkpoint(model_path)
        except Exception as e:
            print(f"COMET model not available: {e}")
            _comet_model = "unavailable"
    return _comet_model

def calculate_bleu(hypothesis: str, reference: str) -> float:
    scorer = get_bleu_scorer()
    score = scorer.corpus_score([hypothesis], [[reference]])
    return score.score

def calculate_chrf(hypothesis: str, reference: str) -> float:
    scorer = get_chrf_scorer()
    score = scorer.corpus_score([hypothesis], [[reference]])
    return score.score

def calculate_bertscore(hypothesis: str, reference: str, lang: str = "multilingual") -> float:
    bert_score = get_bert_scorer()
    P, R, F1 = bert_score.score([hypothesis], [reference], lang=lang, verbose=False)
    return F1.item()

def calculate_comet(source: str, translation: str, reference: str):
    model = get_comet_model()
    if model == "unavailable":
        return None
    try:
        data = [{"src": source, "mt": translation, "ref": reference}]
        output = model.predict(data, batch_size=1, accelerator='cpu', progress_bar=False)
        return output.scores[0]
    except Exception as e:
        print(f"COMET failed: {e}")
        return None

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Computing missing same_lang metrics for:")
    print("  immunize/hepatitis_b | claude-opus-4.5 | arabic")
    print("=" * 60)

    # Load data
    print("\n1. Loading data...")

    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
    print(f"   Loaded {len(results)} results")

    with open(METRICS_FILE, 'r') as f:
        metrics = json.load(f)
    print(f"   Loaded {len(metrics)} metrics entries")

    with open(PROF_TRANSLATION_FILE, 'r') as f:
        professional_translation = f.read()
    print(f"   Loaded professional translation: {len(professional_translation)} chars")

    # Find the relevant result and metrics entries
    result_entry = None
    metrics_idx = None

    for r in results:
        if (r.get('doc_id') == 'immunize/hepatitis_b' and
            r.get('model') == 'claude-opus-4.5' and
            r.get('language') == 'arabic'):
            result_entry = r
            break

    for i, m in enumerate(metrics):
        if (m.get('doc_id') == 'immunize/hepatitis_b' and
            m.get('model') == 'claude-opus-4.5' and
            m.get('language') == 'arabic'):
            metrics_idx = i
            break

    if result_entry is None:
        print("ERROR: Could not find result entry!")
        return
    if metrics_idx is None:
        print("ERROR: Could not find metrics entry!")
        return

    print(f"\n2. Found entries:")
    print(f"   Result: llm_translation = {len(result_entry.get('llm_translation', '') or '')} chars")
    print(f"   Metrics index: {metrics_idx}")

    llm_translation = result_entry.get('llm_translation', '')
    english_original = result_entry.get('english_original', '')

    if not llm_translation:
        print("ERROR: No LLM translation found!")
        return

    # Calculate same_lang metrics
    print("\n3. Calculating same_lang metrics...")

    print("   Computing BLEU...")
    same_lang_bleu = calculate_bleu(llm_translation, professional_translation)
    print(f"   BLEU: {same_lang_bleu:.2f}")

    print("   Computing chrF...")
    same_lang_chrf = calculate_chrf(llm_translation, professional_translation)
    print(f"   chrF: {same_lang_chrf:.2f}")

    print("   Computing BERTScore...")
    same_lang_bertscore = calculate_bertscore(llm_translation, professional_translation)
    print(f"   BERTScore: {same_lang_bertscore:.4f}")

    print("   Computing COMET...")
    same_lang_comet = calculate_comet(english_original, llm_translation, professional_translation)
    print(f"   COMET: {same_lang_comet:.4f}" if same_lang_comet else "   COMET: unavailable")

    # Update metrics
    print("\n4. Updating metrics file...")
    metrics[metrics_idx]['same_lang_bleu'] = same_lang_bleu
    metrics[metrics_idx]['same_lang_chrf'] = same_lang_chrf
    metrics[metrics_idx]['same_lang_bertscore'] = same_lang_bertscore
    metrics[metrics_idx]['same_lang_comet'] = same_lang_comet

    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   Saved updated metrics to {METRICS_FILE}")

    # Verify
    print("\n5. Verification:")
    print(f"   same_lang_bleu:     {metrics[metrics_idx]['same_lang_bleu']:.2f}")
    print(f"   same_lang_chrf:     {metrics[metrics_idx]['same_lang_chrf']:.2f}")
    print(f"   same_lang_bertscore: {metrics[metrics_idx]['same_lang_bertscore']:.4f}")
    print(f"   same_lang_comet:    {metrics[metrics_idx]['same_lang_comet']:.4f}" if metrics[metrics_idx]['same_lang_comet'] else "   same_lang_comet: unavailable")

    print("\n" + "=" * 60)
    print("DONE! Same-lang metrics computed successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()
