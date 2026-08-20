# Frontier Large Language Models for Medical Translation: A Multi-Method Benchmark Across Eight Languages

**Chukwuebuka Anyaegbuna, Eduardo Juan Perez Guerrero, Jerry Sheng-Tung Liu, Timothy Keyes, April Liang, Natasha Steele, Stephen Ma, Jonathan Chen, Kevin Schulman**
Stanford University

---

## Overview

Code and data for a multi-method benchmark of large language model (LLM) medical
translation fidelity. Four frontier LLMs (Claude Opus 4.5, GPT-5.1, Kimi K2 Thinking,
Gemini 3 Pro) translated 22 patient education documents into 8 languages and back
into English. The 22 documents are 11 CDC Vaccine Information Statements and 11
American Cancer Society patient education materials, each with a professional human
translation in all eight languages.

704 forward and back translation pairs were attempted and 702 analyzed.

### Read this before reusing any output file

Metrics built on learned representations process a fixed maximum input length (LaBSE
256 wordpiece tokens, BERTScore and COMET 512). The documents average about 900 words,
so scoring a whole document as a single unit silently truncates it: every
whole-document score reflects only the opening fifth or so of the text.

**Every result in the paper is computed on aligned 150-word segments**, not on whole
documents. Whole-document values survive in this repository for transparency and are
reported side by side with the segment-level values in Supplementary Table S7 of the
paper. Do not treat the whole-document columns as the study's findings.

### What each metric actually compares

All of the round-trip metrics compare the English back-translation against the English
source document. The field names carry legacy prefixes; the table is the authority.

| Field | First argument | Second argument |
|---|---|---|
| `cross_lang_*` | English back-translation | English source |
| `backtrans_*` | English back-translation | English source |
| `prof_backtrans_*` | English back-translation of the professional translation | English source |
| `llm_vs_prof_backtrans_*` | English back-translation (LLM) | English back-translation (professional) |
| `same_lang_*` | LLM forward translation (target language) | Professional translation (target language) |

### The five analyses

1. **Back-translation fidelity** — each English back-translation against the English source, using LaBSE, BERTScore and chrF. Primary analysis.
2. **Comparison with professional translations** — an external reference independent of back-translation, using BERTScore and chrF.
3. **Cross-model sensitivity** — each forward translation back-translated by the other models and rescored with LaBSE (1,576 attempted, 1,550 analyzed).
4. **Inter-model concordance** — the four models' forward translations compared with each other (1,047 pairs).
5. **Verbatim English retention** — how often each of 213 English medical terms survived untranslated, in LLM output and professional translation alike.

Analysis 1 is the primary comparison. Analyses 2 to 5 are secondary and exist to test
whether the measurements in analysis 1 can be trusted.

COMET was computed but is **not reported**. Its model does not cover Haitian Creole,
and on 150-word segments it returned values from −0.62 to 0.96 with a third below 0.3,
a spread irreconcilable with every other measure on the same translations.

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

Resource level denotes estimated availability of text in model training corpora, taken
from CommonCrawl representation (High >1%, Medium 0.1–1%, Low <0.1%). It is not a
statement about speaker numbers or clinical importance.

---

## Key results

Segment-level LaBSE unless stated otherwise. These are the values reported in the
paper.

- **Fidelity did not differ by resource level.** Low-resource 0.885 against
  high-resource 0.880 (difference 0.005; 95% CI −0.019 to 0.029; P = 0.57). By
  language the range was 0.856 to 0.921.
- **Document type mattered far more than language.** Cancer materials 0.934 against
  vaccine statements 0.832 (difference 0.102; 95% CI 0.090 to 0.114; P < 0.001), about
  twenty times the difference between resource groups. The same gap appears in the
  professional human translations put through the identical round trip, 0.909 against
  0.813.
- **Model differences were partly an artifact of self-scoring.** Claude Opus 4.5
  scored 0.941, GPT-5.1 0.879, Kimi K2 Thinking 0.861, Gemini 3 Pro 0.853. When a
  different model performed the back-translation, Claude's score fell by 0.025 and its
  lead over GPT-5.1 narrowed from 0.060 to 0.032. Overall the same-model and
  cross-model means were 0.883 and 0.883 (difference −0.001; P = 0.06).
- **Results did not depend on any single model.** Across 1,047 comparisons the four
  models produced similar translations of the same documents (0.891). Convergence does
  not by itself establish accuracy: two models resembled each other more than either
  resembled the professional translation, chrF 75.0 between models against 62.8 with
  the professional reference (P < 0.001).
- **Untranslated English terminology did not explain the scores.** Retention
  correlated *negatively* with fidelity (Spearman rho −0.218, P < 0.001). Professional
  human translators retained more English medical terminology than the models did,
  33.1% against 27.3%.
- **No evidence of memorization.** A continuation probe scored 39.3 chrF against 63
  for translation from the source, and unpublished controls scored higher than
  published text (42.0 against 39.3, P < 0.001).

None of these metrics has a clinically validated passing score, and none has been
related to patient comprehension. The professional translations, scored through the
identical pipeline, are the reference distribution for this corpus.

---

## Repository structure

```
data/                          Source documents and professional translations
  extracted_text/              22 documents x 9 language versions
output/
  medlineplus_results/         702 forward + back translation pairs
  medlineplus_metrics/         whole-document metrics (superseded; see note above)
  labse_segmented/             segment-level LaBSE, the paper's primary metric
  statistical_tests/           Kruskal-Wallis, Mann-Whitney, Dunn's post-hoc tests
  cross_model_backtranslation/ 1,576 cross-model back-translation pairs
  inter_model_concordance/     1,047 inter-model pairwise comparisons
  lexical_borrowing/           English term retention analysis
  github_pages/                Charts and interactive results
scripts/                       Analysis pipeline
Images/                        Figures
```

Directory names beginning `medlineplus_` are historical. The corpus is CDC and
American Cancer Society material, as described above.

---

## Scripts

Pipeline and original analyses:

| Script | Description |
|--------|-------------|
| `scripts/run_medlineplus_pipeline.py` | Translation pipeline (forward + back-translation) |
| `scripts/calculate_medlineplus_metrics.py` | Whole-document metric computation |
| `scripts/cross_model_backtranslation.py` | Cross-model sensitivity analysis |
| `scripts/inter_model_concordance.py` | Inter-model concordance analysis |
| `scripts/lexical_borrowing_analysis.py` | Verbatim English retention |
| `scripts/config.py` | Language, model and prompt configuration |

Segment-level rescoring and verification:

| Script | Description |
|--------|-------------|
| `recompute_labse_segmented.py` | Segment-level LaBSE, the paper's primary metric |
| `recompute_bertscore_comet_segmented.py` | Segment-level BERTScore and COMET |
| `scripts/recompute_concordance_chrf.py` | Segment-level chrF for inter-model concordance |
| `professional_reference.py` | Professional translations as the reference distribution |
| `memorisation_prefix_probe.py` | Continuation probe for memorization |
| `scripts/verify_manuscript_numbers.py` | Recomputes every number in the manuscript from the output files |

---

## Requirements

Python 3.11.

Key packages: `scipy`, `scikit-posthocs`, `sentence-transformers`, `bert-score`,
`sacrebleu`, `unbabel-comet`, `openai`, `anthropic`, `google-generativeai`.

```bash
pip install scipy scikit-posthocs sentence-transformers bert-score sacrebleu unbabel-comet openai anthropic google-generativeai
```

Library versions are **not pinned**. The analysis environment was rebuilt during
revision, so a lockfile generated now would not describe the environment that produced
the published numbers. Rerunning against current releases may shift values in the
third decimal place.

Translation requires API keys, set as environment variables: `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MOONSHOT_API_KEY`. Scoring and verification
need no keys.

---

## Citation

```
Anyaegbuna C, Perez Guerrero EJ, Liu JS, Keyes T, Liang A, Steele N, Ma S, Chen J, Schulman K.
Frontier Large Language Models for Medical Translation: A Multi-Method Benchmark
Across Eight Languages. 2026.
```

---

## License

Source medical documents derive from CDC Vaccine Information Statements and American
Cancer Society patient education materials, which are public domain or publicly
available resources. Code in this repository is provided for research purposes.
