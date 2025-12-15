# NLP Pipeline Technical Review

This document provides a technical overview of the back-translation evaluation pipeline for NLP review.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACK-TRANSLATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DATA EXTRACTION                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  PDF Files  │───▶│  pdftotext  │───▶│ .txt Files  │                     │
│  │  (198 docs) │    │  + PyMuPDF  │    │             │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│       Note: Arabic PDFs use PyMuPDF for RTL text handling                  │
│                                                                             │
│  2. TRANSLATION                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  English    │───▶│    LLM      │───▶│   Target    │                     │
│  │  Original   │    │  (4 models) │    │  Language   │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                           │                   │                             │
│                           │                   ▼                             │
│                           │            ┌─────────────┐                     │
│                           │            │ Back-Trans  │                     │
│                           └───────────▶│ to English  │                     │
│                                        └─────────────┘                     │
│                                                                             │
│  3. EVALUATION                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Same-Language Metrics (LLM Translation vs Professional)           │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌─────────┐                 │   │
│  │  │  BLEU   │ │  chrF   │ │ BERTScore │ │  COMET  │                 │   │
│  │  │ sacrebleu│ │sacrebleu│ │bert_score │ │unbabel/ │                 │   │
│  │  └─────────┘ └─────────┘ └───────────┘ │ comet   │                 │   │
│  │                                        └─────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Back-Translation Metrics (English Back-Trans vs Original English) │   │
│  │  ┌───────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐                │   │
│  │  │XLM-RoBERTa│ │  LaBSE  │ │  mBERT  │ │ COMET-QE │                │   │
│  │  │ xlm-roberta│ │sentence │ │ bert-   │ │ unbabel/ │                │   │
│  │  │ -large    │ │ -trans. │ │ base-ml │ │wmt22-qe  │                │   │
│  │  └───────────┘ └─────────┘ └─────────┘ └──────────┘                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `extract_text.py` | Extract text from PDFs | PDF files | Text files |
| `extract_arabic_pymupdf.py` | RTL-aware Arabic extraction | Arabic PDFs | Arabic text |
| `run_medlineplus_translations.py` | Run LLM translations | English text | Translations + back-translations |
| `calculate_medlineplus_metrics.py` | Compute all metrics | Translation results | Metrics JSON |
| `generate_github_outputs.py` | Generate reports/charts | Metrics | Excel, PNG, README |

## Metric Implementations

### Same-Language Metrics

These compare LLM translation output to professional human translation (both in target language).

#### 1. BLEU (Bilingual Evaluation Understudy)
- **Library**: `sacrebleu`
- **Implementation**: `sentence_bleu(hypothesis, [reference])`
- **Range**: 0-100
- **What it measures**: N-gram precision overlap
- **Limitations**: Sensitive to exact word matches; penalizes valid paraphrases

#### 2. chrF (Character n-gram F-score)
- **Library**: `sacrebleu`
- **Implementation**: `CHRF().sentence_score(hypothesis, [reference])`
- **Range**: 0-100
- **What it measures**: Character-level overlap (better for morphologically rich languages)
- **Advantage**: More robust than BLEU for non-Latin scripts

#### 3. BERTScore
- **Library**: `bert_score`
- **Model**: `microsoft/deberta-xlarge-mnli`
- **Implementation**: `score(hypotheses, references, lang='xx')`
- **Range**: 0-1
- **What it measures**: Contextual embedding similarity
- **Advantage**: Captures semantic similarity beyond surface forms

#### 4. COMET (Crosslingual Optimized Metric for Evaluation of Translation)
- **Library**: `comet`
- **Model**: `Unbabel/wmt22-comet-da`
- **Implementation**: `model.predict([{src, mt, ref}])`
- **Range**: 0-1
- **What it measures**: Neural translation quality (trained on human judgments)
- **Advantage**: Best correlation with human evaluation

### Back-Translation Semantic Metrics

These compare the back-translation (English) to the original English source text.

**Important**: Despite using multilingual models, this is an English-to-English comparison. We use multilingual models for robustness, not because the comparison is cross-lingual.

#### 1. XLM-RoBERTa Similarity
- **Library**: `transformers`
- **Model**: `xlm-roberta-large`
- **Implementation**: Mean pooling + cosine similarity
- **Range**: 0-1
- **What it measures**: Cross-lingual semantic similarity

#### 2. LaBSE (Language-agnostic BERT Sentence Embedding)
- **Library**: `sentence-transformers`
- **Model**: `sentence-transformers/LaBSE`
- **Implementation**: `model.encode()` + cosine similarity
- **Range**: 0-1
- **What it measures**: Language-agnostic sentence embedding similarity

#### 3. mBERT (Multilingual BERT)
- **Library**: `transformers`
- **Model**: `bert-base-multilingual-cased`
- **Implementation**: Mean pooling + cosine similarity
- **Range**: 0-1
- **What it measures**: Multilingual contextual similarity

#### 4. COMET-QE (Quality Estimation)
- **Library**: `comet`
- **Model**: `Unbabel/wmt22-cometkiwi-da`
- **Implementation**: `model.predict([{src, mt}])` (reference-free)
- **Range**: -1 to 1
- **What it measures**: Translation quality without reference (QE mode)

## Data Flow

```python
# Simplified data flow

# 1. Load source texts
english_original = load_pdf("document_english.pdf")
professional_translation = load_pdf("document_spanish.pdf")  # Human translation

# 2. LLM translation
llm_translation = llm.translate(english_original, target_lang="spanish")
llm_back_translation = llm.translate(llm_translation, target_lang="english")

# 3. Same-language evaluation (Spanish vs Spanish)
same_lang_bleu = bleu(llm_translation, professional_translation)
same_lang_comet = comet(english_original, llm_translation, professional_translation)

# 4. Back-translation evaluation (English vs English)
backtrans_similarity = xlm_roberta_sim(llm_back_translation, english_original)
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

## Known Limitations

1. **PDF Extraction Quality**: Text extraction from PDFs may introduce artifacts, especially for complex layouts or scanned documents.

2. **Arabic RTL Handling**: Required special PyMuPDF extraction with word-order reversal for proper RTL text ordering.

3. **Metric Sensitivity**:
   - BLEU heavily penalizes valid paraphrases
   - COMET requires GPU for efficient computation
   - BERTScore can be slow for long documents

4. **Truncation**: Very long documents are truncated to 512 tokens for embedding models.

5. **Reference Bias**: Same-language metrics rely on a single professional translation as reference, which may penalize equally valid alternative translations.

## Validation Checklist

For NLP review, please verify:

- [ ] **Metric calculations**: Are BLEU/chrF/BERTScore/COMET implementations standard?
- [ ] **Model selection**: Are the embedding models appropriate for this task?
- [ ] **Tokenization**: Is tokenization consistent across comparisons?
- [ ] **Normalization**: Are texts properly normalized before comparison?
- [ ] **Statistical significance**: Are differences between models meaningful?
- [ ] **Correlation analysis**: Do metrics correlate as expected?

## Files for Review

| File | Description |
|------|-------------|
| `scripts/calculate_medlineplus_metrics.py` | Main metrics calculation |
| `scripts/run_medlineplus_translations.py` | Translation pipeline |
| `output/medlineplus_metrics/all_metrics.json` | Raw metrics data |
| `output/medlineplus_results/all_results.json` | Full translation data |

## Contact

For questions about the pipeline, please contact the research team.
