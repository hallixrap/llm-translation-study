# Evaluating Large Language Model Translation Fidelity for Medical Documents Across High- and Low-Resource Languages

Chukwuebuka Anyaegbuna, MD, Eduardo Juan Perez Guerrero, Jerry Liu, MD, Timothy Keyes, PhD, April Liang, MD, Natasha Steele, MD, MPH, Stephen Ma, MD, Jonathan Chen, MD PhD, Kevin Schulman MD MBA

Stanford University School of Medicine, Stanford CA
Stanford University Technology and Digital Solutions

## Abstract

**Background:** Access to accurate medical information in patients' native languages is critical for compliance with federal mandates. Under Section 1557 of the Affordable Care Act, healthcare entities are legally required to provide meaningful access to patients with limited English proficiency, including the use of qualified translators for critical medical documents. Yet professional medical translation remains costly and limited in availability, particularly for low-resource languages. Large language models (LLMs) offer a potential solution, but their reliability for medical translation across diverse languages remains understudied.

**Objective:** To evaluate whether frontier LLMs can maintain translation fidelity for medical documents across both high-resource and low-resource languages using a back-translation methodology and automated Natural Language Processing (NLP) metrics.

**Methods:** We evaluated four frontier LLMs (GPT-5.1, Claude Opus 4.5, Gemini 3 Pro, and Kimi K2) on 22 professionally-translated medical documents from the CDC's Vaccine Information Statements and American Cancer Society patient education materials. Documents were translated from English into 8 languages spanning high-resource (Spanish, Chinese, Russian, Vietnamese), medium-resource (Korean, Arabic), and low-resource (Tagalog, Haitian Creole) categories based on representation in CommonCrawl training corpora. We employed a two-part evaluation framework: (1) assessing LLM back-translation fidelity, and (2) comparing LLM translations to professional translations. Professional translations were also back-translated through each LLM to validate our methodology.

**Results:** Across 704 translation pairs (22 documents × 8 languages × 4 models), all models achieved high semantic preservation on back-translation (LaBSE > 0.92). Notably, low-resource languages (Tagalog: 0.950, Haitian Creole: 0.955) achieved semantic similarity scores comparable to high-resource languages (Spanish: 0.954). Claude Opus 4.5 demonstrated the highest semantic preservation (LaBSE: 0.987), while Gemini 3 Pro led on lexical metrics (BLEU: 39.4). Professional translations back-translated through LLMs showed similar fidelity patterns (LaBSE: 0.92-0.94), validating back-translation as an evaluation method.

**Conclusions:** Frontier LLMs can reliably preserve medical meaning through translation across diverse languages, including historically underserved low-resource languages. Back-translation provides a valid, scalable methodology for evaluating translation quality without requiring human evaluators for each language pair.

**Keywords:** machine translation, large language models, medical translation, health literacy, back-translation, low-resource languages, health equity

---

## Introduction

### The Medical Translation Gap

Equitable healthcare depends critically on access to medical information in patients' preferred languages. Section 1557 of the Affordable Care Act and the U.S. National Standards for Culturally and Linguistically Appropriate Services (CLAS) mandate that healthcare organizations provide language access services, yet significant gaps persist, particularly for speakers of less common languages.1,2 Professional medical translation is expensive, time-consuming, and often unavailable for low-resource languages, those with limited representation in digital corpora and NLP training data, creating barriers to equitable healthcare access.3

### The Promise and Peril of LLM Translation

Large language models have demonstrated remarkable capabilities in natural language processing, including translation.4 However, medical translation presents unique challenges: terminology must be precise, instructions must be unambiguous, and errors can have life-or-death consequences.5 While large language models (LLMs) offer potential for democratizing medical translation access, their reliability and safety across languages, particularly low-resource languages with limited training data, remains uncertain.

### Automated Metrics for Multilingual Evaluation

Evaluating translation quality traditionally requires bilingual human experts for each language pair, limiting scalability across multiple languages. Recent advances in multilingual Natural Language Processing (NLP) have produced automated metrics, including neural embedding-based measures (LaBSE, COMET, BERTScore) that capture semantic similarity across languages.6-8 These metrics enable large-scale evaluation without requiring human evaluators for each language pair, making them particularly valuable for assessing translation quality in low-resource languages where expert evaluators are scarce.

This study leverages these automated multilingual metrics to evaluate LLM translation quality across eight languages, including low-resource languages historically underserved by both professional translation services and NLP research. We focus specifically on English-to-target-language translation, reflecting the clinical scenario where English-language medical materials must be made accessible to non-English-speaking patients. To evaluate translation fidelity, we utilize two methods: direct comparison against professional human translations and back-translation validation. The latter technique involves translating the text back to its source language to confirm that the original meaning is preserved, a methodology aligned with established frameworks for cross-cultural adaptation.9-13 This dual approach provides multiple ways to assess translation accuracy.

### Study Objectives

This study addresses two primary research questions. We first sought to determine if LLM translations preserve medical meaning across high-resource and low-resource languages, as measured by automated multilingual semantic similarity metrics.

Our second objective was to assess the quality of benchmarking and determine how LLM translations compare to existing professional translations on standardized translation quality metrics.

We hypothesized that frontier LLMs can maintain translation fidelity across both high- and low-resource languages, achieving semantic preservation comparable to professional translation services.

### Methodological Approach

We employ automated multilingual evaluation metrics, including neural embedding-based measures (LaBSE, COMET, BERTScore) that capture semantic similarity across languages, to assess translation quality without requiring bilingual human evaluators for each language pair. These metrics enable scalable evaluation across multiple languages, which is particularly valuable for assessing low-resource languages where expert evaluators are scarce.

As an additional validation layer, we use back-translation (from English to the target language and back) alongside these automated metrics. To validate this approach, we also back-translate existing professional translations through each LLM; high-fidelity scores for these translations confirm that our metrics meaningfully reflect translation quality.

---

## Methods

### Study Design

We conducted a cross-sectional evaluation of four frontier LLMs for medical document translation across eight languages, using a two-goal evaluation framework that included automated metrics and validation against professional translation baselines.

### Document Corpus

We assembled a corpus of 22 medical education documents representing two domains:

**Vaccine Information Statements (n=11):** Standardized documents from the Centers for Disease Control and Prevention (CDC), distributed via Immunize.org,14 covering:
- Hepatitis B, HPV, Influenza (inactivated), MMR, Meningococcal ACWY
- Pneumococcal (PCV and PPSV23), Polio (IPV), Shingles (Zoster)
- Tdap, Varicella

**Patients with Cancer Education Materials (n=11):** Documents from the American Cancer Society15 covering:
- Post-diagnosis guidance (breast, cervical, colorectal, lung, prostate cancer)
- Managing side effects of treatment (chemotherapy, nausea/vomiting management)
- Skin cancer resources (detection, living with, treatment, procedures)

All documents were selected based on the availability of professional translations in all eight target languages, ensuring consistent evaluation across language pairs.

### Languages

We selected eight languages representing diverse linguistic families, scripts, and resource availability:

| Language | Script | Family | Resource Level | CommonCrawl % | U.S. Speakers (millions)16 |
|----------|--------|--------|----------------|---------------|-------------------------|
| Russian | Cyrillic | Slavic | High | 6.48 | 0.9 |
| Chinese (Simplified) | Hanzi | Sino-Tibetan | High | 6.18 | 3.5 |
| Spanish | Latin | Romance | High | 4.41 | 41.8 |
| Vietnamese | Latin (+diacritics) | Austroasiatic | High | 1.08 | 1.6 |
| Korean | Hangul | Koreanic | Medium | 0.80 | 1.1 |
| Arabic | Arabic (RTL) | Semitic | Medium | 0.67 | 1.3 |
| Tagalog | Latin | Austronesian | Low | 0.008 | 1.8 |
| Haitian Creole | Latin | French Creole | Low | 0.003 | 0.9 |

Resource level classification was based on representation in CommonCrawl, a primary training corpus for LLMs.3,17 Following conventions in multilingual LLM evaluation, we classified high-resource languages as >1% of the corpus; medium-resource languages 0.1–1%; low-resource languages <0.1%.

### Models

We evaluated four frontier LLMs representing major AI laboratories:

| Model | Provider | Release |
|-------|----------|---------|
| GPT-5.1 | OpenAI | 2025 |
| Claude Opus 4.5 | Anthropic | 2025 |
| Gemini 3 Pro | Google | 2025 |
| Kimi K2 Thinking | Moonshot AI | 2025 |

All models were accessed via their respective APIs using default parameters for translation tasks.

### Translation Pipeline

For each document-language-model combination, we executed the following pipeline:

1. **Forward Translation:** English source document → Target language (LLM)
2. **Back-Translation:** Target language translation → English (same LLM)
3. **Professional Back-Translation:** Professional target language document → English (same LLM)

Critically, forward translation and back-translation were performed in separate API calls (independent conversations), ensuring that back-translation had no access to the original English source text. This prevents the model from simply reproducing memorized content rather than genuinely translating.

This yielded 704 translation pairs (22 documents × 8 languages × 4 models). The complete translation and evaluation workflow is illustrated in Figure 1.

**Figure 1. LLM Translation and Evaluation Pipeline.** The flowchart illustrates the three parallel evaluation paths: (1) Forward translation and subsequent evaluation, (2) Back-translation of the LLM's output, and (3) Back-translation of a professional translation for method validation.

[Figure 1: Images/LLM Translation and Evaluation Pipeline.png]

### Evaluation Framework

#### Primary Analysis 1: LLM Back-Translation Fidelity

We compared LLM back-translations to original English source documents using:

- **BLEU**18: N-gram precision measuring lexical overlap (0-100 scale)
- **LaBSE**6: Language-agnostic sentence embeddings measuring semantic similarity (0-1 scale, where >0.90 indicates high semantic preservation and differences of 0.05 represent meaningful variation)
- **XLM-RoBERTa**19: Cross-lingual semantic similarity
- **mBERT**20: Multilingual contextual embeddings

#### Primary Analysis 2: LLM vs Professional Translation

We compared LLM translations directly to professional translations (same target language) using:

- **BLEU**: Lexical overlap with professional reference
- **chrF**21: Character n-gram F-score
- **BERTScore**7: Contextual embedding similarity
- **COMET**8: Neural translation quality estimation

#### Methodological Validation: Professional Back-Translation

To validate back-translation as an evaluation methodology, we back-translated existing professional translations through each LLM and compared to original English using the same metrics as Primary Analysis 1. High fidelity scores confirm that back-translation meaningfully reflects translation quality.

### Statistical Analysis

We report means and standard deviations for all metrics. Model comparisons use the Kruskal-Wallis test with Dunn's post-hoc correction.22 Language comparisons stratify by resource level. Statistical significance was set at p < 0.05, with p < 0.01 and p < 0.001 denoted where applicable. All analyses were conducted in Python 3.11 using SciPy (v1.13.1) and statsmodels (v0.14.1).

### Ethical Considerations

This study used only publicly available documents, did not involve human subjects, and is exempt from IRB review. All source materials are freely distributed for public health education.

---

## Results

### Methodological Validation

As hypothesized, back-translation of professional translations yielded high fidelity with the original English text (LaBSE: 0.92-0.94; Supplementary Table S2), providing a benchmark of professional translation performance against which to contextualize LLM performance.

### Overall Translation Volume

We completed 702 of 704 translation pairs (99.7%) across all document-language-model combinations. Two Kimi K2 translations failed due to content filtering restrictions.

### Primary Analysis 1: LLM Back-Translation Fidelity

All models achieved high semantic preservation through round-trip translation (Table 1).

**Table 1. Back-Translation Fidelity by Model**

| Model | n | LaBSE (Mean ± SD) | BLEU (Mean ± SD) |
|-------|---|-------------------|------------------|
| Claude Opus 4.5 | 176 | 0.987 ± 0.013 | 68.7 ± 8.3 |
| GPT-5.1 | 176 | 0.957 ± 0.045 | 64.3 ± 7.4 |
| Kimi K2 Thinking | 174 | 0.940 ± 0.053 | 54.9 ± 8.7 |
| Gemini 3 Pro | 176 | 0.921 ± 0.065 | 61.5 ± 9.3 |

Kruskal-Wallis testing revealed significant differences between models for both LaBSE (H = 156.67, p < 0.001) and BLEU (H = 170.69, p < 0.001). Dunn's post-hoc tests with Bonferroni correction showed Claude Opus 4.5 significantly outperformed all other models on semantic preservation (all pairwise p < 0.001). GPT-5.1 significantly outperformed Kimi K2 (p = 0.003) and Gemini 3 Pro (p < 0.001), while Gemini 3 Pro and Kimi K2 showed no significant difference (p = 1.0).

**Table 1b. Post-hoc Pairwise Comparisons for LaBSE (Dunn's test, Bonferroni-corrected)**

| | Claude Opus 4.5 | GPT-5.1 | Gemini 3 Pro | Kimi K2 |
|---|---|---|---|---|
| Claude Opus 4.5 | — | <0.001 | <0.001 | <0.001 |
| GPT-5.1 | | — | <0.001 | 0.003 |
| Gemini 3 Pro | | | — | 1.0 |
| Kimi K2 | | | | — |


### Primary Analysis 2: LLM vs Professional Translation Quality

LLM translations approached professional quality across all models (Table 2). Note that different metrics are reported for this analysis compared to Table 1: here we use reference-based metrics (COMET, BERTScore) designed for comparing translations against a gold-standard reference, whereas Table 1 uses metrics optimized for cross-lingual semantic similarity in back-translation evaluation.

**Table 2. LLM Translation Quality Compared to Professional Reference**

| Model | n | BLEU (Mean ± SD) | BERTScore (Mean ± SD) | COMET (Mean ± SD) |
|-------|---|------------------|----------------------|-------------------|
| Gemini 3 Pro | 176 | 39.4 ± 14.9 | 0.845 ± 0.060 | 0.876 ± 0.054 |
| Claude Opus 4.5 | 176 | 37.3 ± 14.4 | 0.859 ± 0.043 | 0.874 ± 0.054 |
| GPT-5.1 | 176 | 36.0 ± 13.8 | 0.844 ± 0.052 | 0.871 ± 0.052 |
| Kimi K2 | 174 | 36.0 ± 14.3 | 0.840 ± 0.052 | 0.872 ± 0.052 |

**Statistical Comparisons (Kruskal-Wallis):**
- COMET: H = 2.07, p = 0.56 (no significant difference)
- BLEU: H = 5.50, p = 0.14 (no significant difference)
- BERTScore: H = 13.58, p = 0.004 (significant)

The lack of significant differences for COMET and BLEU suggests convergence in frontier LLM translation capabilities. BERTScore showed a significant effect, with post-hoc tests revealing Claude Opus 4.5 significantly outperformed GPT-5.1 (p = 0.04) and Kimi K2 (p = 0.004) on contextual semantic similarity, while no other pairwise comparisons reached significance.

### Language Performance: High vs Low Resource

Table 3 and Figure 2 present translation fidelity by language, while Table 4 provides the statistical comparison between resource groups. Back-translation LaBSE measures semantic preservation (meaning); vs Professional BLEU measures lexical overlap with human translators (word choice).

**Figure 2. Semantic vs Lexical Fidelity by Language Resource Level.** Panel A shows that all languages achieve comparable semantic fidelity (LaBSE 0.937-0.976), with low-resource languages (orange) indistinguishable from high-resource languages (blue). Panel B shows that lexical overlap with professional translations varies by linguistic factors rather than resource level.

[Figure 2: Images/semantic_vs_lexical_fidelity.png]

**Table 3. Translation Fidelity by Language and Resource Level**

| Language | Resource | Back-Translation LaBSE | vs Professional BLEU |
|----------|----------|------------------------|---------------------|
| Spanish | High | 0.954 | 54.3 |
| Vietnamese | High | 0.953 | 50.1 |
| Tagalog | Low | 0.950 | 43.8 |
| Haitian Creole | Low | 0.955 | 37.2 |
| Arabic | Medium | 0.976 | 41.6 |
| Russian | High | 0.945 | 33.4 |
| Korean | Medium | 0.937 | 21.7 |
| Chinese | High | 0.942 | 15.5 |

Low-resource languages (Tagalog, Haitian Creole) achieved back-translation LaBSE scores of 0.950 and 0.955, respectively, comparable to high-resource languages like Spanish (0.954) and Russian (0.945). BLEU scores were lower for low-resource languages than for Spanish.

**Table 4. High-Resource vs Low-Resource Language Comparison (Mann-Whitney U)**

| Metric | High-Resource (Mean) | Low-Resource (Mean) | Difference | p-value |
|--------|---------------------|--------------------|-----------:|---------|
| Back-translation LaBSE | 0.948 | 0.952 | +0.004 | 0.066 |
| Back-translation BLEU | 61.7 | 65.3 | +3.5 | <0.001 |
| vs Professional COMET | 0.879 | 0.837 | -0.042 | <0.001 |
| vs Professional BERTScore | 0.851 | 0.834 | -0.017 | <0.001 |

Low-resource languages achieved comparable semantic preservation scores to high-resource languages (LaBSE: p = 0.066, no significant difference). However, high-resource languages showed better alignment with professional translations (COMET: p < 0.001). The counterintuitive strength of low-resource language performance warranted investigation for potential training data contamination (see Limitations).

BLEU scores varied substantially by language (range: 15.5-54.3), reflecting differences in morphology, syntax, and script. However, semantic similarity metrics (LaBSE) remained consistently high across all languages (range: 0.937-0.976), indicating that LLMs preserve meaning even when surface-level word choices differ from professional translations.

Cancer education materials achieved higher back-translation fidelity (mean LaBSE: 0.984) than Vaccine Information Statements (mean LaBSE: 0.919), with this difference reaching statistical significance (Mann-Whitney U, p < 0.001).

---

## Discussion

This study demonstrates that frontier LLMs can reliably preserve medical meaning through translation across diverse languages, including low-resource languages historically underserved by NLP technologies. Three key findings emerge:

First, low-resource languages achieve translation fidelity comparable to high-resource languages. Tagalog and Haitian Creole, languages with limited NLP resources and training data, achieved semantic similarity scores on par with Spanish and Vietnamese (LaBSE: 0.950-0.955 vs 0.953-0.954). Mann-Whitney U tests confirmed no significant difference in LaBSE scores between low-resource and high-resource languages (p = 0.066). This finding contrasts with earlier evaluations of LLMs that demonstrated significant performance gaps for low-resource languages,3 suggesting that frontier models released in 2025 may have substantially improved their multilingual capabilities. This indicates that current LLMs preserve medical meaning equally well regardless of the amount of training data available for a language.

However, lexical overlap with professional translations (BLEU) was lower for low-resource languages. This means that while LLMs accurately convey the information, they may phrase things differently than a human translator would, i.e. using different vocabulary or sentence structures. The likely explanation is that professional translation conventions are more established for high-resource languages like Spanish and Chinese, giving LLMs more examples to learn from during training.

LLMs can reliably convey medical information to Tagalog and Haitian Creole speakers with meaning preservation comparable to Spanish. However, the phrasing may sound less natural than a professional human translation. This distinction matters in lower resource settings or for urgent dissemination of health information where professional translators are unavailable, LLM translation can effectively communicate the core message. For polished, publication-ready materials, professional human translation remains preferable.

Second, automated multilingual metrics enable scalable evaluation across diverse languages. By employing neural embedding-based metrics (LaBSE, COMET, BERTScore) alongside traditional lexical metrics (BLEU, chrF), we evaluated translation quality across eight languages without requiring bilingual human evaluators for each pair. Professional translations maintained high fidelity through back-translation (LaBSE: 0.92-0.94), validating our automated evaluation approach. Critically, these metrics enabled rigorous comparison across languages where finding qualified human evaluators would be challenging or impossible.

Third, semantic preservation is more consistent than lexical overlap. While BLEU scores varied widely by language (range: 15.5-54.3, reflecting morphological and syntactic differences), semantic metrics remained consistently high across all languages (LaBSE range: 0.937-0.976). This finding validates the importance of using multilingual embedding-based metrics rather than relying solely on n-gram overlap for evaluating translation quality across typologically diverse languages.

These findings have significant implications for the delivery of equitable health care at scale. Medical translation services are often unavailable or delayed for speakers of less common languages, creating barriers to informed healthcare decision-making. If LLMs can reliably translate medical content for low-resource languages, they could democratize access to health information for underserved populations.

However, we emphasize that LLM translation should complement, not replace, professional medical translation for high-stakes clinical documents. Our results suggest LLMs may be appropriate for patient education materials where the goal is general comprehension rather than legal or regulatory compliance.

All four frontier models performed within a narrow band on translation quality metrics, suggesting that model selection is less critical than language pair selection for medical translation. This convergence may reflect shared training approaches, similar underlying architectures, or saturation of translation capabilities at the frontier.

Claude Opus 4.5 achieved the highest semantic preservation through back-translation, while Gemini 3 Pro led on lexical agreement with professional translations. These complementary strengths suggest potential for ensemble approaches in production systems.

### Limitations

Several limitations warrant consideration:

**Training data contamination.** The medical documents evaluated in this study (CDC Vaccine Information Statements, American Cancer Society patient education materials) are publicly available resources that may be present in the training corpora of the evaluated LLMs. This potential data contamination could artificially inflate translation performance metrics if models have memorized specific document content rather than developing generalizable translation capabilities. The comparable performance of low-resource languages (Tagalog, Haitian Creole) compared to high-resource languages raised concern about this possibility.

To address this concern, we conducted a comprehensive sentence-reordering sensitivity analysis (n=240 translation pairs; Supplementary Analysis S1). We randomly shuffled sentence order within 10 documents and repeated the translation pipeline across all 4 models and 3 representative languages (Spanish, Chinese Simplified, Tagalog). The hypothesis was that memorized documents would show significant performance degradation when sentence structure was disrupted, whereas true translation capability should preserve semantic similarity regardless of sentence order.

Results showed no significant performance change in 10 of 12 model-language combinations (83%), with mean differences typically <1%. Two comparisons reached statistical significance: Claude Opus 4.5 with Tagalog showed a 6.0% decrease (p=0.041), while Gemini 3 Pro with Tagalog showed a 3.0% increase (p=0.026). The latter finding, improved performance with shuffled text, is opposite to what memorization would predict, suggesting these isolated significant results likely reflect normal statistical variation across multiple comparisons rather than systematic memorization effects.

These findings suggest our results primarily reflect translation capability rather than document memorization. However, we cannot completely exclude the possibility that models learned general medical translation patterns from similar documents during training, which could still provide an advantage over the translation of completely novel medical content.

**Lexical borrowing in low-resource languages.** The strong back-translation performance of low-resource languages (Tagalog, Haitian Creole) may partly reflect patterns of lexical borrowing from English. Medical Tagalog frequently retains English terminology (e.g., "chemotherapy," "diabetes," "vaccine"), as do many post-colonial languages in technical domains. Similarly, Haitian Creole incorporates substantial French and English vocabulary in medical contexts. This lexical overlap could inflate back-translation fidelity scores compared to languages like Chinese or Russian that use entirely distinct native medical terminology. Future work should examine whether translation performance varies systematically between borrowed versus native terminology within the same language.

**Automated metrics only.** While we employed multiple validated metrics, automated evaluation cannot fully capture nuances of medical terminology, cultural appropriateness, or potential for patient misunderstanding. Future work should incorporate human evaluation for a subset of translations.

**Limited document types.** Our corpus included patient education materials only. Results may not generalize to clinical notes, consent forms, or other medical document types with different linguistic characteristics.

**Single translation direction.** We evaluated English-to-target translation only. Target-to-English translation (relevant for patient-provider communication) may show different patterns.

**Snapshot evaluation.** LLM capabilities evolve rapidly. Our results reflect model versions available in late 2025 and may not reflect future or past capabilities.

**Back-translation through same model.** Using the same LLM for forward and back translation may inflate fidelity scores if the model exhibits consistent translation biases. Future work could employ different models for each direction.

### Future Directions

Several extensions of this work warrant further investigation. First, bilingual expert review should be incorporated for a stratified subset of translations to assess the accuracy of medical terminology and identify errors with plausible potential for patient harm. Second, evaluation should be broadened beyond the current materials to include additional clinical document types, such as clinician notes, medication instructions, and informed consent forms. Third, given the rapid evolution of large language models, longitudinal assessment is needed to track translation performance over time as underlying models and deployment configurations are updated. Fourth, future studies should examine the impact of prompt design, including whether specialized medical translation prompts measurably improve fidelity and reduce clinically meaningful errors. Finally, ensemble approaches should be tested to determine whether combining outputs from multiple models or multiple candidate translations yields more reliable, higher-quality translations than any single model alone.

---

## Conclusion

Frontier large language models can reliably preserve medical meaning through translation across both high-resource and low-resource languages. Back-translation provides a valid, scalable methodology for evaluating translation quality. Low-resource languages achieve semantic preservation comparable to high-resource languages, suggesting LLMs could extend medical translation access to historically underserved populations.

These findings support cautious optimism about LLM medical translation, while underscoring the continued importance of professional translation for high-stakes clinical applications. As LLM capabilities continue to evolve, ongoing evaluation will be essential to ensure safe and equitable deployment in healthcare settings.

---

## References

1. Department of Health and Human Services. Nondiscrimination in Health Programs and Activities. Fed Regist. 2024;89(88):37522-37703.

2. Office of Minority Health. National Standards for Culturally and Linguistically Appropriate Services (CLAS) in Health and Health Care. U.S. Department of Health and Human Services; 2013.

3. Lai VD, Ngo NT, Pouran Ben Veyseh A, et al. ChatGPT beyond English: towards a comprehensive evaluation of large language models in multilingual learning. Findings of the Association for Computational Linguistics: EMNLP 2023. Singapore: Association for Computational Linguistics; 2023:13171-99.

4. Brown T, Mann B, Ryder N, et al. Language models are few-shot learners. Advances in Neural Information Processing Systems. 2020;33:1877-1901.

5. Quan K, Lynch J. The High Costs of Language Barriers in Medical Malpractice. National Health Law Program; 2010. Accessed January 25, 2026. https://healthlaw.org/wp-content/uploads/2018/09/Language-Access-and-Malpractice.pdf

6. Feng F, Yang Y, Cer D, et al. Language-agnostic BERT sentence embedding. Proceedings of ACL. 2022:878-891.

7. Zhang T, Kishore V, Wu F, Weinberger KQ, Artzi Y. BERTScore: Evaluating text generation with BERT. Proceedings of ICLR. 2020.

8. Rei R, Stewart C, Farinha AC, Lavie A. COMET: A neural framework for MT evaluation. Proceedings of EMNLP. 2020:2685-2702.

9. Brislin RW. Back-translation for cross-cultural research. Journal of Cross-Cultural Psychology. 1970;1(3):185-216.

10. Tyupa S. A theoretical framework for back-translation as a quality assessment tool. New Voices in Translation Studies. 2011;7(1):35-46.

11. Wild D, Grove A, Martin M, et al. Principles of Good Practice for the Translation and Cultural Adaptation Process for Patient-Reported Outcomes (PRO) Measures: Report of the ISPOR Task Force for Translation and Cultural Adaptation. Value Health. 2005;8(2):94-104.

12. Beaton DE, Bombardier C, Guillemin F, Ferraz MB. Guidelines for the process of cross-cultural adaptation of self-report measures. Spine. 2000;25(24):3186-3191.

13. Cruchinho P, López-Franco MD, Capelas ML, et al. Translation, Cross-Cultural Adaptation, and Validation of Measurement Instruments: A Practical Guideline for Novice Researchers. J Multidiscip Healthc. 2024;17:2701–2728.

14. Immunize.org. Vaccine Information Statements (VIS). https://www.immunize.org/vis/. Accessed December 20, 2025.

15. American Cancer Society. Cancer Information. https://www.cancer.org/cancer.html. Accessed December 20, 2025.

16. Dietrich S, Hernandez E. Language Use in the United States: 2019. U.S. Census Bureau; 2022. American Community Survey Reports, ACS-50. Accessed January 25, 2026. https://www.census.gov/content/dam/Census/library/publications/2022/acs/acs-50.pdf

17. Common Crawl. Statistics of Common Crawl Monthly Archives: Languages. https://commoncrawl.github.io/cc-crawl-statistics/plots/languages.html. Accessed December 20, 2025.

18. Papineni K, Roukos S, Ward T, Zhu WJ. BLEU: a method for automatic evaluation of machine translation. Proceedings of ACL. 2002:311-318.

19. Conneau A, Khandelwal K, Goyal N, et al. Unsupervised cross-lingual representation learning at scale. Proceedings of ACL. 2020:8440-8451.

20. Devlin J, Chang MW, Lee K, Toutanova K. BERT: Pre-training of deep bidirectional transformers for language understanding. Proceedings of NAACL. 2019:4171-4186.

21. Popović M. chrF: character n-gram F-score for automatic MT evaluation. Proceedings of WMT. 2015:392-395.

22. Dunn OJ. Multiple comparisons using rank sums. Technometrics. 1964;6(3):241-252.

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

### Supplementary Analysis S1: Sentence Reordering Sensitivity Analysis

To address concerns about training data contamination, we conducted a sensitivity analysis testing whether LLM performance reflects document memorization versus true translation capability.

**Methods:** We randomly shuffled sentence order in 10 documents (5 immunization, 5 cancer) and compared translation performance between original and shuffled conditions across all 4 models (GPT-5.1, Claude Opus 4.5, Gemini 3 Pro, Kimi K2) and 3 languages representing high-resource (Spanish), high-resource non-Latin script (Chinese Simplified), and low-resource (Tagalog) categories. This yielded 240 translation pairs (10 documents × 4 models × 3 languages × 2 conditions).

**Hypothesis:** If models memorized documents, shuffling sentences should significantly degrade performance (semantic similarity drops). If models are truly translating, semantic similarity should remain stable regardless of sentence order.

**Results:**

**Table S1.1: Sentence Reordering Sensitivity Analysis - LaBSE Semantic Similarity**

| Model | Language | Original (Mean ± SD) | Shuffled (Mean ± SD) | Δ Change | p-value | Result |
|-------|----------|---------------------|---------------------|----------|---------|--------|
| GPT-5.1 | Spanish | 0.991 ± 0.004 | 0.992 ± 0.007 | +0.1% | 0.740 | No change |
| GPT-5.1 | Chinese | 0.983 ± 0.007 | 0.985 ± 0.005 | +0.2% | 0.585 | No change |
| GPT-5.1 | Tagalog | 0.991 ± 0.004 | 0.989 ± 0.007 | -0.2% | 0.429 | No change |
| Claude Opus 4.5 | Spanish | 0.994 ± 0.006 | 0.958 ± 0.058 | -3.6% | 0.082 | No change |
| Claude Opus 4.5 | Chinese | 0.989 ± 0.006 | 0.944 ± 0.073 | -4.6% | 0.078 | No change |
| Claude Opus 4.5 | Tagalog | 0.997 ± 0.001 | 0.937 ± 0.078 | -6.0% | 0.041* | Significant |
| Gemini 3 Pro | Spanish | 0.980 ± 0.023 | 0.990 ± 0.013 | +1.0% | 0.140 | No change |
| Gemini 3 Pro | Chinese | 0.957 ± 0.033 | 0.978 ± 0.024 | +2.2% | 0.196 | No change |
| Gemini 3 Pro | Tagalog | 0.957 ± 0.032 | 0.986 ± 0.015 | +3.0% | 0.026* | Significant† |
| Kimi K2 | Spanish | 0.981 ± 0.022 | 0.950 ± 0.087 | -3.1% | 0.284 | No change |
| Kimi K2 | Chinese | 0.978 ± 0.021 | 0.980 ± 0.008 | +0.2% | 0.794 | No change |
| Kimi K2 | Tagalog | 0.976 ± 0.045 | 0.981 ± 0.013 | +0.5% | 0.752 | No change |

*Paired t-tests, n=10 document pairs per cell. p < 0.05 †Note: Gemini 3 Pro showed significant improvement with shuffled text, opposite to memorization hypothesis.

**Summary:** Of 12 model-language combinations tested:
- 10/12 (83%): No significant difference between original and shuffled conditions
- 1/12: Claude Opus 4.5 + Tagalog showed 6% decrease (p=0.041), potentially consistent with some memorization
- 1/12: Gemini 3 Pro + Tagalog showed 3% increase (p=0.026), inconsistent with memorization

**Metric Sensitivity Validation (Negative Control):** To confirm that LaBSE is sensitive to sentence reordering, we directly compared original documents to their shuffled versions without any translation. This establishes the expected similarity score if a model were to memorize and reproduce the original document structure when given shuffled input.

**Table S1.2: Direct Original vs Shuffled Document Similarity (No Translation)**

| Document | LaBSE (Original vs Shuffled) |
|----------|------------------------------|
| immunize/polio_ipv | 0.800 |
| immunize/varicella | 0.779 |
| immunize/zoster_recombinant | 0.732 |
| immunize/meningococcal_acwy | 0.773 |
| immunize/hpv | 0.876 |
| cancer/after-a-breast-cancer-diagnosis | 0.759 |
| cancer/skin-cancer-treatments | 0.874 |
| cancer/checking-your-skin | 0.843 |
| cancer/skin-cancer-tests-and-procedures | 0.874 |
| cancer/after-a-colorectal-cancer-diagnosis | 0.818 |
| **Mean ± SD** | **0.813 ± 0.050** |

Sentence shuffling reduces LaBSE similarity from 1.0 to 0.81 on average (range: 0.73–0.88), representing a 19% decrease. This confirms that LaBSE is sensitive to structural changes in document organization. Critically, back-translations from both original and shuffled conditions achieved scores of ~0.95, well above the 0.81 baseline. If models had memorized original documents and "unscrambled" shuffled input during translation, we would expect shuffled back-translations to score around 0.81 (matching the shuffled structure) rather than 0.95. The equivalent high scores for both conditions indicate that models preserve semantic content through translation rather than recalling memorized text structures.

**Conclusion:** The predominant finding across 240 translations is that sentence reordering does not significantly affect translation quality, providing evidence against widespread document memorization. The isolated significant results (2/12 comparisons) likely reflect normal statistical variation given multiple comparisons, particularly since one showed improvement rather than the degradation expected from memorization. These findings support the validity of our main results.

[Full results available in repository: output/sensitivity_analysis/]

### Supplementary Table S2: Professional Translation Back-Translation Fidelity

To validate back-translation as an evaluation methodology, we back-translated existing professional human translations through each LLM and compared the results to the original English source text. High fidelity scores for professional translations confirm that our automated metrics meaningfully reflect translation quality and that back-translation does not introduce systematic distortion.

| Model | BLEU | BERTScore | LaBSE |
|-------|------|-----------|-------|
| GPT-5.1 | 55.8 | 0.919 | 0.940 |
| Claude Opus 4.5 | 54.7 | 0.924 | 0.942 |
| Gemini 3 Pro | 48.3 | 0.913 | 0.928 |
| Kimi K2 | 43.9 | 0.912 | 0.934 |

All models achieved LaBSE scores of 0.92-0.94 when back-translating professional translations, indicating that the back-translation process reliably preserves meaning. These scores provide a benchmark against which to contextualize LLM translation performance.

### Supplementary Table S3: Complete Metrics by Model and Language

[Available in Excel report: medlineplus_backtranslation_report.xlsx]
