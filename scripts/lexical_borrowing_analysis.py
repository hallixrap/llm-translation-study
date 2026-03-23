#!/usr/bin/env python3
"""
Lexical Borrowing Quantification Analysis

Addresses reviewer critique: high LaBSE scores for low-resource languages (Tagalog,
Haitian Creole) may reflect English/French medical terminology being retained verbatim
in translations (transliteration rather than genuine translation).

This script:
1. Builds a comprehensive medical terminology list (~150 terms)
2. Detects English medical terms retained verbatim in each translation
3. For Haitian Creole, also detects French medical term borrowing
4. Computes borrowing rates by language, resource level, model, and script type
5. Correlates borrowing rates with LaBSE scores (key test of the reviewer's hypothesis)
6. Identifies the most commonly borrowed terms for Tagalog and Haitian Creole

If lexical borrowing inflates LaBSE scores, we expect a positive Spearman correlation
between borrowing rate and LaBSE within low-resource languages.
"""

import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from scipy.stats import kruskal, mannwhitneyu, spearmanr

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "output" / "medlineplus_results" / "all_results.json"
METRICS_FILE = BASE_DIR / "output" / "medlineplus_metrics" / "all_metrics.json"
OUTPUT_DIR = BASE_DIR / "output" / "lexical_borrowing"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Language metadata (must match config.py exactly)
LANGUAGES = {
    "spanish":            {"resource_level": "high",   "script": "Latin"},
    "chinese_simplified": {"resource_level": "high",   "script": "Non-Latin"},
    "vietnamese":         {"resource_level": "high",   "script": "Latin"},
    "russian":            {"resource_level": "high",   "script": "Non-Latin"},
    "arabic":             {"resource_level": "medium", "script": "Non-Latin"},
    "korean":             {"resource_level": "medium", "script": "Non-Latin"},
    "tagalog":            {"resource_level": "low",    "script": "Latin"},
    "haitian_creole":     {"resource_level": "low",    "script": "Latin"},
}

MODELS = ["gpt-5.1", "claude-opus-4.5", "gemini-3-pro", "kimi-k2"]

# =============================================================================
# MEDICAL TERMINOLOGY LISTS
# =============================================================================

# Comprehensive English medical term list (~160 terms)
# Curated from CDC Vaccine Information Statements and ACS cancer education materials,
# which are the source document types in this corpus.
ENGLISH_MEDICAL_TERMS = [
    # --- Vaccines & Immunization ---
    "vaccine", "vaccines", "vaccination", "vaccinated", "immunization",
    "immunize", "immunized", "booster", "dose", "doses", "antigen",
    "antibody", "antibodies", "immunity", "immune", "adjuvant",
    # Specific vaccines & diseases
    "influenza", "flu", "hepatitis", "hpv", "papillomavirus",
    "meningococcal", "meningitis", "mmr", "measles", "mumps", "rubella",
    "pneumococcal", "pneumonia", "polio", "poliovirus", "tdap",
    "tetanus", "diphtheria", "pertussis", "varicella", "chickenpox",
    "shingles", "zoster", "rotavirus", "smallpox", "covid",
    "coronavirus", "sars", "mRNA",
    # Vaccine-related terms
    "inactivated", "recombinant", "conjugate", "toxoid",
    "intramuscular", "subcutaneous", "intradermal",
    "syringe", "injection", "injectable",
    # Adverse reactions
    "anaphylaxis", "anaphylactic", "allergic", "allergy",
    "fever", "seizure", "seizures", "guillain",

    # --- Cancer & Oncology ---
    "cancer", "cancers", "tumor", "tumors", "tumour", "tumours",
    "malignant", "malignancy", "benign", "metastasis", "metastatic",
    "metastasize", "carcinoma", "sarcoma", "lymphoma", "melanoma",
    "leukemia", "oncology", "oncologist", "neoplasm",
    # Cancer types referenced in corpus
    "breast", "cervical", "colorectal", "colon", "rectal",
    "lung", "prostate", "skin", "basal", "squamous",
    # Treatments
    "chemotherapy", "radiation", "radiotherapy", "immunotherapy",
    "surgery", "surgical", "biopsy", "biopsies", "excision",
    "mastectomy", "lumpectomy", "colectomy", "prostatectomy",
    "hysterectomy", "resection",
    # Screening & diagnostics
    "mammogram", "mammography", "colonoscopy", "pap", "screening",
    "diagnosis", "diagnostic", "prognosis", "staging",
    "mri", "ct", "ultrasound", "x-ray", "pet",
    "biopsy", "pathology", "pathologist", "cytology",
    "dermoscopy", "dermatoscopy",

    # --- General Medical Terms ---
    "diabetes", "diabetic", "insulin", "glucose", "glycemic",
    "hypertension", "cholesterol", "cardiovascular", "cardiac",
    "bronchitis", "asthma", "respiratory",
    "antibiotic", "antibiotics", "antiviral", "antifungal",
    "analgesic", "ibuprofen", "acetaminophen", "aspirin",
    "prescription", "pharmaceutical", "medication", "medications",
    "intravenous", "oral", "topical",
    "symptom", "symptoms", "chronic", "acute",
    "inflammation", "inflammatory", "infection", "infectious",
    "bacteria", "bacterial", "virus", "viral", "pathogen",
    "clinical", "therapy", "therapeutic", "treatment",
    "hormone", "hormonal", "estrogen", "testosterone",
    "genetic", "genomic", "gene", "genes", "mutation",
    "nausea", "vomiting", "diarrhea", "constipation", "fatigue",
    "lymph", "lymphatic", "lymphocyte",
    "platelet", "hemoglobin", "anemia",
    "catheter", "stent", "prosthesis",
    "palliative", "hospice", "remission",
    "polyp", "polyps", "lesion", "lesions", "nodule", "nodules",
    "benign", "premalignant", "precancerous",
    "tumor", "hematologist", "dermatologist", "gastroenterologist",
    "pulmonologist", "urologist", "gynecologist",
    "cdc", "fda",
]

# Deduplicate (case-insensitive) and sort
_seen = set()
_deduped = []
for term in ENGLISH_MEDICAL_TERMS:
    low = term.lower()
    if low not in _seen:
        _seen.add(low)
        _deduped.append(low)
ENGLISH_MEDICAL_TERMS = sorted(_deduped)

# French medical terms for Haitian Creole analysis
# Haitian Creole derives from French, so medical borrowing may come from French
# rather than English. We include French equivalents of key terms.
FRENCH_MEDICAL_TERMS = [
    # Vaccines & Immunization
    "vaccin", "vaccins", "vaccination", "vacciné", "immunisation",
    "immunisé", "rappel", "antigène", "anticorps", "immunité",
    "adjuvant",
    # Specific diseases (French forms)
    "grippe", "hépatite", "méningite", "rougeole", "oreillons",
    "rubéole", "pneumonie", "tétanos", "diphtérie", "coqueluche",
    "varicelle", "zona", "poliomyélite",
    # Vaccine-related
    "inactivé", "recombinant", "conjugué", "toxoïde",
    "intramusculaire", "sous-cutané", "intradermique",
    "seringue", "injection",
    # Adverse reactions
    "anaphylaxie", "anaphylactique", "allergique", "allergie",
    "fièvre", "convulsion", "convulsions",

    # Cancer & Oncology
    "cancer", "cancers", "tumeur", "tumeurs",
    "malin", "maligne", "bénin", "bénigne", "métastase", "métastatique",
    "carcinome", "sarcome", "lymphome", "mélanome",
    "leucémie", "oncologie", "oncologue", "néoplasme",
    # Cancer types
    "sein", "cervical", "colorectal", "côlon", "rectal",
    "poumon", "prostate", "peau", "basocellulaire",
    # Treatments
    "chimiothérapie", "radiothérapie", "immunothérapie",
    "chirurgie", "chirurgical", "biopsie", "biopsies", "excision",
    "mastectomie", "colectomie", "prostatectomie",
    "hystérectomie", "résection",
    # Screening & diagnostics
    "mammographie", "coloscopie", "dépistage",
    "diagnostic", "pronostic", "stadification",
    "échographie", "radiographie", "pathologie", "pathologiste",
    "cytologie", "dermoscopie",

    # General Medical
    "diabète", "diabétique", "insuline", "glucose", "glycémique",
    "hypertension", "cholestérol", "cardiovasculaire", "cardiaque",
    "bronchite", "asthme", "respiratoire",
    "antibiotique", "antibiotiques", "antiviral", "antifongique",
    "analgésique", "ibuprofène", "acétaminophène", "aspirine",
    "prescription", "pharmaceutique", "médicament", "médicaments",
    "intraveineux", "oral", "topique",
    "symptôme", "symptômes", "chronique", "aigu",
    "inflammation", "inflammatoire", "infection", "infectieux",
    "bactérie", "bactérien", "virus", "viral", "pathogène",
    "clinique", "thérapie", "thérapeutique", "traitement",
    "hormone", "hormonal", "œstrogène", "testostérone",
    "génétique", "génomique", "gène", "gènes", "mutation",
    "nausée", "vomissement", "diarrhée", "constipation", "fatigue",
    "lymphe", "lymphatique", "lymphocyte",
    "plaquette", "hémoglobine", "anémie",
    "cathéter", "stent", "prothèse",
    "palliatif", "rémission",
    "polype", "polypes", "lésion", "lésions", "nodule", "nodules",
    "précancéreux", "prémalin",
    "hématologue", "dermatologue", "gastroentérologue",
    "pneumologue", "urologue", "gynécologue",
]

# Deduplicate French terms
_seen_fr = set()
_deduped_fr = []
for term in FRENCH_MEDICAL_TERMS:
    low = term.lower()
    if low not in _seen_fr:
        _seen_fr.add(low)
        _deduped_fr.append(low)
FRENCH_MEDICAL_TERMS = sorted(_deduped_fr)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def tokenize(text):
    """
    Simple whitespace + punctuation tokenizer.
    Splits on whitespace, strips surrounding punctuation, lowercases.
    Returns list of tokens.
    """
    # Split on whitespace
    raw_tokens = text.split()
    tokens = []
    for tok in raw_tokens:
        # Strip common punctuation from edges
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', tok, flags=re.UNICODE)
        if cleaned:
            tokens.append(cleaned.lower())
    return tokens


def find_medical_terms_in_text(text, term_list):
    """
    Find which medical terms from term_list appear in the given text.
    Uses word-boundary matching to avoid partial matches (e.g., 'oral' in 'colorectal').

    Returns:
        set of matched terms (lowercased)
    """
    text_lower = text.lower()
    found = set()
    for term in term_list:
        # Use word boundary regex for accurate matching
        # \b handles most cases; for terms with hyphens or special chars, escape them
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, text_lower):
            found.add(term)
    return found


def compute_borrowing_rate(original_terms, translated_terms):
    """
    Compute the borrowing rate: proportion of English medical terms found in
    the original that also appear verbatim in the translation.

    Args:
        original_terms: set of medical terms found in the English source
        translated_terms: set of medical terms found in the translated text

    Returns:
        float: borrowing rate (0.0 to 1.0), or NaN if no terms in original
    """
    if not original_terms:
        return np.nan
    borrowed = original_terms & translated_terms
    return len(borrowed) / len(original_terms)


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def load_data():
    """Load translation results and metrics data."""
    print("Loading data...")
    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
    with open(METRICS_FILE, 'r') as f:
        metrics = json.load(f)

    results_df = pd.DataFrame(results)
    metrics_df = pd.DataFrame(metrics)

    print(f"  Results: {len(results_df)} entries")
    print(f"  Metrics: {len(metrics_df)} entries")
    print(f"  Languages: {sorted(results_df['language'].unique())}")
    print(f"  Models: {sorted(results_df['model'].unique())}")
    print(f"  Documents: {results_df['doc_id'].nunique()}")
    return results_df, metrics_df


def analyze_borrowing(results_df, metrics_df):
    """
    Main analysis: compute lexical borrowing rates for every translation.
    """
    print("\nAnalyzing lexical borrowing...")
    print(f"  English medical terms in list: {len(ENGLISH_MEDICAL_TERMS)}")
    print(f"  French medical terms in list: {len(FRENCH_MEDICAL_TERMS)}")

    per_translation = []

    for idx, row in results_df.iterrows():
        doc_id = row['doc_id']
        model = row['model']
        language = row['language']
        original_text = row['english_original']
        translated_text = row['llm_translation']

        lang_meta = LANGUAGES.get(language, {})
        resource_level = lang_meta.get('resource_level', 'unknown')
        script_type = lang_meta.get('script', 'unknown')

        # Find English medical terms in the original
        original_eng_terms = find_medical_terms_in_text(original_text, ENGLISH_MEDICAL_TERMS)

        # Find English medical terms retained in the translation
        translated_eng_terms = find_medical_terms_in_text(translated_text, ENGLISH_MEDICAL_TERMS)

        # Compute English borrowing rate
        eng_borrowing_rate = compute_borrowing_rate(original_eng_terms, translated_eng_terms)

        # Terms that were borrowed (intersection)
        eng_borrowed_terms = sorted(original_eng_terms & translated_eng_terms)

        # For Haitian Creole: also check French medical term presence
        french_borrowing_rate = np.nan
        french_terms_found = []
        if language == 'haitian_creole':
            french_terms_in_translation = find_medical_terms_in_text(
                translated_text, FRENCH_MEDICAL_TERMS
            )
            # For French borrowing, we compute what fraction of original English
            # medical concepts appear as French terms in the translation.
            # This requires a different denominator: still the original English terms.
            # But the numerator is French terms found in translation.
            # Since French and English term lists overlap for some terms, we count
            # French-specific terms (those NOT in the English list).
            french_only_terms = french_terms_in_translation - set(ENGLISH_MEDICAL_TERMS)
            french_terms_found = sorted(french_only_terms)
            if original_eng_terms:
                french_borrowing_rate = len(french_only_terms) / len(original_eng_terms)

        entry = {
            'doc_id': doc_id,
            'model': model,
            'language': language,
            'resource_level': resource_level,
            'script_type': script_type,
            'n_original_eng_terms': len(original_eng_terms),
            'n_borrowed_eng_terms': len(eng_borrowed_terms),
            'eng_borrowing_rate': eng_borrowing_rate,
            'borrowed_eng_terms': eng_borrowed_terms,
            'french_borrowing_rate': french_borrowing_rate,
            'french_terms_found': french_terms_found,
        }
        per_translation.append(entry)

    df = pd.DataFrame(per_translation)

    # Merge with metrics to get LaBSE scores
    merge_keys = ['doc_id', 'model', 'language']
    labse_cols = merge_keys + ['cross_lang_labse']
    df = df.merge(
        metrics_df[labse_cols],
        on=merge_keys,
        how='left'
    )

    print(f"  Translations analyzed: {len(df)}")
    print(f"  Mean English medical terms per document: "
          f"{df['n_original_eng_terms'].mean():.1f}")
    print(f"  Overall mean borrowing rate: {df['eng_borrowing_rate'].mean():.3f}")

    return df


def compute_summary_statistics(df):
    """Compute aggregated summary statistics."""
    print("\nComputing summary statistics...")
    summary = {}

    # -------------------------------------------------------------------------
    # 1. By Language
    # -------------------------------------------------------------------------
    lang_stats = df.groupby('language').agg(
        n=('eng_borrowing_rate', 'count'),
        mean_borrowing_rate=('eng_borrowing_rate', 'mean'),
        std_borrowing_rate=('eng_borrowing_rate', 'std'),
        median_borrowing_rate=('eng_borrowing_rate', 'median'),
        mean_labse=('cross_lang_labse', 'mean'),
    ).reset_index()

    # Add resource level and script type
    lang_stats['resource_level'] = lang_stats['language'].map(
        lambda l: LANGUAGES[l]['resource_level']
    )
    lang_stats['script_type'] = lang_stats['language'].map(
        lambda l: LANGUAGES[l]['script']
    )

    summary['by_language'] = lang_stats.to_dict('records')
    print("\n  Borrowing rates by language:")
    for _, row in lang_stats.sort_values('mean_borrowing_rate', ascending=False).iterrows():
        print(f"    {row['language']:25s}  rate={row['mean_borrowing_rate']:.3f} "
              f"(SD={row['std_borrowing_rate']:.3f})  "
              f"[{row['resource_level']}, {row['script_type']}]")

    # -------------------------------------------------------------------------
    # 2. By Resource Level
    # -------------------------------------------------------------------------
    resource_stats = df.groupby('resource_level').agg(
        n=('eng_borrowing_rate', 'count'),
        mean_borrowing_rate=('eng_borrowing_rate', 'mean'),
        std_borrowing_rate=('eng_borrowing_rate', 'std'),
        median_borrowing_rate=('eng_borrowing_rate', 'median'),
    ).reset_index()

    summary['by_resource_level'] = resource_stats.to_dict('records')
    print("\n  Borrowing rates by resource level:")
    for _, row in resource_stats.iterrows():
        print(f"    {row['resource_level']:10s}  rate={row['mean_borrowing_rate']:.3f} "
              f"(SD={row['std_borrowing_rate']:.3f}, n={row['n']})")

    # -------------------------------------------------------------------------
    # 3. By Model
    # -------------------------------------------------------------------------
    model_stats = df.groupby('model').agg(
        n=('eng_borrowing_rate', 'count'),
        mean_borrowing_rate=('eng_borrowing_rate', 'mean'),
        std_borrowing_rate=('eng_borrowing_rate', 'std'),
        median_borrowing_rate=('eng_borrowing_rate', 'median'),
    ).reset_index()

    summary['by_model'] = model_stats.to_dict('records')
    print("\n  Borrowing rates by model:")
    for _, row in model_stats.sort_values('mean_borrowing_rate', ascending=False).iterrows():
        print(f"    {row['model']:20s}  rate={row['mean_borrowing_rate']:.3f} "
              f"(SD={row['std_borrowing_rate']:.3f})")

    # -------------------------------------------------------------------------
    # 4. By Script Type (Latin vs Non-Latin)
    # -------------------------------------------------------------------------
    script_stats = df.groupby('script_type').agg(
        n=('eng_borrowing_rate', 'count'),
        mean_borrowing_rate=('eng_borrowing_rate', 'mean'),
        std_borrowing_rate=('eng_borrowing_rate', 'std'),
        median_borrowing_rate=('eng_borrowing_rate', 'median'),
    ).reset_index()

    summary['by_script_type'] = script_stats.to_dict('records')
    print("\n  Borrowing rates by script type:")
    for _, row in script_stats.iterrows():
        print(f"    {row['script_type']:15s}  rate={row['mean_borrowing_rate']:.3f} "
              f"(SD={row['std_borrowing_rate']:.3f}, n={row['n']})")

    # -------------------------------------------------------------------------
    # 5. By Model x Language (interaction)
    # -------------------------------------------------------------------------
    model_lang_stats = df.groupby(['model', 'language']).agg(
        mean_borrowing_rate=('eng_borrowing_rate', 'mean'),
    ).reset_index()
    summary['by_model_language'] = model_lang_stats.to_dict('records')

    # -------------------------------------------------------------------------
    # 6. Haitian Creole French borrowing
    # -------------------------------------------------------------------------
    ht_df = df[df['language'] == 'haitian_creole']
    if not ht_df.empty:
        ht_french_stats = {
            'n': len(ht_df),
            'mean_french_borrowing_rate': float(ht_df['french_borrowing_rate'].mean()),
            'std_french_borrowing_rate': float(ht_df['french_borrowing_rate'].std()),
            'median_french_borrowing_rate': float(ht_df['french_borrowing_rate'].median()),
            'mean_eng_borrowing_rate': float(ht_df['eng_borrowing_rate'].mean()),
        }
        summary['haitian_creole_french_borrowing'] = ht_french_stats
        print(f"\n  Haitian Creole French borrowing rate: "
              f"{ht_french_stats['mean_french_borrowing_rate']:.3f} "
              f"(SD={ht_french_stats['std_french_borrowing_rate']:.3f})")

    return summary


def compute_top_borrowed_terms(df):
    """
    Identify the top 20 most commonly borrowed English terms for
    Tagalog and Haitian Creole.
    """
    print("\nComputing top borrowed terms...")
    top_terms = {}

    for lang in ['tagalog', 'haitian_creole']:
        lang_df = df[df['language'] == lang]
        counter = Counter()
        for _, row in lang_df.iterrows():
            for term in row['borrowed_eng_terms']:
                counter[term] += 1
        top_20 = counter.most_common(20)
        top_terms[lang] = [
            {'term': term, 'count': count, 'frequency': count / len(lang_df)}
            for term, count in top_20
        ]
        print(f"\n  Top 20 borrowed terms for {lang}:")
        for i, (term, count) in enumerate(top_20, 1):
            freq = count / len(lang_df) * 100
            print(f"    {i:2d}. {term:25s}  {count:3d}/{len(lang_df)} ({freq:.1f}%)")

    # Also get top French terms for Haitian Creole
    ht_df = df[df['language'] == 'haitian_creole']
    fr_counter = Counter()
    for _, row in ht_df.iterrows():
        for term in row['french_terms_found']:
            fr_counter[term] += 1
    top_20_fr = fr_counter.most_common(20)
    top_terms['haitian_creole_french'] = [
        {'term': term, 'count': count, 'frequency': count / len(ht_df)}
        for term, count in top_20_fr
    ]
    if top_20_fr:
        print(f"\n  Top French-origin terms in Haitian Creole translations:")
        for i, (term, count) in enumerate(top_20_fr, 1):
            freq = count / len(ht_df) * 100
            print(f"    {i:2d}. {term:25s}  {count:3d}/{len(ht_df)} ({freq:.1f}%)")

    return top_terms


def run_statistical_tests(df):
    """
    Run statistical tests on borrowing rates.
    """
    print("\nRunning statistical tests...")
    test_results = {}

    # -------------------------------------------------------------------------
    # 1. Kruskal-Wallis across resource levels
    # -------------------------------------------------------------------------
    groups_by_resource = {}
    for level in ['high', 'medium', 'low']:
        vals = df[df['resource_level'] == level]['eng_borrowing_rate'].dropna().values
        if len(vals) > 0:
            groups_by_resource[level] = vals

    if len(groups_by_resource) >= 2:
        group_arrays = list(groups_by_resource.values())
        h_stat, p_val = kruskal(*group_arrays)
        test_results['kruskal_wallis_resource_levels'] = {
            'test': 'Kruskal-Wallis',
            'comparison': 'Borrowing rate across resource levels (high/medium/low)',
            'H_statistic': float(h_stat),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
            'group_sizes': {k: len(v) for k, v in groups_by_resource.items()},
        }
        print(f"  Kruskal-Wallis (resource levels): H={h_stat:.2f}, p={p_val:.4f}")

    # -------------------------------------------------------------------------
    # 2. Mann-Whitney: Tagalog/Haitian Creole vs all other languages
    # -------------------------------------------------------------------------
    low_resource = df[df['language'].isin(['tagalog', 'haitian_creole'])]['eng_borrowing_rate'].dropna()
    other_langs = df[~df['language'].isin(['tagalog', 'haitian_creole'])]['eng_borrowing_rate'].dropna()

    if len(low_resource) > 0 and len(other_langs) > 0:
        u_stat, p_val = mannwhitneyu(low_resource, other_langs, alternative='two-sided')
        test_results['mann_whitney_low_vs_others'] = {
            'test': 'Mann-Whitney U',
            'comparison': 'Borrowing rate: Tagalog+Haitian Creole vs all other languages',
            'U_statistic': float(u_stat),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
            'n_low': int(len(low_resource)),
            'n_other': int(len(other_langs)),
            'mean_low': float(low_resource.mean()),
            'mean_other': float(other_langs.mean()),
        }
        print(f"  Mann-Whitney (low vs others): U={u_stat:.2f}, p={p_val:.6f}")
        print(f"    Low-resource mean: {low_resource.mean():.3f}, Others mean: {other_langs.mean():.3f}")

    # -------------------------------------------------------------------------
    # 3. Mann-Whitney: Latin script vs Non-Latin script
    # -------------------------------------------------------------------------
    latin = df[df['script_type'] == 'Latin']['eng_borrowing_rate'].dropna()
    non_latin = df[df['script_type'] != 'Latin']['eng_borrowing_rate'].dropna()

    if len(latin) > 0 and len(non_latin) > 0:
        u_stat, p_val = mannwhitneyu(latin, non_latin, alternative='two-sided')
        test_results['mann_whitney_latin_vs_nonlatin'] = {
            'test': 'Mann-Whitney U',
            'comparison': 'Borrowing rate: Latin script vs Non-Latin script languages',
            'U_statistic': float(u_stat),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
            'n_latin': int(len(latin)),
            'n_non_latin': int(len(non_latin)),
            'mean_latin': float(latin.mean()),
            'mean_non_latin': float(non_latin.mean()),
        }
        print(f"  Mann-Whitney (Latin vs Non-Latin): U={u_stat:.2f}, p={p_val:.6f}")
        print(f"    Latin mean: {latin.mean():.3f}, Non-Latin mean: {non_latin.mean():.3f}")

    # -------------------------------------------------------------------------
    # 4. Kruskal-Wallis across models
    # -------------------------------------------------------------------------
    groups_by_model = {}
    for model in MODELS:
        vals = df[df['model'] == model]['eng_borrowing_rate'].dropna().values
        if len(vals) > 0:
            groups_by_model[model] = vals

    if len(groups_by_model) >= 2:
        group_arrays = list(groups_by_model.values())
        h_stat, p_val = kruskal(*group_arrays)
        test_results['kruskal_wallis_models'] = {
            'test': 'Kruskal-Wallis',
            'comparison': 'Borrowing rate across models',
            'H_statistic': float(h_stat),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
            'group_sizes': {k: len(v) for k, v in groups_by_model.items()},
        }
        print(f"  Kruskal-Wallis (models): H={h_stat:.2f}, p={p_val:.4f}")

    # -------------------------------------------------------------------------
    # 5. Pairwise Mann-Whitney between each language pair (for completeness)
    # -------------------------------------------------------------------------
    all_languages = sorted(df['language'].unique())
    pairwise = []
    for i, lang1 in enumerate(all_languages):
        for lang2 in all_languages[i + 1:]:
            vals1 = df[df['language'] == lang1]['eng_borrowing_rate'].dropna()
            vals2 = df[df['language'] == lang2]['eng_borrowing_rate'].dropna()
            if len(vals1) > 0 and len(vals2) > 0:
                u_stat, p_val = mannwhitneyu(vals1, vals2, alternative='two-sided')
                pairwise.append({
                    'language_1': lang1,
                    'language_2': lang2,
                    'U_statistic': float(u_stat),
                    'p_value': float(p_val),
                    'significant_uncorrected': bool(p_val < 0.05),
                    'mean_1': float(vals1.mean()),
                    'mean_2': float(vals2.mean()),
                })
    # Apply Bonferroni correction
    n_comparisons = len(pairwise)
    for pw in pairwise:
        pw['p_value_bonferroni'] = min(pw['p_value'] * n_comparisons, 1.0)
        pw['significant_bonferroni'] = bool(pw['p_value_bonferroni'] < 0.05)

    test_results['pairwise_language_comparisons'] = pairwise

    return test_results


def correlate_borrowing_with_labse(df):
    """
    KEY ANALYSIS: Test whether lexical borrowing drives LaBSE scores.

    If the reviewer's hypothesis is correct (borrowing inflates LaBSE),
    we expect a positive Spearman correlation between borrowing rate
    and LaBSE score, especially within low-resource languages.
    """
    print("\nCorrelating borrowing rate with LaBSE scores...")
    correlations = {}

    # Per-language Spearman correlations
    for lang in sorted(df['language'].unique()):
        lang_df = df[df['language'] == lang].dropna(
            subset=['eng_borrowing_rate', 'cross_lang_labse']
        )
        if len(lang_df) >= 5:  # Need minimum observations for meaningful correlation
            rho, p_val = spearmanr(
                lang_df['eng_borrowing_rate'],
                lang_df['cross_lang_labse']
            )
            correlations[lang] = {
                'n': int(len(lang_df)),
                'spearman_rho': float(rho),
                'p_value': float(p_val),
                'significant': bool(p_val < 0.05),
                'mean_borrowing_rate': float(lang_df['eng_borrowing_rate'].mean()),
                'mean_labse': float(lang_df['cross_lang_labse'].mean()),
            }
            sig_marker = "*" if p_val < 0.05 else ""
            print(f"  {lang:25s}  rho={rho:+.3f}  p={p_val:.4f} {sig_marker}")

    # Overall correlation
    valid = df.dropna(subset=['eng_borrowing_rate', 'cross_lang_labse'])
    if len(valid) >= 5:
        rho, p_val = spearmanr(valid['eng_borrowing_rate'], valid['cross_lang_labse'])
        correlations['overall'] = {
            'n': int(len(valid)),
            'spearman_rho': float(rho),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
        }
        print(f"  {'overall':25s}  rho={rho:+.3f}  p={p_val:.4f}")

    # Low-resource only (Tagalog + Haitian Creole)
    low_df = df[df['language'].isin(['tagalog', 'haitian_creole'])].dropna(
        subset=['eng_borrowing_rate', 'cross_lang_labse']
    )
    if len(low_df) >= 5:
        rho, p_val = spearmanr(low_df['eng_borrowing_rate'], low_df['cross_lang_labse'])
        correlations['low_resource_combined'] = {
            'n': int(len(low_df)),
            'spearman_rho': float(rho),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
        }
        print(f"  {'low-resource combined':25s}  rho={rho:+.3f}  p={p_val:.4f}")

    # Haitian Creole: also correlate French borrowing with LaBSE
    ht_df = df[df['language'] == 'haitian_creole'].dropna(
        subset=['french_borrowing_rate', 'cross_lang_labse']
    )
    if len(ht_df) >= 5:
        rho, p_val = spearmanr(ht_df['french_borrowing_rate'], ht_df['cross_lang_labse'])
        correlations['haitian_creole_french_vs_labse'] = {
            'n': int(len(ht_df)),
            'spearman_rho': float(rho),
            'p_value': float(p_val),
            'significant': bool(p_val < 0.05),
            'description': 'French borrowing rate correlated with LaBSE in Haitian Creole',
        }
        print(f"  {'HC French→LaBSE':25s}  rho={rho:+.3f}  p={p_val:.4f}")

    return correlations


def generate_human_readable_summary(summary, top_terms, test_results, correlations, df):
    """Generate a human-readable text summary."""
    lines = []
    lines.append("=" * 80)
    lines.append("LEXICAL BORROWING ANALYSIS — SUMMARY REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PURPOSE: Quantify how often English (and French) medical terms are retained")
    lines.append("verbatim in translations, addressing reviewer concern that high LaBSE scores")
    lines.append("for low-resource languages may reflect transliteration rather than translation.")
    lines.append("")

    # --- Overall ---
    lines.append("-" * 80)
    lines.append("OVERALL STATISTICS")
    lines.append("-" * 80)
    n_terms = len(ENGLISH_MEDICAL_TERMS)
    n_french = len(FRENCH_MEDICAL_TERMS)
    lines.append(f"  English medical terms in vocabulary: {n_terms}")
    lines.append(f"  French medical terms in vocabulary: {n_french}")
    lines.append(f"  Total translations analyzed: {len(df)}")
    lines.append(f"  Mean English medical terms per source document: "
                 f"{df['n_original_eng_terms'].mean():.1f}")
    lines.append(f"  Overall mean English borrowing rate: "
                 f"{df['eng_borrowing_rate'].mean():.3f}")
    lines.append("")

    # --- By Language ---
    lines.append("-" * 80)
    lines.append("BORROWING RATES BY LANGUAGE")
    lines.append("-" * 80)
    lines.append(f"  {'Language':<25s}  {'Rate':>6s}  {'SD':>6s}  {'Resource':>8s}  {'Script':<15s}")
    lines.append(f"  {'-'*25}  {'-'*6}  {'-'*6}  {'-'*8}  {'-'*15}")
    for entry in sorted(summary['by_language'],
                        key=lambda x: x['mean_borrowing_rate'], reverse=True):
        lines.append(
            f"  {entry['language']:<25s}  {entry['mean_borrowing_rate']:>6.3f}  "
            f"{entry['std_borrowing_rate']:>6.3f}  {entry['resource_level']:>8s}  "
            f"{entry['script_type']:<15s}"
        )
    lines.append("")

    # --- By Resource Level ---
    lines.append("-" * 80)
    lines.append("BORROWING RATES BY RESOURCE LEVEL")
    lines.append("-" * 80)
    for entry in summary['by_resource_level']:
        lines.append(
            f"  {entry['resource_level']:<10s}  mean={entry['mean_borrowing_rate']:.3f}  "
            f"SD={entry['std_borrowing_rate']:.3f}  n={entry['n']}"
        )
    lines.append("")

    # --- By Script Type ---
    lines.append("-" * 80)
    lines.append("BORROWING RATES BY SCRIPT TYPE (Latin vs Non-Latin)")
    lines.append("-" * 80)
    for entry in summary['by_script_type']:
        lines.append(
            f"  {entry['script_type']:<15s}  mean={entry['mean_borrowing_rate']:.3f}  "
            f"SD={entry['std_borrowing_rate']:.3f}  n={entry['n']}"
        )
    lines.append("")

    # --- By Model ---
    lines.append("-" * 80)
    lines.append("BORROWING RATES BY MODEL")
    lines.append("-" * 80)
    for entry in sorted(summary['by_model'],
                        key=lambda x: x['mean_borrowing_rate'], reverse=True):
        lines.append(
            f"  {entry['model']:<20s}  mean={entry['mean_borrowing_rate']:.3f}  "
            f"SD={entry['std_borrowing_rate']:.3f}"
        )
    lines.append("")

    # --- Haitian Creole French Borrowing ---
    if 'haitian_creole_french_borrowing' in summary:
        lines.append("-" * 80)
        lines.append("HAITIAN CREOLE: FRENCH BORROWING")
        lines.append("-" * 80)
        ht = summary['haitian_creole_french_borrowing']
        lines.append(f"  English borrowing rate: {ht['mean_eng_borrowing_rate']:.3f}")
        lines.append(f"  French borrowing rate:  {ht['mean_french_borrowing_rate']:.3f}")
        lines.append(f"  (French rate = French-specific terms found / English source terms)")
        lines.append("")

    # --- Top Borrowed Terms ---
    lines.append("-" * 80)
    lines.append("TOP 20 MOST COMMONLY BORROWED ENGLISH TERMS")
    lines.append("-" * 80)
    for lang in ['tagalog', 'haitian_creole']:
        if lang in top_terms:
            lang_df = df[df['language'] == lang]
            n_total = len(lang_df)
            lines.append(f"\n  {lang.upper()} (n={n_total} translations):")
            lines.append(f"  {'Rank':<5s}  {'Term':<25s}  {'Count':>5s}  {'Frequency':>10s}")
            for i, entry in enumerate(top_terms[lang], 1):
                pct = entry['frequency'] * 100
                lines.append(
                    f"  {i:<5d}  {entry['term']:<25s}  {entry['count']:>5d}  "
                    f"{pct:>9.1f}%"
                )

    if 'haitian_creole_french' in top_terms and top_terms['haitian_creole_french']:
        lines.append(f"\n  HAITIAN CREOLE — FRENCH-ORIGIN TERMS:")
        lines.append(f"  {'Rank':<5s}  {'Term':<25s}  {'Count':>5s}  {'Frequency':>10s}")
        ht_n = len(df[df['language'] == 'haitian_creole'])
        for i, entry in enumerate(top_terms['haitian_creole_french'], 1):
            pct = entry['frequency'] * 100
            lines.append(
                f"  {i:<5d}  {entry['term']:<25s}  {entry['count']:>5d}  "
                f"{pct:>9.1f}%"
            )
    lines.append("")

    # --- Statistical Tests ---
    lines.append("-" * 80)
    lines.append("STATISTICAL TESTS")
    lines.append("-" * 80)

    if 'kruskal_wallis_resource_levels' in test_results:
        t = test_results['kruskal_wallis_resource_levels']
        sig = "SIGNIFICANT" if t['significant'] else "not significant"
        lines.append(f"\n  1. Kruskal-Wallis: Borrowing rate across resource levels")
        lines.append(f"     H = {t['H_statistic']:.2f}, p = {t['p_value']:.6f} ({sig})")
        lines.append(f"     Groups: {t['group_sizes']}")

    if 'mann_whitney_low_vs_others' in test_results:
        t = test_results['mann_whitney_low_vs_others']
        sig = "SIGNIFICANT" if t['significant'] else "not significant"
        lines.append(f"\n  2. Mann-Whitney U: Tagalog+Haitian Creole vs others")
        lines.append(f"     U = {t['U_statistic']:.2f}, p = {t['p_value']:.6f} ({sig})")
        lines.append(f"     Low-resource mean = {t['mean_low']:.3f}, "
                     f"Others mean = {t['mean_other']:.3f}")

    if 'mann_whitney_latin_vs_nonlatin' in test_results:
        t = test_results['mann_whitney_latin_vs_nonlatin']
        sig = "SIGNIFICANT" if t['significant'] else "not significant"
        lines.append(f"\n  3. Mann-Whitney U: Latin script vs Non-Latin script")
        lines.append(f"     U = {t['U_statistic']:.2f}, p = {t['p_value']:.6f} ({sig})")
        lines.append(f"     Latin mean = {t['mean_latin']:.3f}, "
                     f"Non-Latin mean = {t['mean_non_latin']:.3f}")

    if 'kruskal_wallis_models' in test_results:
        t = test_results['kruskal_wallis_models']
        sig = "SIGNIFICANT" if t['significant'] else "not significant"
        lines.append(f"\n  4. Kruskal-Wallis: Borrowing rate across models")
        lines.append(f"     H = {t['H_statistic']:.2f}, p = {t['p_value']:.6f} ({sig})")
    lines.append("")

    # --- Correlation with LaBSE ---
    lines.append("-" * 80)
    lines.append("CORRELATION: BORROWING RATE vs LaBSE SCORE (KEY HYPOTHESIS TEST)")
    lines.append("-" * 80)
    lines.append("")
    lines.append("  Reviewer hypothesis: If lexical borrowing inflates LaBSE scores,")
    lines.append("  we expect a POSITIVE correlation between borrowing rate and LaBSE.")
    lines.append("")
    lines.append(f"  {'Language':<30s}  {'n':>4s}  {'rho':>7s}  {'p-value':>10s}  {'Sig?':>5s}")
    lines.append(f"  {'-'*30}  {'-'*4}  {'-'*7}  {'-'*10}  {'-'*5}")

    # Show per-language first, then special aggregations
    lang_corrs = {k: v for k, v in correlations.items()
                  if k not in ['overall', 'low_resource_combined',
                               'haitian_creole_french_vs_labse']}
    for lang in sorted(lang_corrs.keys()):
        c = lang_corrs[lang]
        sig = "YES" if c['significant'] else "no"
        lines.append(
            f"  {lang:<30s}  {c['n']:>4d}  {c['spearman_rho']:>+7.3f}  "
            f"{c['p_value']:>10.4f}  {sig:>5s}"
        )

    if 'low_resource_combined' in correlations:
        c = correlations['low_resource_combined']
        sig = "YES" if c['significant'] else "no"
        lines.append(
            f"  {'low-resource combined':<30s}  {c['n']:>4d}  {c['spearman_rho']:>+7.3f}  "
            f"{c['p_value']:>10.4f}  {sig:>5s}"
        )
    if 'overall' in correlations:
        c = correlations['overall']
        sig = "YES" if c['significant'] else "no"
        lines.append(
            f"  {'OVERALL':<30s}  {c['n']:>4d}  {c['spearman_rho']:>+7.3f}  "
            f"{c['p_value']:>10.4f}  {sig:>5s}"
        )
    if 'haitian_creole_french_vs_labse' in correlations:
        c = correlations['haitian_creole_french_vs_labse']
        sig = "YES" if c['significant'] else "no"
        lines.append(
            f"  {'HC French borrow→LaBSE':<30s}  {c['n']:>4d}  {c['spearman_rho']:>+7.3f}  "
            f"{c['p_value']:>10.4f}  {sig:>5s}"
        )
    lines.append("")

    # --- Interpretation ---
    lines.append("-" * 80)
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append("")

    # Auto-generate interpretation based on results
    if 'low_resource_combined' in correlations:
        c = correlations['low_resource_combined']
        if c['significant'] and c['spearman_rho'] > 0:
            lines.append("  FINDING: There IS a significant positive correlation between")
            lines.append("  borrowing rate and LaBSE score in low-resource languages,")
            lines.append("  supporting the reviewer's concern that lexical borrowing may")
            lines.append("  partially inflate LaBSE scores.")
        elif c['significant'] and c['spearman_rho'] < 0:
            lines.append("  FINDING: There is a significant NEGATIVE correlation between")
            lines.append("  borrowing rate and LaBSE score in low-resource languages.")
            lines.append("  This goes AGAINST the reviewer's hypothesis — more borrowing")
            lines.append("  is associated with LOWER LaBSE scores.")
        else:
            lines.append("  FINDING: There is NO significant correlation between borrowing")
            lines.append("  rate and LaBSE score in low-resource languages (rho="
                         f"{c['spearman_rho']:+.3f}, p={c['p_value']:.3f}).")
            lines.append("  This suggests that lexical borrowing does NOT meaningfully inflate")
            lines.append("  LaBSE scores, undermining the reviewer's concern.")

    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    lines.append("")

    return "\n".join(lines)


def save_results(df, summary, top_terms, test_results, correlations, report_text):
    """Save all results to output files."""
    print("\nSaving results...")

    # 1. Per-translation results (JSON)
    # Convert lists/sets for JSON serialization
    per_trans = df.copy()
    # Ensure borrowed_eng_terms is a list (not set)
    per_trans['borrowed_eng_terms'] = per_trans['borrowed_eng_terms'].apply(
        lambda x: x if isinstance(x, list) else list(x) if isinstance(x, set) else []
    )
    per_trans['french_terms_found'] = per_trans['french_terms_found'].apply(
        lambda x: x if isinstance(x, list) else list(x) if isinstance(x, set) else []
    )

    # Convert numpy types for JSON
    per_trans_records = per_trans.to_dict('records')
    for rec in per_trans_records:
        for k, v in rec.items():
            if isinstance(v, (np.integer,)):
                rec[k] = int(v)
            elif isinstance(v, (np.floating,)):
                rec[k] = float(v) if not np.isnan(v) else None
            elif isinstance(v, np.bool_):
                rec[k] = bool(v)

    results_path = OUTPUT_DIR / "lexical_borrowing_results.json"
    with open(results_path, 'w') as f:
        json.dump(per_trans_records, f, indent=2, ensure_ascii=False)
    print(f"  Per-translation results: {results_path}")

    # 2. Summary (JSON)
    summary_data = {
        'summary_statistics': summary,
        'top_borrowed_terms': top_terms,
        'statistical_tests': test_results,
        'labse_correlations': correlations,
        'metadata': {
            'n_english_terms': len(ENGLISH_MEDICAL_TERMS),
            'n_french_terms': len(FRENCH_MEDICAL_TERMS),
            'n_translations': len(df),
            'languages': sorted(df['language'].unique().tolist()),
            'models': sorted(df['model'].unique().tolist()),
            'n_documents': int(df['doc_id'].nunique()),
        }
    }

    summary_path = OUTPUT_DIR / "lexical_borrowing_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"  Summary JSON: {summary_path}")

    # 3. Human-readable summary (TXT)
    report_path = OUTPUT_DIR / "lexical_borrowing_summary.txt"
    with open(report_path, 'w') as f:
        f.write(report_text)
    print(f"  Human-readable report: {report_path}")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    print("=" * 80)
    print("LEXICAL BORROWING QUANTIFICATION ANALYSIS")
    print("=" * 80)

    # Load data
    results_df, metrics_df = load_data()

    # Core analysis: compute borrowing rates
    df = analyze_borrowing(results_df, metrics_df)

    # Aggregated statistics
    summary = compute_summary_statistics(df)

    # Top borrowed terms for Tagalog and Haitian Creole
    top_terms = compute_top_borrowed_terms(df)

    # Statistical tests
    test_results = run_statistical_tests(df)

    # Key hypothesis test: borrowing rate vs LaBSE correlation
    correlations = correlate_borrowing_with_labse(df)

    # Generate human-readable report
    report_text = generate_human_readable_summary(
        summary, top_terms, test_results, correlations, df
    )

    # Save everything
    save_results(df, summary, top_terms, test_results, correlations, report_text)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
