# LLM Medical Translation Study: Evaluating Fidelity Across Languages

## Research Question

**Can LLMs maintain translation fidelity for medical documents across both high-resource and low-resource languages?**

We use back-translation as our evaluation method: translating English → Target Language → English, then measuring how well the original meaning is preserved. This approach lets us assess translation quality without requiring human evaluators for each language.

---

## Executive Summary

This study evaluates **4 frontier LLMs** on medical translation quality across **8 languages** (including 2 low-resource: Tagalog and Haitian Creole) using **22 professionally-translated health documents** from CDC vaccine information sheets and the American Cancer Society.

### Key Findings

1. **Low-resource languages achieve comparable semantic fidelity to high-resource languages.** Tagalog (LaBSE: 0.950) and Haitian Creole (0.955) achieve scores indistinguishable from Spanish (0.954) and Vietnamese (0.953), indicating LLMs preserve medical meaning equally well regardless of training data availability.

2. **Semantic preservation is consistent; lexical overlap varies by linguistic factors.** LaBSE scores cluster tightly (0.937-0.976) across all languages, while BLEU scores vary widely (15.5-54.3) based on script type and morphology rather than resource level.

3. **All models achieve high semantic preservation** (LaBSE > 0.92), indicating LLMs reliably preserve medical meaning through round-trip translation.

4. **Claude Opus 4.5** achieves the highest semantic preservation (LaBSE: 0.987), while **Gemini 3 Pro** leads in professional translation alignment (COMET: 0.876).

---

## Study Design

### Two-Part Evaluation Framework

| Analysis | Question | Method |
|----------|----------|--------|
| **Analysis 1: Back-Translation Fidelity** | Does LLM translation preserve meaning? | Back-translate LLM output → compare to original English |
| **Analysis 2: Professional Comparison** | How do LLM translations compare to professionals? | Compare LLM translation directly to professional translation |
| **Validation** | Is back-translation a valid evaluation method? | Back-translate professional translations → compare to original English |

**Validation establishes our baseline**: professional translations back-translated through LLMs achieve LaBSE scores of 0.92-0.94, confirming back-translation reliably preserves meaning.

### Documents
- **22 health education documents** (704 translation pairs)
  - 11 Vaccine Information Statements (VIS) from CDC/Immunize.org
  - 11 Cancer education materials from American Cancer Society

### Languages Evaluated

| Language | Script | Resource Level | CommonCrawl % |
|----------|--------|----------------|---------------|
| Russian | Cyrillic | High | 6.48 |
| Chinese (Simplified) | Hanzi | High | 6.18 |
| Spanish | Latin | High | 4.41 |
| Vietnamese | Latin (+ diacritics) | High | 1.08 |
| Korean | Hangul | Medium | 0.80 |
| Arabic | Arabic (RTL) | Medium | 0.67 |
| **Tagalog** | Latin | **Low** | 0.008 |
| **Haitian Creole** | Latin | **Low** | 0.003 |

Resource levels based on CommonCrawl representation: High >1%, Medium 0.1-1%, Low <0.1%.

### Models Tested

| Model | Provider |
|-------|----------|
| GPT-5.1 | OpenAI |
| Claude Opus 4.5 | Anthropic |
| Gemini 3 Pro | Google |
| Kimi K2 | Moonshot AI |

---

## Results

### Analysis 1: Back-Translation Fidelity

All models maintain high semantic fidelity through round-trip translation:

| Model | LaBSE | BLEU |
|-------|-------|------|
| **Claude Opus 4.5** | **0.987** | **68.6** |
| GPT-5.1 | 0.957 | 64.3 |
| Kimi K2 | 0.940 | 54.9 |
| Gemini 3 Pro | 0.921 | 61.5 |

**Claude Opus 4.5** achieves the highest semantic preservation, indicating the most reliable meaning transfer through translation.

### Analysis 2: Professional Translation Comparison

| Model | COMET | BLEU | BERTScore |
|-------|-------|------|-----------|
| **Gemini 3 Pro** | **0.876** | **39.4** | 0.845 |
| Claude Opus 4.5 | 0.873 | 37.3 | **0.859** |
| GPT-5.1 | 0.871 | 36.0 | 0.844 |
| Kimi K2 | 0.872 | 36.0 | 0.840 |

All models perform within a narrow band (~1% COMET spread), suggesting frontier LLMs have converged on medical translation quality.

### Language Performance: The Key Finding

| Language | Resource | Semantic (LaBSE) | Lexical (BLEU) |
|----------|----------|------------------|----------------|
| Spanish | High | 0.954 | **54.3** |
| Vietnamese | High | 0.953 | 50.1 |
| **Tagalog** | **Low** | 0.950 | 43.8 |
| **Haitian Creole** | **Low** | **0.955** | 37.2 |
| Arabic | Medium | 0.976 | 41.6 |
| Russian | High | 0.945 | 33.4 |
| Korean | Medium | 0.937 | 21.7 |
| Chinese | High | 0.942 | 15.5 |

**Key insight**: Low-resource languages (Tagalog, Haitian Creole) achieve semantic fidelity comparable to high-resource languages. The variation in BLEU scores reflects linguistic factors (script, morphology) rather than resource level.

---

## Visualizations

### Semantic vs Lexical Fidelity by Language
![Semantic vs Lexical](output/github_pages/charts/semantic_vs_lexical_fidelity.png)

### Model Comparison
![Model Comparison](output/github_pages/charts/model_comparison_same_lang.png)

### Language Comparison
![Language Comparison](output/github_pages/charts/language_comparison_same_lang.png)

---

## Key Insights

### 1. Low-Resource Languages Perform Surprisingly Well
Tagalog and Haitian Creole—languages with <0.01% CommonCrawl representation—achieve semantic fidelity scores comparable to Spanish and Vietnamese. This suggests frontier LLMs can reliably translate medical content for historically underserved language communities.

### 2. Semantic vs Lexical Metrics Tell Different Stories
- **Semantic fidelity (LaBSE)**: Consistently high across all languages (0.937-0.976)
- **Lexical fidelity (BLEU)**: Varies widely (15.5-54.3) based on script and morphology

For health materials, semantic preservation matters most—patients need accurate information, not necessarily the exact wording a professional translator would choose.

### 3. Model Differentiation is Subtle
All four frontier models perform within a narrow band (~3% COMET spread), suggesting model selection is less critical than language pair selection for medical translation.

### 4. Script Type Affects Lexical Metrics
Languages using Latin-based scripts (Spanish, Vietnamese, Tagalog) show higher BLEU scores, likely due to tokenization similarities with English. This doesn't indicate better translations—semantic metrics confirm meaning is preserved equally well across all scripts.

### 5. Back-Translation Validates LLM Quality
Professional translations back-translated through LLMs achieve LaBSE scores of 0.92-0.94, establishing back-translation as a valid evaluation method.

---

## Implications for Health Equity

These findings have significant implications for medical translation access:

- **LLMs could democratize medical translation** for speakers of low-resource languages where professional translation services are unavailable or delayed.
- **Meaning preservation is reliable** — patients receive accurate health information regardless of their language's "resource level."
- **LLM translation should complement, not replace, professional translation** for high-stakes clinical documents. Our results support LLM use for patient education materials where general comprehension is the goal.

---

## Files

| File | Description |
|------|-------------|
| `output/github_pages/medlineplus_backtranslation_report.xlsx` | Full Excel report with all metrics |
| `output/github_pages/charts/` | Visualization PNG files |
| `output/github_pages/index.html` | Interactive results page |
| `output/medlineplus_metrics/all_metrics.json` | Raw metrics data (JSON) |
| `output/medlineplus_metrics/summary.json` | Aggregated summary statistics |
| `data/extracted_text/` | Source text files (22 docs × 9 languages) |

---

## Citation

If you use this dataset or methodology, please cite:

```
Evaluating Large Language Model Translation Fidelity for Medical Documents
Across High- and Low-Resource Languages
2026
```

---

*Updated: 2026-01-19*
