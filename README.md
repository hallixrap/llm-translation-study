# LLM Back-Translation Study: MedlinePlus Health Materials

A comprehensive evaluation of how well frontier LLMs translate patient health education materials, using back-translation methodology and comparison with professional human translations.

**Live Results:** [https://hallixrap.github.io/llm-translation-study/](https://hallixrap.github.io/llm-translation-study/)

## Study Overview

| Dimension | Details |
|-----------|---------|
| **Documents** | 22 health documents (11 CDC Vaccine VIS + 11 American Cancer Society materials) |
| **Languages** | Spanish, Chinese (Simplified), Vietnamese, Russian, Arabic, Korean, Tagalog, Haitian Creole |
| **Models** | Claude Opus 4.5, GPT-5.1, Gemini 3 Pro, Kimi K2 |
| **Translation Pairs** | 704 (22 docs × 8 languages × 4 models) |
| **API Calls** | 2,112 (3 translations per pair) |

## Three Evaluation Goals

### Goal 1: LLM Meaning Preservation
**LLM back-translation vs Original English**

Measures how well meaning is preserved through the LLM's translation round-trip (English → Target → English).

| Model | BLEU | LaBSE | BERTScore |
|-------|------|-------|-----------|
| **Claude Opus 4.5** | **67.8** | **0.983** | **0.946** |
| GPT-5.1 | 63.7 | 0.953 | 0.927 |
| Gemini 3 Pro | 61.2 | 0.916 | 0.915 |
| Kimi K2 | 54.7 | 0.934 | 0.916 |

### Goal 2: Professional Alignment
**LLM translation vs Professional human translation**

Measures how closely LLM translations match professional human translations (same target language comparison).

| Model | BLEU | COMET | BERTScore |
|-------|------|-------|-----------|
| **Gemini 3 Pro** | **38.2** | **0.867** | 0.839 |
| Claude Opus 4.5 | 35.8 | 0.864 | **0.853** |
| GPT-5.1 | 34.8 | 0.862 | 0.838 |
| Kimi K2 | 34.5 | 0.864 | 0.835 |

### Goal 3: Professional Baseline
**Professional back-translation vs Original English**

Establishes upper bound by measuring how well professional translations back-translate (using LLM as back-translator).

| Model (back-translator) | BLEU | LaBSE | BERTScore |
|-------------------------|------|-------|-----------|
| GPT-5.1 | **54.8** | 0.936 | 0.913 |
| Claude Opus 4.5 | 53.7 | **0.938** | **0.919** |
| Gemini 3 Pro | 46.7 | 0.923 | 0.908 |
| Kimi K2 | 42.5 | 0.929 | 0.906 |

## Key Findings

1. **All LLMs preserve health information reliably** — LaBSE scores of 0.91-0.98 indicate core medical content is maintained across translations.

2. **Claude Opus 4.5 excels at faithful translation** — Best at preserving exact meaning through the round-trip (Goal 1).

3. **Gemini 3 Pro writes most like human translators** — Closest stylistic match to professional translations (Goal 2).

4. **LLM translations are surprisingly "stable"** — LLM back-translations (Goal 1) score higher than professional back-translations (Goal 3), suggesting LLMs produce more consistent round-trip results.

5. **Script type matters for BLEU, not for semantics** — Chinese/Korean show lower BLEU due to tokenization differences, but semantic scores (LaBSE) remain high.

## Metrics Explained

| Metric | What It Measures | Range | Best For |
|--------|-----------------|-------|----------|
| **BLEU** | N-gram word overlap | 0-100 | Exact wording similarity |
| **LaBSE** | Semantic meaning similarity | 0-1 | Cross-script comparison |
| **BERTScore** | Contextual embedding similarity | 0-1 | Overall quality |
| **COMET** | Human judgment correlation | 0-1 | Translation quality rating |

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TRANSLATION PIPELINE (per combination)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: Forward Translation                                        │
│  ┌───────────────┐      ┌───────────────┐                          │
│  │ English       │ ──── │ Target        │                          │
│  │ Original      │ LLM  │ Language      │                          │
│  └───────────────┘      └───────────────┘                          │
│                                │                                    │
│  Step 2: LLM Back-Translation  │                                    │
│                                ▼                                    │
│                         ┌───────────────┐                          │
│                         │ LLM Back-     │ ──→ Compare vs Original   │
│                         │ Translation   │     (Goal 1)              │
│                         └───────────────┘                          │
│                                                                     │
│  Step 3: Professional Back-Translation                              │
│  ┌───────────────┐      ┌───────────────┐                          │
│  │ Professional  │ ──── │ Prof Back-    │ ──→ Compare vs Original   │
│  │ Translation   │ LLM  │ Translation   │     (Goal 3)              │
│  └───────────────┘      └───────────────┘                          │
│                                                                     │
│  Goal 2: Compare LLM Translation vs Professional Translation        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `index.html` | Interactive results page |
| `all_metrics.json` | Raw metrics data (JSON) |
| `summary.json` | Aggregated summary statistics |
| `all_results.json` | Full translation data |

## Data Sources

- **Vaccine VIS**: CDC Vaccine Information Statements from Immunize.org
- **Cancer Materials**: American Cancer Society patient education documents
- **Professional Translations**: Official translations from MedlinePlus in all 8 languages

## Citation

```
LLM Back-Translation Study for MedlinePlus Health Materials
Stanford University, December 2025
```

## Contact

For questions about this study, please contact the research team.
