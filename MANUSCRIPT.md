# Evaluating Large Language Model Translation Fidelity for Medical Documents Across High- and Low-Resource Languages: A Back-Translation Study

## Abstract

**Background:** Access to accurate medical information in patients' native languages is critical for health equity, yet professional medical translation remains costly and limited in availability, particularly for low-resource languages. Large language models (LLMs) offer a potential solution, but their reliability for medical translation across diverse languages remains understudied.

**Objective:** To evaluate whether frontier LLMs can maintain translation fidelity for medical documents across both high-resource and low-resource languages using back-translation methodology.

**Methods:** We evaluated four frontier LLMs (GPT-5.1, Claude Opus 4.5, Gemini 3 Pro, and Kimi K2) on 22 professionally-translated medical documents from CDC Vaccine Information Statements and American Cancer Society patient education materials. Documents were translated from English into 8 languages spanning high-resource (Spanish, Chinese, Russian, Korean), medium-resource (Vietnamese, Arabic), and low-resource (Tagalog, Haitian Creole) categories. We employed a three-goal evaluation framework: (1) assessing LLM back-translation fidelity, (2) comparing LLM translations to professional translations, and (3) validating back-translation as an evaluation methodology using professional translations as baseline.

**Results:** Across 704 translation pairs, all models achieved high semantic preservation on back-translation (LaBSE > 0.92). Notably, low-resource languages (Tagalog: 0.950, Haitian Creole: 0.955) achieved semantic similarity scores comparable to high-resource languages (Spanish: 0.954). Claude Opus 4.5 demonstrated the highest semantic preservation (LaBSE: 0.987), while Gemini 3 Pro led on lexical metrics (BLEU: 39.4). Professional translations back-translated through LLMs showed similar fidelity patterns (LaBSE: 0.92-0.94), validating back-translation as an evaluation method.

**Conclusions:** Frontier LLMs can reliably preserve medical meaning through translation across diverse languages, including historically underserved low-resource languages. Back-translation provides a valid, scalable methodology for evaluating translation quality without requiring human evaluators for each language pair.

**Keywords:** machine translation, large language models, medical translation, health literacy, back-translation, low-resource languages, health equity

---

## Introduction

### The Medical Translation Gap

Health literacy depends critically on access to medical information in patients' native languages. The U.S. National Standards for Culturally and Linguistically Appropriate Services (CLAS) mandate that healthcare organizations provide language access services, yet significant gaps persist, particularly for speakers of less common languages [1]. Professional medical translation is expensive, time-consuming, and often unavailable for low-resource languages, creating barriers to equitable healthcare access.

### The Promise and Peril of LLM Translation

Large language models have demonstrated remarkable capabilities in natural language processing, including translation [2]. However, medical translation presents unique challenges: terminology must be precise, instructions must be unambiguous, and errors can have life-or-death consequences. While LLMs offer potential for democratizing medical translation access, their reliability across languages—particularly low-resource languages with limited training data—remains uncertain.

### Back-Translation as Evaluation Methodology

Evaluating translation quality traditionally requires bilingual human experts for each language pair, limiting scalability. Back-translation—translating text from the source language to a target language and back—offers an alternative approach: if meaning is preserved through the round-trip, the translation likely maintains fidelity [3]. This methodology enables evaluation across many languages using only English-language assessment.

### Study Objectives

This study addresses three interconnected research questions:

1. **Fidelity Assessment:** Do LLM translations preserve medical meaning through back-translation?
2. **Professional Comparison:** How do LLM translations compare to existing professional translations?
3. **Methodology Validation:** Is back-translation a valid approach for evaluating translation quality?

We hypothesize that frontier LLMs can maintain translation fidelity across both high- and low-resource languages, and that back-translation provides a valid evaluation methodology as evidenced by consistent performance when applied to professional translations.

---

## Methods

### Study Design

We conducted a cross-sectional evaluation of four frontier LLMs on medical document translation across eight languages, using a three-goal evaluation framework with both automated metrics and validation through professional translation baselines.

### Document Corpus

We assembled a corpus of 22 medical education documents representing two domains:

**Vaccine Information Statements (n=11):** Standardized documents from the Centers for Disease Control and Prevention (CDC), distributed via Immunize.org, covering:
- Hepatitis B, HPV, Influenza (inactivated), MMR, Meningococcal ACWY
- Pneumococcal (PCV and PPSV23), Polio (IPV), Shingles (Zoster)
- Tdap, Varicella

**Cancer Patient Education Materials (n=11):** Documents from the American Cancer Society covering:
- Post-diagnosis guidance (breast, cervical, colorectal, lung, prostate cancer)
- Treatment information (chemotherapy, nausea/vomiting management)
- Skin cancer resources (detection, living with, treatment, procedures)

All documents were selected based on availability of professional translations in all eight target languages, ensuring consistent evaluation across language pairs.

### Languages

We selected eight languages representing diverse linguistic families, scripts, and resource availability:

| Language | Script | Family | Resource Level | U.S. Speakers (millions) |
|----------|--------|--------|----------------|-------------------------|
| Spanish | Latin | Romance | High | 41.8 |
| Chinese (Simplified) | Hanzi | Sino-Tibetan | High | 3.5 |
| Vietnamese | Latin (+diacritics) | Austroasiatic | Medium | 1.6 |
| Russian | Cyrillic | Slavic | High | 0.9 |
| Arabic | Arabic (RTL) | Semitic | Medium | 1.3 |
| Korean | Hangul | Koreanic | High | 1.1 |
| Tagalog | Latin | Austronesian | Low | 1.8 |
| Haitian Creole | Latin | French Creole | Low | 0.9 |

Resource level classification was based on availability of NLP resources, parallel corpora, and representation in LLM training data, following established taxonomies [4].

### Models

We evaluated four frontier LLMs representing major AI laboratories:

| Model | Provider | Release |
|-------|----------|---------|
| GPT-5.1 | OpenAI | 2025 |
| Claude Opus 4.5 | Anthropic | 2025 |
| Gemini 3 Pro | Google | 2025 |
| Kimi K2 | Moonshot AI | 2025 |

All models were accessed via their respective APIs using default parameters for translation tasks.

### Translation Pipeline

For each document-language-model combination, we executed the following pipeline:

1. **Forward Translation:** English source document → Target language (LLM)
2. **Back-Translation:** Target language translation → English (same LLM)
3. **Professional Back-Translation:** Professional target language document → English (same LLM)

This yielded 704 translation pairs (22 documents × 8 languages × 4 models).

### Evaluation Framework

#### Goal 1: LLM Back-Translation Fidelity

We compared LLM back-translations to original English source documents using:

- **BLEU** [5]: N-gram precision measuring lexical overlap
- **LaBSE** [6]: Language-agnostic sentence embeddings measuring semantic similarity
- **XLM-RoBERTa** [7]: Cross-lingual semantic similarity
- **mBERT** [8]: Multilingual contextual embeddings

#### Goal 2: LLM vs Professional Translation

We compared LLM translations directly to professional translations (same target language) using:

- **BLEU**: Lexical overlap with professional reference
- **chrF** [9]: Character n-gram F-score
- **BERTScore** [10]: Contextual embedding similarity
- **COMET** [11]: Neural translation quality estimation

#### Goal 3: Back-Translation Validation

We back-translated professional translations through each LLM and compared to original English, using the same metrics as Goal 1. High fidelity scores validate back-translation as an evaluation methodology.

### Statistical Analysis

We report means and standard deviations for all metrics. Model comparisons use the Kruskal-Wallis test with Dunn's post-hoc correction. Language comparisons stratify by resource level. All analyses were conducted in Python 3.11 using SciPy and statsmodels.

### Ethical Considerations

This study used only publicly available documents and did not involve human subjects. All source materials are freely distributed for public health education.

---

## Results

### Overall Translation Volume

We successfully completed 704 translation pairs across all document-language-model combinations, with no failures or API errors.

### Goal 1: LLM Back-Translation Fidelity

All models achieved high semantic preservation through round-trip translation (Table 1).

**Table 1. Back-Translation Fidelity by Model (Goal 1)**

| Model | BLEU | LaBSE | XLM-RoBERTa | mBERT |
|-------|------|-------|-------------|-------|
| Claude Opus 4.5 | 68.6 | **0.987** | **0.983** | **0.966** |
| GPT-5.1 | 64.3 | 0.957 | 0.963 | 0.948 |
| Gemini 3 Pro | 61.5 | 0.921 | 0.935 | 0.908 |
| Kimi K2 | 54.9 | 0.940 | 0.939 | 0.907 |

Claude Opus 4.5 achieved significantly higher semantic preservation scores (LaBSE: 0.987) compared to other models (p < 0.001), indicating superior meaning retention through the translation round-trip.

### Goal 2: LLM vs Professional Translation Quality

LLM translations approached professional quality across all models (Table 2).

**Table 2. LLM Translation Quality Compared to Professional Reference (Goal 2)**

| Model | BLEU | chrF | BERTScore | COMET |
|-------|------|------|-----------|-------|
| Gemini 3 Pro | **39.4** | **64.6** | 0.845 | **0.876** |
| Claude Opus 4.5 | 37.3 | 63.1 | **0.859** | 0.873 |
| GPT-5.1 | 36.0 | 61.7 | 0.844 | 0.871 |
| Kimi K2 | 36.0 | 61.9 | 0.840 | 0.872 |

All models performed within a narrow band (COMET range: 0.871-0.876), suggesting convergence in frontier LLM translation capabilities. Gemini 3 Pro led on lexical metrics (BLEU, chrF), while Claude Opus 4.5 achieved the highest semantic similarity (BERTScore: 0.859).

### Goal 3: Validation of Back-Translation Methodology

Professional translations back-translated through LLMs maintained high fidelity (Table 3).

**Table 3. Professional Translation Back-Translation Fidelity (Goal 3)**

| Model | BLEU | BERTScore | LaBSE |
|-------|------|-----------|-------|
| GPT-5.1 | **55.8** | 0.919 | **0.940** |
| Claude Opus 4.5 | 54.7 | **0.924** | 0.942 |
| Gemini 3 Pro | 48.3 | 0.913 | 0.928 |
| Kimi K2 | 43.9 | 0.912 | 0.934 |

Professional translations achieved LaBSE scores of 0.92-0.94 through back-translation, confirming that back-translation reliably preserves meaning. This validates our evaluation methodology: if professional translations maintain fidelity through back-translation, then back-translation scores meaningfully reflect translation quality.

### Language Performance: High vs Low Resource

Critically, low-resource languages achieved semantic similarity scores comparable to high-resource languages (Table 4).

**Table 4. Translation Fidelity by Language and Resource Level**

| Language | Resource | G1: LaBSE | G2: BLEU | G3: LaBSE |
|----------|----------|-----------|----------|-----------|
| Spanish | High | 0.954 | **54.3** | 0.942 |
| Vietnamese | Medium | 0.953 | 50.1 | 0.933 |
| **Tagalog** | **Low** | 0.950 | 43.8 | 0.935 |
| **Haitian Creole** | **Low** | **0.955** | 37.2 | 0.934 |
| Arabic | Medium | 0.976 | 41.6 | **0.965** |
| Russian | High | 0.945 | 33.4 | 0.921 |
| Korean | High | 0.937 | 21.7 | 0.929 |
| Chinese | High | 0.942 | 15.5 | 0.930 |

Low-resource languages (Tagalog, Haitian Creole) achieved Goal 1 LaBSE scores of 0.950 and 0.955 respectively—comparable to or exceeding high-resource languages like Spanish (0.954) and Russian (0.945). This suggests frontier LLMs have developed robust multilingual capabilities that extend to traditionally underserved languages.

### Lexical vs Semantic Metrics

BLEU scores varied substantially by language (range: 15.5-54.3), reflecting differences in morphology, syntax, and script. However, semantic similarity metrics (LaBSE) remained consistently high across all languages (range: 0.937-0.976), indicating that LLMs preserve meaning even when surface-level word choices differ from professional translations.

### Document Category Analysis

Vaccine Information Statements and cancer education materials showed similar fidelity patterns, with no significant difference in back-translation scores between categories (p = 0.34).

---

## Discussion

### Principal Findings

This study demonstrates that frontier LLMs can reliably preserve medical meaning through translation across diverse languages, including low-resource languages historically underserved by NLP technologies. Three key findings emerge:

**First, back-translation provides valid quality assessment.** Professional translations maintained high fidelity through back-translation (LaBSE: 0.92-0.94), establishing back-translation as a valid methodology for evaluating translation quality without requiring bilingual human evaluators for each language pair.

**Second, low-resource languages perform comparably to high-resource languages.** Tagalog and Haitian Creole—languages with limited NLP resources and training data—achieved semantic similarity scores on par with Spanish and Vietnamese. This suggests frontier LLMs have developed robust multilingual representations that extend beyond their predominant training languages.

**Third, semantic preservation is more consistent than lexical overlap.** While BLEU scores varied widely by language (reflecting morphological and syntactic differences), semantic metrics remained consistently high. LLMs preserve meaning even when word choices differ from professional translations.

### Implications for Health Equity

These findings have significant implications for health equity. Medical translation services are often unavailable or delayed for speakers of less common languages, creating barriers to informed healthcare decision-making. If LLMs can reliably translate medical content for low-resource languages, they could democratize access to health information for underserved populations.

However, we emphasize that LLM translation should complement—not replace—professional medical translation for high-stakes clinical documents. Our results suggest LLMs may be appropriate for patient education materials where the goal is general comprehension rather than legal or regulatory compliance.

### Model Differentiation

All four frontier models performed within a narrow band on translation quality metrics, suggesting that model selection is less critical than language pair selection for medical translation. This convergence may reflect shared training approaches, similar underlying architectures, or saturation of translation capabilities at the frontier.

Claude Opus 4.5 achieved the highest semantic preservation through back-translation, while Gemini 3 Pro led on lexical agreement with professional translations. These complementary strengths suggest potential for ensemble approaches in production systems.

### Limitations

Several limitations warrant consideration:

**Automated metrics only.** While we employed multiple validated metrics, automated evaluation cannot fully capture nuances of medical terminology, cultural appropriateness, or potential for patient misunderstanding. Future work should incorporate human evaluation for a subset of translations.

**Limited document types.** Our corpus included patient education materials only. Results may not generalize to clinical notes, consent forms, or other medical document types with different linguistic characteristics.

**Single translation direction.** We evaluated English-to-target translation only. Target-to-English translation (relevant for patient-provider communication) may show different patterns.

**Snapshot evaluation.** LLM capabilities evolve rapidly. Our results reflect model versions available in late 2025 and may not reflect future or past capabilities.

**Back-translation through same model.** Using the same LLM for forward and back translation may inflate fidelity scores if the model exhibits consistent translation biases. Future work could employ different models for each direction.

### Future Directions

Several extensions of this work merit investigation:

1. **Human evaluation:** Conduct bilingual expert evaluation for a stratified sample of translations, focusing on medical terminology accuracy and potential for patient harm.

2. **Clinical document types:** Extend evaluation to clinical notes, medication instructions, and consent forms.

3. **Longitudinal tracking:** Monitor LLM translation capabilities over time as models are updated.

4. **Prompt engineering:** Evaluate whether specialized medical translation prompts improve fidelity.

5. **Ensemble methods:** Test whether combining multiple LLM translations improves quality.

---

## Conclusion

Frontier large language models can reliably preserve medical meaning through translation across both high-resource and low-resource languages. Back-translation provides a valid, scalable methodology for evaluating translation quality. Low-resource languages achieve semantic preservation comparable to high-resource languages, suggesting LLMs could extend medical translation access to historically underserved populations.

These findings support cautious optimism about LLM medical translation, while underscoring the continued importance of professional translation for high-stakes clinical applications. As LLM capabilities continue to evolve, ongoing evaluation will be essential to ensure safe and equitable deployment in healthcare settings.

---

## References

1. Office of Minority Health. National Standards for Culturally and Linguistically Appropriate Services (CLAS) in Health and Health Care. U.S. Department of Health and Human Services; 2013.

2. Brown T, Mann B, Ryder N, et al. Language models are few-shot learners. Advances in Neural Information Processing Systems. 2020;33:1877-1901.

3. Brislin RW. Back-translation for cross-cultural research. Journal of Cross-Cultural Psychology. 1970;1(3):185-216.

4. Joshi P, Santy S, Buber A, et al. The state and fate of linguistic diversity and inclusion in the NLP world. Proceedings of ACL. 2020:6282-6293.

5. Papineni K, Roukos S, Ward T, Zhu WJ. BLEU: a method for automatic evaluation of machine translation. Proceedings of ACL. 2002:311-318.

6. Feng F, Yang Y, Cer D, et al. Language-agnostic BERT sentence embedding. Proceedings of ACL. 2022:878-891.

7. Conneau A, Khandelwal K, Goyal N, et al. Unsupervised cross-lingual representation learning at scale. Proceedings of ACL. 2020:8440-8451.

8. Devlin J, Chang MW, Lee K, Toutanova K. BERT: Pre-training of deep bidirectional transformers for language understanding. Proceedings of NAACL. 2019:4171-4186.

9. Popović M. chrF: character n-gram F-score for automatic MT evaluation. Proceedings of WMT. 2015:392-395.

10. Zhang T, Kishore V, Wu F, Weinberger KQ, Artzi Y. BERTScore: Evaluating text generation with BERT. Proceedings of ICLR. 2020.

11. Rei R, Stewart C, Farinha AC, Lavie A. COMET: A neural framework for MT evaluation. Proceedings of EMNLP. 2020:2685-2702.

---

## Acknowledgments

We thank the CDC, Immunize.org, and the American Cancer Society for making professionally-translated health education materials publicly available.

## Author Contributions

[To be completed]

## Funding

[To be completed]

## Conflicts of Interest

The authors declare no conflicts of interest.

## Data Availability

All source documents, extracted text, translation outputs, and evaluation metrics are available at: https://github.com/hallixrap/llm-translation-study

---

## Supplementary Materials

### Supplementary Table S1: Complete Metrics by Model and Language

[Available in Excel report: medlineplus_backtranslation_report.xlsx]

### Supplementary Figure S1: COMET Score Heatmap by Model and Language

[Available in repository: output/github_pages/charts/comet_heatmap.png]

### Supplementary Figure S2: Three-Goal Comparison Across Languages

[Available in repository: output/github_pages/charts/three_goals_comparison.png]
