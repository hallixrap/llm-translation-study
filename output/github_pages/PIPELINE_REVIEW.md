# NLP Pipeline Technical Review

This document provides a technical overview of the back-translation evaluation pipeline for NLP review.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACK-TRANSLATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DATA EXTRACTION (Multiple Methods)                                      │
│  ┌─────────────┐    ┌─────────────────────────┐    ┌─────────────┐         │
│  │  PDF/DOCX   │───▶│  Hybrid Extraction:     │───▶│ .txt Files  │         │
│  │  (198 docs) │    │  - DOCX: python-docx    │    │             │         │
│  └─────────────┘    │  - PDF: pdftotext/PyMuPDF│   └─────────────┘         │
│                     │  - 2-col: LLM screenshot │                            │
│                     └─────────────────────────┘                             │
│       Note: Arabic PDFs use PyMuPDF for RTL text handling                  │
│                                                                             │
│  2. TRANSLATION (3 steps per combination)                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  English    │───▶│    LLM      │───▶│   Target    │                     │
│  │  Original   │    │  (4 models) │    │  Language   │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                           │                   │                             │
│                           │                   ▼                             │
│                           │            ┌─────────────┐                     │
│                           │            │ LLM Back-   │ ──→ Goal 1          │
│                           └───────────▶│ Translation │                     │
│                                        └─────────────┘                     │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐                                        │
│  │ Professional│───▶│ Prof Back-  │ ──→ Goal 3                             │
│  │ Translation │LLM │ Translation │                                        │
│  └─────────────┘    └─────────────┘                                        │
│                                                                             │
│  3. EVALUATION                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Goal 1: LLM Back-Trans vs Original (meaning preservation)         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐                  │   │
│  │  │  BLEU   │ │  LaBSE  │ │BERTScore│ │ COMET-QE │                  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Goal 2: LLM Translation vs Professional (same-language alignment) │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌─────────┐                 │   │
│  │  │  BLEU   │ │  chrF   │ │ BERTScore │ │  COMET  │                 │   │
│  │  └─────────┘ └─────────┘ └───────────┘ └─────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Goal 3: Professional Back-Trans vs Original (baseline)            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                               │   │
│  │  │  BLEU   │ │  LaBSE  │ │BERTScore│                               │   │
│  │  └─────────┘ └─────────┘ └─────────┘                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `extract_pdf_text.py` | Extract text from PDFs | PDF files | Text files |
| `extract_arabic_pymupdf.py` | RTL-aware Arabic extraction | Arabic PDFs | Arabic text |
| `run_medlineplus_pipeline.py` | Run LLM translations (all 3 steps) | English text + Professional translations | Translations + back-translations |
| `calculate_medlineplus_metrics.py` | Compute all metrics for Goals 1, 2, 3 | Translation results | Metrics JSON |
| `generate_github_outputs.py` | Generate reports/charts | Metrics | Excel, PNG, HTML |

## Three Evaluation Goals

### Goal 1: LLM Meaning Preservation
**Comparison:** LLM back-translation vs Original English

Measures how well the LLM's translation round-trip preserves meaning.

**Metrics:**
- BLEU (sacrebleu)
- LaBSE (sentence-transformers)
- BERTScore (bert-score)
- COMET-QE (unbabel-comet, reference-free)

### Goal 2: Professional Alignment
**Comparison:** LLM translation vs Professional translation (same target language)

Measures how closely LLM output matches human expert translations.

**Metrics:**
- BLEU (sacrebleu)
- chrF (sacrebleu)
- BERTScore (bert-score)
- COMET (unbabel-comet, with reference)

### Goal 3: Professional Baseline
**Comparison:** Professional back-translation vs Original English

Establishes an upper bound by measuring how well professional translations back-translate.

**Metrics:**
- BLEU (sacrebleu)
- LaBSE (sentence-transformers)
- BERTScore (bert-score)

## Metric Implementations

### BLEU (Bilingual Evaluation Understudy)
- **Library**: `sacrebleu`
- **Implementation**: `sentence_bleu(hypothesis, [reference])`
- **Range**: 0-100
- **What it measures**: N-gram precision overlap
- **Limitations**: Sensitive to exact word matches; penalizes valid paraphrases; poor for non-Latin scripts

### chrF (Character n-gram F-score)
- **Library**: `sacrebleu`
- **Implementation**: `CHRF().sentence_score(hypothesis, [reference])`
- **Range**: 0-100
- **What it measures**: Character-level overlap
- **Advantage**: More robust than BLEU for morphologically rich languages

### BERTScore
- **Library**: `bert_score`
- **Model**: `microsoft/deberta-xlarge-mnli`
- **Implementation**: `score(hypotheses, references, lang='xx')`
- **Range**: 0-1
- **What it measures**: Contextual embedding similarity
- **Advantage**: Captures semantic similarity beyond surface forms

### COMET (Crosslingual Optimized Metric for Evaluation of Translation)
- **Library**: `comet`
- **Model**: `Unbabel/wmt22-comet-da`
- **Implementation**: `model.predict([{src, mt, ref}])`
- **Range**: 0-1
- **What it measures**: Neural translation quality (trained on human judgments)
- **Advantage**: Best correlation with human evaluation

### LaBSE (Language-agnostic BERT Sentence Embedding)
- **Library**: `sentence-transformers`
- **Model**: `sentence-transformers/LaBSE`
- **Implementation**: `model.encode()` + cosine similarity
- **Range**: 0-1
- **What it measures**: Language-agnostic sentence embedding similarity
- **Advantage**: Works well across scripts (Latin, CJK, Arabic, etc.)

### COMET-QE (Quality Estimation)
- **Library**: `comet`
- **Model**: `Unbabel/wmt22-cometkiwi-da`
- **Implementation**: `model.predict([{src, mt}])` (reference-free)
- **Range**: -1 to 1
- **What it measures**: Translation quality without reference

## Data Flow

```python
# Simplified data flow for run_medlineplus_pipeline.py

# 1. Load source texts
english_original = load_txt("document_english.txt")
professional_translation = load_txt("document_spanish.txt")  # Human translation

# 2. Step 1: Forward translation (English → Target)
llm_translation = llm.translate(english_original, target_lang="spanish")

# 3. Step 2: Back-translation of LLM output (Target → English)
llm_back_translation = llm.translate(llm_translation, target_lang="english")

# 4. Step 3: Back-translation of Professional (Target → English)
prof_back_translation = llm.translate(professional_translation, target_lang="english")

# 5. Goal 1: LLM back-translation vs Original
goal1_bleu = bleu(llm_back_translation, english_original)
goal1_labse = labse_similarity(llm_back_translation, english_original)

# 6. Goal 2: LLM translation vs Professional (same language)
goal2_bleu = bleu(llm_translation, professional_translation)
goal2_comet = comet(english_original, llm_translation, professional_translation)

# 7. Goal 3: Professional back-translation vs Original
goal3_bleu = bleu(prof_back_translation, english_original)
goal3_labse = labse_similarity(prof_back_translation, english_original)
```

## Models Used for Translation

| Model | API | Temperature | Max Tokens |
|-------|-----|-------------|------------|
| GPT-5.1 | OpenAI | 0.3 | 8192 |
| Claude Opus 4.5 | Anthropic | 0.3 | 8192 |
| Gemini 3 Pro | Google | 0.3 | 8192 |
| Kimi K2 | Moonshot | 0.3 | 8192 |

## Translation Prompt Template

```
Translate the following English text to {language}.

Rules:
1. Preserve all medical terminology accurately
2. Maintain the original formatting and structure
3. Do not add or omit any information
4. Use formal register appropriate for health education materials

Text to translate:
{english_text}
```

## Scale

| Metric | Count |
|--------|-------|
| Documents | 22 (11 VIS + 11 Cancer) |
| Languages | 8 |
| Models | 4 |
| Translation pairs | 704 (22 × 8 × 4) |
| Translation steps per pair | 3 (forward + LLM back + professional back) |
| **Total API calls** | **2,112** |

## Data Extraction Methods

Text was extracted from MedlinePlus documents using multiple methods:

| Method | Use Case | Tool |
|--------|----------|------|
| **DOCX Extraction** | Documents converted to Word format | python-docx |
| **PDF Text Extraction** | Single-column PDFs | pdftotext |
| **PyMuPDF** | Arabic RTL PDFs | fitz (PyMuPDF) |
| **LLM Screenshot** | 2-column PDFs | Vision LLM to maintain structure |

**Note:** Some VIS documents have 2-column layouts. When extracted via pdftotext, columns may interleave. For critical documents, LLM screenshot extraction was used to preserve the reading order.

## Known Limitations

1. **2-Column Layout Artifacts**: Some VIS documents have 2-column layouts that may show interleaved text when extracted via standard pdftotext. This affects readability but the translation evaluation remains valid as both LLM and professional translations work from the same source.

2. **Arabic RTL Handling**: Required special PyMuPDF extraction with word-order handling for proper RTL text ordering.

3. **Metric Sensitivity**:
   - BLEU heavily penalizes valid paraphrases and performs poorly on non-Latin scripts
   - COMET requires GPU for efficient computation
   - BERTScore can be slow for long documents

4. **Truncation**: Very long documents are truncated to 512 tokens for embedding models. Some Gemini responses showed truncation warnings at max_tokens limit.

5. **Reference Bias**: Goal 2 metrics rely on a single professional translation as reference, which may penalize equally valid alternative translations.

6. **Back-translation Limitation**: Back-translation measures round-trip fidelity, not unidirectional quality. A "stable" translation that back-translates well may still contain errors invisible to this methodology.

## Validation Checklist

For NLP review, please verify:

- [ ] **Metric calculations**: Are BLEU/chrF/BERTScore/COMET/LaBSE implementations standard?
- [ ] **Model selection**: Are the embedding models appropriate for this task?
- [ ] **Tokenization**: Is tokenization consistent across comparisons?
- [ ] **Normalization**: Are texts properly normalized before comparison?
- [ ] **Statistical significance**: Are differences between models meaningful?
- [ ] **Goal 3 interpretation**: Is the professional baseline correctly positioned as upper bound?

## Files for Review

| File | Description |
|------|-------------|
| `scripts/calculate_medlineplus_metrics.py` | Main metrics calculation (Goals 1, 2, 3) |
| `scripts/run_medlineplus_pipeline.py` | Translation pipeline (3-step process) |
| `output/medlineplus_metrics/all_metrics.json` | Raw metrics data |
| `output/medlineplus_metrics/summary.json` | Aggregated summaries |
| `output/medlineplus_results/all_results.json` | Full translation data |

## Contact

For questions about the pipeline, please contact the research team.
