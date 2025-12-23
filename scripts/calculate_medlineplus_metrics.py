#!/usr/bin/env python3
"""
MedlinePlus Metrics Calculation

Calculates all metrics for the back-translation evaluation:

SAME-LANGUAGE METRICS (LLM translation vs Professional translation):
- BLEU
- chrF
- BERTScore
- COMET

CROSS-LANGUAGE METRICS (Back-translation vs Original English):
- XLM-RoBERTa similarity
- LaBSE similarity
- mBERT similarity
- COMET-QE

Output: Results table matching poster format
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List
import numpy as np

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import logger, METRICS_DIR

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path("/Users/chukanya/Documents/Coding/Back translation project")
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
OUTPUT_DIR = BASE_DIR / "output" / "medlineplus_metrics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LAZY-LOADED MODELS
# =============================================================================

_bleu_scorer = None
_chrf_scorer = None
_bert_scorer = None
_comet_model = None
_comet_qe_model = None
_labse_model = None
_xlm_roberta_model = None
_mbert_model = None


def get_bleu_scorer():
    global _bleu_scorer
    if _bleu_scorer is None:
        from sacrebleu.metrics import BLEU
        _bleu_scorer = BLEU(effective_order=True)
        logger.info("BLEU scorer initialized")
    return _bleu_scorer


def get_chrf_scorer():
    global _chrf_scorer
    if _chrf_scorer is None:
        from sacrebleu.metrics import CHRF
        _chrf_scorer = CHRF()
        logger.info("chrF scorer initialized")
    return _chrf_scorer


def get_bert_scorer():
    global _bert_scorer
    if _bert_scorer is None:
        import bert_score
        _bert_scorer = bert_score
        logger.info("BERTScore initialized")
    return _bert_scorer


def get_comet_model():
    global _comet_model
    if _comet_model is None:
        try:
            from comet import download_model, load_from_checkpoint
            model_path = download_model("Unbabel/wmt22-comet-da")
            _comet_model = load_from_checkpoint(model_path)
            logger.info("COMET model initialized")
        except Exception as e:
            logger.warning(f"COMET model not available: {e}")
            _comet_model = "unavailable"
    return _comet_model


def get_comet_qe_model():
    global _comet_qe_model
    if _comet_qe_model is None:
        try:
            from comet import download_model, load_from_checkpoint
            # Use reference-free model that works
            model_path = download_model("Unbabel/wmt20-comet-qe-da")
            _comet_qe_model = load_from_checkpoint(model_path)
            logger.info("COMET-QE model initialized")
        except Exception as e:
            logger.warning(f"COMET-QE model not available: {e}")
            _comet_qe_model = "unavailable"
    return _comet_qe_model


def get_labse_model():
    global _labse_model
    if _labse_model is None:
        from sentence_transformers import SentenceTransformer
        _labse_model = SentenceTransformer('sentence-transformers/LaBSE')
        logger.info("LaBSE model initialized")
    return _labse_model


def get_xlm_roberta_model():
    global _xlm_roberta_model
    if _xlm_roberta_model is None:
        from sentence_transformers import SentenceTransformer
        _xlm_roberta_model = SentenceTransformer('sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens')
        logger.info("XLM-RoBERTa model initialized")
    return _xlm_roberta_model


def get_mbert_model():
    global _mbert_model
    if _mbert_model is None:
        from sentence_transformers import SentenceTransformer
        # Use a working multilingual BERT model
        _mbert_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("mBERT model initialized")
    return _mbert_model


# =============================================================================
# METRIC CALCULATIONS
# =============================================================================

def calculate_bleu(hypothesis: str, reference: str) -> float:
    scorer = get_bleu_scorer()
    score = scorer.corpus_score([hypothesis], [[reference]])
    return score.score


def calculate_chrf(hypothesis: str, reference: str) -> float:
    scorer = get_chrf_scorer()
    score = scorer.corpus_score([hypothesis], [[reference]])
    return score.score


def calculate_bertscore(hypothesis: str, reference: str, lang: str = "en") -> float:
    bert_score = get_bert_scorer()
    P, R, F1 = bert_score.score([hypothesis], [reference], lang=lang, verbose=False)
    return F1.item()


def calculate_comet(source: str, translation: str, reference: str) -> Optional[float]:
    model = get_comet_model()
    if model == "unavailable":
        return None
    try:
        data = [{"src": source, "mt": translation, "ref": reference}]
        output = model.predict(data, batch_size=1, accelerator='cpu', progress_bar=False)
        return output.scores[0]
    except Exception as e:
        logger.warning(f"COMET failed: {e}")
        return None


def calculate_comet_qe(source: str, translation: str) -> Optional[float]:
    model = get_comet_qe_model()
    if model == "unavailable":
        return None
    try:
        data = [{"src": source, "mt": translation}]
        output = model.predict(data, batch_size=1, accelerator='cpu', progress_bar=False)
        return output.scores[0]
    except Exception as e:
        logger.warning(f"COMET-QE failed: {e}")
        return None


def calculate_embedding_similarity(model, text1: str, text2: str) -> float:
    embeddings = model.encode([text1, text2])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


def calculate_labse_similarity(text1: str, text2: str) -> float:
    return calculate_embedding_similarity(get_labse_model(), text1, text2)


def calculate_xlm_roberta_similarity(text1: str, text2: str) -> float:
    return calculate_embedding_similarity(get_xlm_roberta_model(), text1, text2)


def calculate_mbert_similarity(text1: str, text2: str) -> float:
    return calculate_embedding_similarity(get_mbert_model(), text1, text2)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TranslationMetrics:
    doc_id: str
    model: str
    language: str

    # ==========================================================================
    # GOAL 2: Same-language metrics (LLM translation vs Professional translation)
    # ==========================================================================
    same_lang_bleu: Optional[float] = None
    same_lang_chrf: Optional[float] = None
    same_lang_bertscore: Optional[float] = None
    same_lang_comet: Optional[float] = None

    # ==========================================================================
    # GOAL 1: LLM Back-translation vs Original English
    # ==========================================================================
    # Cross-language semantic similarity
    cross_lang_xlm_roberta: Optional[float] = None
    cross_lang_labse: Optional[float] = None
    cross_lang_mbert: Optional[float] = None
    cross_lang_comet_qe: Optional[float] = None

    # String-based metrics (back-translation vs original)
    backtrans_bleu: Optional[float] = None
    backtrans_chrf: Optional[float] = None
    backtrans_bertscore: Optional[float] = None

    # ==========================================================================
    # GOAL 3: Professional Back-translation vs Original English [NEW]
    # ==========================================================================
    prof_backtrans_bleu: Optional[float] = None
    prof_backtrans_chrf: Optional[float] = None
    prof_backtrans_bertscore: Optional[float] = None
    prof_backtrans_labse: Optional[float] = None
    prof_backtrans_xlm_roberta: Optional[float] = None

    # ==========================================================================
    # GOAL 3b: LLM Back-translation vs Professional Back-translation [NEW]
    # ==========================================================================
    llm_vs_prof_backtrans_bleu: Optional[float] = None
    llm_vs_prof_backtrans_chrf: Optional[float] = None
    llm_vs_prof_backtrans_bertscore: Optional[float] = None
    llm_vs_prof_backtrans_labse: Optional[float] = None

    def to_dict(self):
        return asdict(self)


# =============================================================================
# MAIN EVALUATION
# =============================================================================

def evaluate_single(result: dict) -> TranslationMetrics:
    """Evaluate a single translation result."""
    metrics = TranslationMetrics(
        doc_id=result['doc_id'],
        model=result['model'],
        language=result['language']
    )

    english_original = result['english_original']
    llm_translation = result['llm_translation']
    professional_translation = result['professional_translation']
    back_translation = result['llm_back_translation']
    professional_back_translation = result.get('professional_back_translation', '')  # NEW

    # Skip if missing data
    if not llm_translation or not back_translation:
        logger.warning(f"Missing data for {result['doc_id']}/{result['model']}/{result['language']}")
        return metrics

    # ===========================================
    # GOAL 2: SAME-LANGUAGE METRICS (LLM vs Professional)
    # ===========================================
    if professional_translation:
        try:
            metrics.same_lang_bleu = calculate_bleu(llm_translation, professional_translation)
        except Exception as e:
            logger.warning(f"same_lang_bleu failed: {e}")

        try:
            metrics.same_lang_chrf = calculate_chrf(llm_translation, professional_translation)
        except Exception as e:
            logger.warning(f"same_lang_chrf failed: {e}")

        try:
            # Use multilingual BERTScore for non-English
            metrics.same_lang_bertscore = calculate_bertscore(
                llm_translation, professional_translation, lang="multilingual"
            )
        except Exception as e:
            logger.warning(f"same_lang_bertscore failed: {e}")

        try:
            metrics.same_lang_comet = calculate_comet(
                english_original, llm_translation, professional_translation
            )
        except Exception as e:
            logger.warning(f"same_lang_comet failed: {e}")

    # ===========================================
    # GOAL 1: CROSS-LANGUAGE METRICS (LLM Back-trans vs Original)
    # ===========================================
    try:
        metrics.cross_lang_xlm_roberta = calculate_xlm_roberta_similarity(
            back_translation, english_original
        )
    except Exception as e:
        logger.warning(f"xlm_roberta failed: {e}")

    try:
        metrics.cross_lang_labse = calculate_labse_similarity(
            back_translation, english_original
        )
    except Exception as e:
        logger.warning(f"labse failed: {e}")

    try:
        metrics.cross_lang_mbert = calculate_mbert_similarity(
            back_translation, english_original
        )
    except Exception as e:
        logger.warning(f"mbert failed: {e}")

    try:
        metrics.cross_lang_comet_qe = calculate_comet_qe(
            english_original, back_translation
        )
    except Exception as e:
        logger.warning(f"comet_qe failed: {e}")

    # GOAL 1: String-based metrics (LLM back-trans vs Original English)
    try:
        metrics.backtrans_bleu = calculate_bleu(back_translation, english_original)
    except Exception as e:
        logger.warning(f"backtrans_bleu failed: {e}")

    try:
        metrics.backtrans_chrf = calculate_chrf(back_translation, english_original)
    except Exception as e:
        logger.warning(f"backtrans_chrf failed: {e}")

    try:
        metrics.backtrans_bertscore = calculate_bertscore(back_translation, english_original)
    except Exception as e:
        logger.warning(f"backtrans_bertscore failed: {e}")

    # ===========================================
    # GOAL 3: PROFESSIONAL BACK-TRANSLATION vs Original English [NEW]
    # ===========================================
    if professional_back_translation:
        try:
            metrics.prof_backtrans_bleu = calculate_bleu(professional_back_translation, english_original)
        except Exception as e:
            logger.warning(f"prof_backtrans_bleu failed: {e}")

        try:
            metrics.prof_backtrans_chrf = calculate_chrf(professional_back_translation, english_original)
        except Exception as e:
            logger.warning(f"prof_backtrans_chrf failed: {e}")

        try:
            metrics.prof_backtrans_bertscore = calculate_bertscore(professional_back_translation, english_original)
        except Exception as e:
            logger.warning(f"prof_backtrans_bertscore failed: {e}")

        try:
            metrics.prof_backtrans_labse = calculate_labse_similarity(professional_back_translation, english_original)
        except Exception as e:
            logger.warning(f"prof_backtrans_labse failed: {e}")

        try:
            metrics.prof_backtrans_xlm_roberta = calculate_xlm_roberta_similarity(professional_back_translation, english_original)
        except Exception as e:
            logger.warning(f"prof_backtrans_xlm_roberta failed: {e}")

        # ===========================================
        # GOAL 3b: LLM Back-trans vs Professional Back-trans [NEW]
        # ===========================================
        try:
            metrics.llm_vs_prof_backtrans_bleu = calculate_bleu(back_translation, professional_back_translation)
        except Exception as e:
            logger.warning(f"llm_vs_prof_backtrans_bleu failed: {e}")

        try:
            metrics.llm_vs_prof_backtrans_chrf = calculate_chrf(back_translation, professional_back_translation)
        except Exception as e:
            logger.warning(f"llm_vs_prof_backtrans_chrf failed: {e}")

        try:
            metrics.llm_vs_prof_backtrans_bertscore = calculate_bertscore(back_translation, professional_back_translation)
        except Exception as e:
            logger.warning(f"llm_vs_prof_backtrans_bertscore failed: {e}")

        try:
            metrics.llm_vs_prof_backtrans_labse = calculate_labse_similarity(back_translation, professional_back_translation)
        except Exception as e:
            logger.warning(f"llm_vs_prof_backtrans_labse failed: {e}")

    return metrics


def run_evaluation(
    input_file: str = None,
    output_file: str = "all_metrics.json",
    checkpoint_interval: int = 50
):
    """Run evaluation on all results."""
    input_file = input_file or str(RESULTS_FILE)

    # Load results
    logger.info(f"Loading results from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    logger.info(f"Evaluating {len(results)} translations")

    # Check for existing checkpoint
    checkpoint_file = OUTPUT_DIR / "metrics_checkpoint.json"
    completed = set()
    all_metrics = []

    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        completed = set(checkpoint.get('completed', []))
        # Load existing metrics
        metrics_file = OUTPUT_DIR / output_file
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                all_metrics = json.load(f)
        logger.info(f"Resuming from checkpoint: {len(completed)} completed")

    # Process each result
    for i, result in enumerate(results):
        key = f"{result['doc_id']}|{result['model']}|{result['language']}"

        if key in completed:
            continue

        logger.info(f"[{i+1}/{len(results)}] {result['doc_id']} | {result['model']} | {result['language']}")

        metrics = evaluate_single(result)
        all_metrics.append(metrics.to_dict())
        completed.add(key)

        # Save checkpoint
        if (len(completed) % checkpoint_interval == 0) or (i == len(results) - 1):
            with open(OUTPUT_DIR / output_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)
            with open(checkpoint_file, 'w') as f:
                json.dump({'completed': list(completed)}, f)
            logger.info(f"Checkpoint saved: {len(completed)}/{len(results)}")

    # Final save
    with open(OUTPUT_DIR / output_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    logger.info(f"Evaluation complete! Saved to {OUTPUT_DIR / output_file}")
    return all_metrics


# =============================================================================
# RESULTS AGGREGATION
# =============================================================================

def aggregate_results(metrics_file: str = "all_metrics.json"):
    """Aggregate metrics by model, language, and category for poster table."""
    with open(OUTPUT_DIR / metrics_file, 'r') as f:
        metrics = json.load(f)

    # Aggregate by model
    by_model = {}
    for m in metrics:
        model = m['model']
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(m)

    # Aggregate by language
    by_language = {}
    for m in metrics:
        lang = m['language']
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(m)

    # Aggregate by category (immunize vs cancer)
    by_category = {'immunize': [], 'cancer': []}
    for m in metrics:
        # doc_id format: "category/topic" e.g. "immunize/hepatitis_b" or "cancer/breast-cancer"
        category = m['doc_id'].split('/')[0]
        if category in by_category:
            by_category[category].append(m)

    # Aggregate by model AND category
    by_model_category = {}
    for m in metrics:
        model = m['model']
        category = m['doc_id'].split('/')[0]
        key = f"{model}|{category}"
        if key not in by_model_category:
            by_model_category[key] = []
        by_model_category[key].append(m)

    # Calculate averages
    def avg(values):
        valid = [v for v in values if v is not None]
        return sum(valid) / len(valid) if valid else None

    def fmt(v):
        return f"{v:.2f}" if v is not None else "N/A"

    # =========================================================================
    # GOAL 2: LLM vs Professional Translation (Same Language)
    # =========================================================================
    print("\n" + "="*100)
    print("GOAL 2: LLM TRANSLATION vs PROFESSIONAL TRANSLATION (by Model)")
    print("="*100)
    print(f"{'Model':<20} {'BLEU':>8} {'chrF':>8} {'BERT':>8} {'COMET':>8}")
    print("-"*60)

    model_summaries = {}
    for model, model_metrics in sorted(by_model.items()):
        summary = {
            'same_lang_bleu': avg([m['same_lang_bleu'] for m in model_metrics]),
            'same_lang_chrf': avg([m['same_lang_chrf'] for m in model_metrics]),
            'same_lang_bertscore': avg([m['same_lang_bertscore'] for m in model_metrics]),
            'same_lang_comet': avg([m['same_lang_comet'] for m in model_metrics]),
            'cross_lang_xlm_roberta': avg([m['cross_lang_xlm_roberta'] for m in model_metrics]),
            'cross_lang_labse': avg([m['cross_lang_labse'] for m in model_metrics]),
            'cross_lang_mbert': avg([m['cross_lang_mbert'] for m in model_metrics]),
            'cross_lang_comet_qe': avg([m['cross_lang_comet_qe'] for m in model_metrics]),
            'backtrans_bleu': avg([m['backtrans_bleu'] for m in model_metrics]),
            'backtrans_bertscore': avg([m['backtrans_bertscore'] for m in model_metrics]),
            # Goal 3 metrics
            'prof_backtrans_bleu': avg([m.get('prof_backtrans_bleu') for m in model_metrics]),
            'prof_backtrans_bertscore': avg([m.get('prof_backtrans_bertscore') for m in model_metrics]),
            'prof_backtrans_labse': avg([m.get('prof_backtrans_labse') for m in model_metrics]),
            'llm_vs_prof_backtrans_bleu': avg([m.get('llm_vs_prof_backtrans_bleu') for m in model_metrics]),
            'llm_vs_prof_backtrans_labse': avg([m.get('llm_vs_prof_backtrans_labse') for m in model_metrics]),
        }
        model_summaries[model] = summary

        print(f"{model:<20} {fmt(summary['same_lang_bleu']):>8} {fmt(summary['same_lang_chrf']):>8} "
              f"{fmt(summary['same_lang_bertscore']):>8} {fmt(summary['same_lang_comet']):>8}")

    # =========================================================================
    # GOAL 1: Back-Translation Quality (LLM back-trans vs Original English)
    # =========================================================================
    print("\n" + "="*100)
    print("GOAL 1: LLM BACK-TRANSLATION vs ORIGINAL ENGLISH (by Model)")
    print("="*100)
    print(f"{'Model':<20} {'BLEU':>8} {'BERT':>8} {'LaBSE':>8} {'XLM-R':>8} {'COMET-QE':>8}")
    print("-"*80)

    for model, summary in model_summaries.items():
        print(f"{model:<20} {fmt(summary['backtrans_bleu']):>8} {fmt(summary['backtrans_bertscore']):>8} "
              f"{fmt(summary['cross_lang_labse']):>8} {fmt(summary['cross_lang_xlm_roberta']):>8} "
              f"{fmt(summary['cross_lang_comet_qe']):>8}")

    # =========================================================================
    # GOAL 3: Professional Back-Translation vs Original English
    # =========================================================================
    print("\n" + "="*100)
    print("GOAL 3: PROFESSIONAL BACK-TRANSLATION vs ORIGINAL ENGLISH (by Model)")
    print("="*100)
    print(f"{'Model':<20} {'BLEU':>8} {'BERT':>8} {'LaBSE':>8}")
    print("-"*60)

    for model, summary in model_summaries.items():
        print(f"{model:<20} {fmt(summary['prof_backtrans_bleu']):>8} {fmt(summary['prof_backtrans_bertscore']):>8} "
              f"{fmt(summary['prof_backtrans_labse']):>8}")

    # =========================================================================
    # GOAL 3b: LLM Back-Trans vs Professional Back-Trans
    # =========================================================================
    print("\n" + "="*100)
    print("GOAL 3b: LLM BACK-TRANS vs PROFESSIONAL BACK-TRANS (by Model)")
    print("="*100)
    print(f"{'Model':<20} {'BLEU':>8} {'LaBSE':>8}")
    print("-"*40)

    for model, summary in model_summaries.items():
        print(f"{model:<20} {fmt(summary['llm_vs_prof_backtrans_bleu']):>8} {fmt(summary['llm_vs_prof_backtrans_labse']):>8}")

    # =========================================================================
    # BY LANGUAGE
    # =========================================================================
    print("\n" + "="*100)
    print("RESULTS BY LANGUAGE (All Goals)")
    print("="*100)
    print(f"{'Language':<20} {'G2:BLEU':>8} {'G1:BLEU':>8} {'G1:LaBSE':>8} {'G3:BLEU':>8} {'G3:LaBSE':>8}")
    print("-"*80)

    lang_summaries = {}
    for lang, lang_metrics in sorted(by_language.items()):
        summary = {
            'same_lang_bleu': avg([m['same_lang_bleu'] for m in lang_metrics]),
            'backtrans_bleu': avg([m['backtrans_bleu'] for m in lang_metrics]),
            'cross_lang_labse': avg([m['cross_lang_labse'] for m in lang_metrics]),
            'prof_backtrans_bleu': avg([m.get('prof_backtrans_bleu') for m in lang_metrics]),
            'prof_backtrans_labse': avg([m.get('prof_backtrans_labse') for m in lang_metrics]),
        }
        lang_summaries[lang] = summary

        print(f"{lang:<20} {fmt(summary['same_lang_bleu']):>8} {fmt(summary['backtrans_bleu']):>8} "
              f"{fmt(summary['cross_lang_labse']):>8} {fmt(summary['prof_backtrans_bleu']):>8} "
              f"{fmt(summary['prof_backtrans_labse']):>8}")

    # =========================================================================
    # BY CATEGORY (Immunize vs Cancer)
    # =========================================================================
    print("\n" + "="*100)
    print("RESULTS BY CATEGORY (Vaccine VIS vs Cancer Materials)")
    print("="*100)
    print(f"{'Category':<15} {'Count':>6} {'G2:BLEU':>8} {'G1:BLEU':>8} {'G1:LaBSE':>8} {'G3:BLEU':>8} {'G3:LaBSE':>8}")
    print("-"*80)

    category_summaries = {}
    for category, cat_metrics in sorted(by_category.items()):
        summary = {
            'count': len(cat_metrics),
            'same_lang_bleu': avg([m['same_lang_bleu'] for m in cat_metrics]),
            'backtrans_bleu': avg([m['backtrans_bleu'] for m in cat_metrics]),
            'cross_lang_labse': avg([m['cross_lang_labse'] for m in cat_metrics]),
            'prof_backtrans_bleu': avg([m.get('prof_backtrans_bleu') for m in cat_metrics]),
            'prof_backtrans_labse': avg([m.get('prof_backtrans_labse') for m in cat_metrics]),
        }
        category_summaries[category] = summary

        print(f"{category:<15} {summary['count']:>6} {fmt(summary['same_lang_bleu']):>8} {fmt(summary['backtrans_bleu']):>8} "
              f"{fmt(summary['cross_lang_labse']):>8} {fmt(summary['prof_backtrans_bleu']):>8} "
              f"{fmt(summary['prof_backtrans_labse']):>8}")

    # =========================================================================
    # BY MODEL AND CATEGORY (for publication - shows if patterns hold)
    # =========================================================================
    print("\n" + "="*100)
    print("RESULTS BY MODEL × CATEGORY (Vaccine VIS vs Cancer)")
    print("="*100)
    print(f"{'Model':<20} {'Category':<10} {'G2:BLEU':>8} {'G1:BLEU':>8} {'G1:LaBSE':>8} {'G3:BLEU':>8}")
    print("-"*80)

    model_category_summaries = {}
    for key, mc_metrics in sorted(by_model_category.items()):
        model, category = key.split('|')
        summary = {
            'same_lang_bleu': avg([m['same_lang_bleu'] for m in mc_metrics]),
            'backtrans_bleu': avg([m['backtrans_bleu'] for m in mc_metrics]),
            'cross_lang_labse': avg([m['cross_lang_labse'] for m in mc_metrics]),
            'prof_backtrans_bleu': avg([m.get('prof_backtrans_bleu') for m in mc_metrics]),
        }
        model_category_summaries[key] = summary

        print(f"{model:<20} {category:<10} {fmt(summary['same_lang_bleu']):>8} {fmt(summary['backtrans_bleu']):>8} "
              f"{fmt(summary['cross_lang_labse']):>8} {fmt(summary['prof_backtrans_bleu']):>8}")

    # Save summaries
    summary_data = {
        'by_model': model_summaries,
        'by_language': lang_summaries,
        'by_category': category_summaries,
        'by_model_category': model_category_summaries
    }
    with open(OUTPUT_DIR / "summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nSummary saved to {OUTPUT_DIR / 'summary.json'}")

    return summary_data


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calculate metrics for MedlinePlus translations")
    parser.add_argument("--evaluate", action="store_true", help="Run full evaluation")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate results into summary table")
    parser.add_argument("--input", type=str, help="Input results file")
    parser.add_argument("--test", action="store_true", help="Test with single result")

    args = parser.parse_args()

    if args.test:
        # Test with first result
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)

        print("Testing with first result...")
        metrics = evaluate_single(results[0])
        print(f"\nResult: {metrics.doc_id} | {metrics.model} | {metrics.language}")
        print(f"  Same-lang BLEU: {metrics.same_lang_bleu}")
        print(f"  Same-lang chrF: {metrics.same_lang_chrf}")
        print(f"  Same-lang BERTScore: {metrics.same_lang_bertscore}")
        print(f"  Cross-lang LaBSE: {metrics.cross_lang_labse}")
        print(f"  Cross-lang XLM-R: {metrics.cross_lang_xlm_roberta}")

    elif args.evaluate:
        run_evaluation(input_file=args.input)

    elif args.aggregate:
        aggregate_results()

    else:
        print("""
MedlinePlus Metrics Calculator

Usage:
  python calculate_medlineplus_metrics.py --test       # Test with single result
  python calculate_medlineplus_metrics.py --evaluate   # Run full evaluation (704 results)
  python calculate_medlineplus_metrics.py --aggregate  # Generate summary tables

Metrics calculated:
  SAME-LANGUAGE (LLM vs Professional):
    - BLEU, chrF, BERTScore, COMET

  CROSS-LANGUAGE (Back-translation vs Original):
    - XLM-RoBERTa, LaBSE, mBERT, COMET-QE
        """)
