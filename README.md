# Multi-Method Validation of Large Language Model Medical Translation Across High- and Low-Resource Languages

**Chukwuebuka Anyaegbuna, Eduardo Juan Perez Guerrero, Jerry Liu, Timothy Keyes, April Liang, Natasha Steele, Stephen Ma, Jonathan Chen, Kevin Schulman**
Stanford University

---

## Overview

This repository contains the code and data for a multi-method validation study of large language model (LLM) medical translation fidelity. We evaluate **4 frontier LLMs** (Claude Opus 4.5, GPT-5.1, Kimi K2, Gemini 3 Pro) across **8 languages** and **22 standardized clinical documents** from MedlinePlus, CDC vaccine information sheets, and American Cancer Society patient education materials.

Our **5-layer validation framework** addresses the circularity critique inherent in back-translation evaluation:

1. **Back-translation fidelity** -- LaBSE, BLEU, BERTScore, COMET on round-trip translations
2. **Professional translation comparison** -- Direct comparison to human-translated references (co-primary outcome)
3. **Cross-model back-translation sensitivity** -- Forward-translate with one model, back-translate with another (1,576 pairs across 9 model pairings)
4. **Inter-model concordance** -- Pairwise agreement among independent model translations (1,047 pairs)
5. **Lexical borrowing quantification** -- Measuring verbatim English term retention in low-resource language translations

### What each metric actually compares

`cross_lang_labse`, `cross_lang_xlm_roberta`, `cross_lang_mbert` and
`cross_lang_comet_qe` are **misnomers kept for backwards compatibility** with the
published output files. All four compare the **English back-translation against the
English source document**. Both sides are English.

No metric in this pipeline compares the English source directly against the
target-language forward translation.

| Field | First argument | Second argument |
|---|---|---|
| `cross_lang_*` | English back-translation | English source |
| `backtrans_*` | English back-translation | English source |
| `prof_backtrans_*` | English back-translation of the professional translation | English source |
| `llm_vs_prof_backtrans_*` | English back-translation (LLM) | English back-translation (professional) |
| `same_lang_*` | LLM forward translation (target language) | Professional translation (target language) |

Embedding metrics also process a fixed maximum input length (LaBSE 256 tokens,
BERTScore and COMET 512). Documents here average ~900 words, so whole-document
scoring truncates. Segment-level scoring is implemented in
`recompute_labse_segmented.py`.

### Languages

| Language | Script | Resource Level | CommonCrawl % |
|----------|--------|----------------|---------------|
| Russian | Cyrillic | High | 6.48 |
| Chinese (Simplified) | Hanzi | High | 6.18 |
| Spanish | Latin | High | 4.41 |
| Vietnamese | Latin (diacritics) | High | 1.08 |
| Korean | Hangul | Medium | 0.80 |
| Arabic | Arabic (RTL) | Medium | 0.67 |
| Tagalog | Latin | Low | 0.008 |
| Haitian Creole | Latin | Low | 0.003 |

Resource levels based on CommonCrawl representation: High >1%, Medium 0.1--1%, Low <0.1%.

---

## Key Results

- **All models achieve high semantic preservation**: LaBSE > 0.92 across all languages
- **Low- vs high-resource languages**: No significant difference in translation fidelity (p = 0.066)
- **Cross-model sensitivity analysis**: Mean delta = -0.0009 between same-model and cross-model back-translation, falsifying the circularity concern
- **Inter-model concordance**: Mean LaBSE = 0.946 across 1,047 pairwise comparisons
- **Lexical borrowing**: No correlation with fidelity scores (Spearman rho = +0.018, p = 0.82)

---

## Repository Structure

```
data/                          Source documents and professional translations
  extracted_text/              22 documents x 9 language versions
output/
  medlineplus_results/         702 forward + back translation pairs
  medlineplus_metrics/         LaBSE, BLEU, COMET, BERTScore for all pairs
  statistical_tests/           Kruskal-Wallis, Mann-Whitney, Dunn's post-hoc tests
  cross_model_backtranslation/ 1,576 cross-model back-translation pairs
  inter_model_concordance/     1,047 inter-model pairwise comparisons
  lexical_borrowing/           English term retention analysis
  github_pages/                Charts and interactive results
scripts/                       Analysis pipeline
Images/                        Figures
```

---

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/run_medlineplus_pipeline.py` | Main translation pipeline (forward + back-translation) |
| `scripts/calculate_medlineplus_metrics.py` | Metric computation (LaBSE, BLEU, COMET, BERTScore) |
| `scripts/cross_model_backtranslation.py` | Cross-model sensitivity analysis |
| `scripts/inter_model_concordance.py` | Inter-model concordance analysis |
| `scripts/lexical_borrowing_analysis.py` | Lexical borrowing quantification |
| `scripts/config.py` | Language, model, and prompt configuration |

---

## Requirements

- Python 3.11+
- Key packages: `scipy`, `sentence-transformers`, `bert-score`, `comet`, `sacrebleu`, `openai`, `anthropic`, `google-generativeai`
- API keys required for translation (set as environment variables): `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MOONSHOT_API_KEY`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Citation

If you use this dataset or methodology, please cite:

```
Anyaegbuna C, Perez Guerrero EJ, Liu J, Keyes T, Liang A, Steele N, Ma S, Chen J, Schulman K.
Multi-Method Validation of Large Language Model Medical Translation
Across High- and Low-Resource Languages. 2026.
```

---

## License

Source medical documents are derived from CDC Vaccine Information Statements and American Cancer Society patient education materials, which are public domain / publicly available resources. Code in this repository is provided for research purposes.
