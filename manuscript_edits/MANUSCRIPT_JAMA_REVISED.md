# Evaluating Large Language Model Translation Fidelity for Medical Documents Across High- and Low-Resource Languages

Chukwuebuka Anyaegbuna, MD, Eduardo J. Perez Guerrero, MD, Jerry Liu, MD, Timothy Keyes, PhD, April S. Liang, MD, Natasha Steele, MD, MPH, Stephen P. Ma, MD, PhD, Jonathan H. Chen, MD, PhD, Kevin Schulman, MD, MBA

Division of Hospital Medicine, Stanford University School of Medicine, Stanford, CA
Stanford University School of Medicine, Stanford, CA
Stanford University Technology and Digital Solutions, Stanford, CA
Division of Computational Medicine, Stanford University School of Medicine, Stanford, CA
Clinical Excellence Research Center, Stanford University School of Medicine, Stanford, CA

**Word Count:** 2982

**Corresponding Author:** Chukwuebuka Anyaegbuna, MD, 3180 Porter Drive, Palo Alto, CA 94304; gozirim@gmail.com; +1 628 309 3402

## Abstract

**Importance:** For the 27.3 million U.S. residents with limited English proficiency (LEP), language barriers create substantial obstacles to accessing medical information and achieving optimal health outcomes. Professional medical translation remains costly and often unavailable, particularly for low-resource languages with limited digital representation.

**Objective:** To evaluate whether frontier large language models (LLMs) maintain translation fidelity for medical documents across high-resource and low-resource languages.

**Design, Setting, and Participants:** Cross-sectional evaluation of four frontier LLMs (GPT-5.1, Claude Opus 4.5, Gemini 3 Pro, Kimi K2) translating 22 professionally-translated medical documents from CDC Vaccine Information Statements and American Cancer Society patient education materials into 8 languages classified by CommonCrawl representation: high-resource (Spanish, Chinese, Russian, Vietnamese), medium-resource (Korean, Arabic), and low-resource (Tagalog, Haitian Creole).

**Main Outcomes and Measures:** Back-translation fidelity assessed using LaBSE (semantic similarity, 0-1 scale) and BLEU (lexical overlap, 0-100 scale), and comparison to professional translations using COMET and BERTScore.

**Results:** Across 704 translation pairs, all models achieved high semantic preservation (LaBSE > 0.92). Low-resource languages achieved semantic similarity comparable to that of high-resource languages (Tagalog: 0.950; Haitian Creole: 0.955 vs. Spanish: 0.954; p = 0.066). Claude Opus 4.5 demonstrated the highest semantic preservation (LaBSE: 0.987). Professional back-translations showed similar fidelity (LaBSE: 0.92-0.94), validating the methodology.

**Conclusions and Relevance:** Frontier LLMs reliably preserve medical meaning across diverse languages, including low-resource languages that have historically been underserved by translation services. These findings suggest LLMs could help address language barriers in healthcare, potentially extending medical translation access to populations for whom professional translation is currently unavailable.

**Keywords:** machine translation, large language models, medical translation, health equity, language access, low-resource languages

## Key Points

**Question:** Do large language models reliably translate medical documents for patients who speak low-resource languages with limited digital representation?

**Findings:** In this cross-sectional evaluation of 704 translations across 8 languages, frontier LLMs preserved medical meaning equally well for low-resource languages (Tagalog, Haitian Creole) as for high-resource languages (Spanish, Chinese), with no significant difference in semantic fidelity (p = 0.066).

**Meaning:** LLMs could help address language barriers in healthcare by providing reliable medical translations for historically underserved language communities, though regulatory frameworks must evolve to recognize these technological advances.

---

## Introduction

Access to medical information is fundamental to patient engagement and health outcomes. Studies encompassing over 74,000 patients have demonstrated that patient education significantly improves physiological, physical, and psychological outcomes while reducing medication use and healthcare utilization.1 Yet for the 27.3 million U.S. residents with limited English proficiency (LEP), language barriers create substantial obstacles to accessing this information.2-4

The consequences are well-documented. Adults with LEP report poorer health outcomes, including lower rates of glycemic control, higher rates of uncontrolled asthma, and increased odds of poorly controlled hypertension.3 They are significantly less likely to utilize outpatient visits and are three times as likely as the English-proficient population to be uninsured.3 Medical errors experienced by LEP individuals are more likely to cause physical harm compared to those experienced by English-proficient patients.4 As the Joint Commission notes in their Roadmap for Hospitals, "effective communication is now accepted as an essential component of quality care and patient safety."5

Federal law recognizes these disparities. Section 1557 of the Affordable Care Act and the National Standards for Culturally and Linguistically Appropriate Services (CLAS) mandate that healthcare organizations provide language access services.6,7 However, manual professional medical translation is costly and resource-intensive and is not always available in a timely or workflow-compatible manner during routine clinical care.8,9 As a result, professional translation is often applied selectively rather than comprehensively, with documented gaps for speakers of less common languages and for written materials generated during rapid clinical processes such as hospital discharge.10

Large language models have demonstrated remarkable capabilities in translation.11 Given their ready accessibility, these technologies could address critical gaps in medical information availability. However, medical translation presents unique challenges: terminology must be precise, instructions unambiguous, and errors can have serious consequences.12 Early evaluations suggest LLM translation quality varies by language: a recent study found ChatGPT and Google Translate performed comparably to professional translation for Spanish and Portuguese discharge instructions but had significantly more clinically significant errors for Haitian Creole.13 The reliability of LLMs across languages, particularly low-resource languages with limited training data, requires systematic evaluation.

Evaluating this technology is an ongoing need given its rapid evolution. Recent survey data show that 57% of U.S. physicians are already using or planning to adopt AI translation services within the next year—a faster adoption rate than any other AI use case surveyed.14 This creates urgency: clinicians are deploying tools with variable performance across languages, yet lack systematic data to guide their use. Physicians and patients require timely data on translation performance to inform patient education strategies. Such evaluations must assess performance across diverse languages, including those that have historically been underserved by both professional translation services and natural language processing research.

Traditional translation evaluation requires a bilingual human expert for each language pair, thereby limiting scalability. Recent advances in multilingual natural language processing (NLP) have produced automated metrics (including LaBSE, COMET, and BERTScore) that capture semantic similarity across languages.15-17 These metrics enable evaluation without requiring human evaluators for each language pair, making them particularly valuable for assessing low-resource languages where expert evaluators are scarce.

This study reports a systematic assessment of LLM translation performance using automated multilingual metrics across eight languages. We focus on English-to-target translation, reflecting clinical scenarios where English-language materials must be made accessible to non-English-speaking patients. We employed back-translation validation (translating text to the target language and back to confirm meaning preservation), a methodology aligned with established cross-cultural adaptation frameworks.18,19

---

## Methods

### Study Objectives

This study addressed three research questions: (1) Do LLM translations preserve medical meaning across high-resource and low-resource languages? (2) Does translation fidelity differ by language resource level? (3) How do LLM translations compare to professional translations?

We hypothesized that current-generation LLMs maintain translation fidelity across both high- and low-resource languages, achieving semantic preservation comparable to professional translation.

### Study Design

We conducted a cross-sectional evaluation of four frontier LLMs for medical document translation across eight languages, using automated metrics and validation against professional translation baselines.

**Models:** GPT-5.1 (OpenAI, 2025), Claude Opus 4.5 (Anthropic, 2025), Gemini 3 Pro (Google, 2025), and Kimi K2 Thinking (Moonshot AI, 2025). All models were accessed via their respective APIs using default parameters.

**Languages:** Russian, Chinese (Simplified), Spanish, Vietnamese, Korean, Arabic, Tagalog, and Haitian Creole, representing diverse linguistic families, scripts, and resource levels.

### Data Sample

We assembled 22 medical education documents from two domains:

**Vaccine Information Statements (n=11):** CDC documents distributed via Immunize.org covering Hepatitis B, HPV, Influenza, MMR, Meningococcal ACWY, Pneumococcal vaccines, Polio, Shingles, Tdap, and Varicella.20

**Cancer Education Materials (n=11):** American Cancer Society documents covering post-diagnosis guidance (breast, cervical, colorectal, lung, prostate cancer), treatment side effects, and skin cancer resources.21

Documents were selected based on the availability of professional translations in all eight target languages.

### Language Classification

Languages were classified by CommonCrawl representation, a primary LLM training corpus:22,23 high-resource (>1%: Spanish, Chinese, Russian, Vietnamese), medium-resource (0.1-1%: Korean, Arabic), and low-resource (<0.1%: Tagalog, Haitian Creole). See Supplementary Table S1 for detailed classification criteria including CommonCrawl percentages and U.S. speaker populations.

### Translation Pipeline

For each document-language-model combination:

1. **Forward Translation:** English → Target language (LLM)
2. **Back-Translation:** Target language → English (same LLM)
3. **Professional Back-Translation:** Professional translation → English (same LLM)

Forward and back translation used separate API calls, ensuring that back translation had no access to the original English text. This yielded 704 translation pairs (22 documents × 8 languages × 4 models).

**[Figure 1 about here]**

### Evaluation Metrics

Translation quality can be assessed through two complementary lenses: *lexical fidelity*, which measures whether the same words and phrases are used, and *semantic fidelity*, which measures whether the meaning is preserved regardless of exact wording. High lexical fidelity implies high semantic fidelity, but the reverse is not true: a translation can preserve meaning while using different vocabulary. For example, "Take medication twice daily" and "Take medicine two times each day" have imperfect lexical overlap but identical meaning. This distinction is particularly important for cross-lingual evaluation, as languages with different scripts or morphological structures (e.g., Chinese, Russian) will inherently show lower lexical overlap even when meaning is fully preserved.

**Methodological Validation:** Back-translating professional translations through each LLM established a benchmark; high fidelity scores confirm that the methodology meaningfully reflects translation quality.

**Back-Translation Fidelity:** We compared back-translations to original English using BLEU (lexical overlap, 0-100 scale; scores above 50 indicate strong word-level agreement),24 LaBSE (semantic similarity, 0-1 scale),15 XLM-RoBERTa,25 and mBERT.26 LaBSE scores >0.90 indicate high semantic preservation; differences of 0.05 represent meaningful variation.

**Comparison to Professional Translation:** We compared LLM translations to professional references using BLEU, chrF,27 BERTScore,16 and COMET.17

### Statistical Analysis

We report means and standard deviations. Model comparisons used Kruskal-Wallis tests with Dunn's post-hoc correction.28 Language comparisons stratified by resource level. Significance was set at p < 0.05. Analyses used Python 3.11 with SciPy (v1.13.1) and statsmodels (v0.14.1).

---

## Results

We completed 702 of 704 translation pairs (99.7%). Two Kimi K2 translations failed due to content filtering.

### Methodological Validation

Back-translation of professional translations yielded high fidelity with original English (LaBSE: 0.92-0.94; BLEU: 43.9-55.8; Supplementary Table S2), establishing the benchmark against which to contextualize LLM performance.

### LLM Back-Translation Fidelity

All models achieved high semantic preservation (Table 1). Kruskal-Wallis testing revealed significant differences between models for both LaBSE (H = 156.67, p < 0.001) and BLEU (H = 170.69, p < 0.001). Dunn's post-hoc tests with Bonferroni correction showed Claude Opus 4.5 significantly outperformed all other models on semantic preservation (all pairwise p < 0.001). GPT-5.1 significantly outperformed Kimi K2 (p = 0.003) and Gemini 3 Pro (p < 0.001), while Gemini 3 Pro and Kimi K2 showed no significant difference (p = 1.0).

**[Table 1 about here]**

### Language Performance by Resource Level

Low-resource languages achieved semantic preservation comparable to high-resource languages (Figure 2, Supplementary Table S3). Tagalog (0.950) and Haitian Creole (0.955) scored on par with Spanish (0.954) and Vietnamese (0.953). Mann-Whitney U testing confirmed no significant difference between resource groups for semantic preservation (LaBSE: 0.948 vs 0.952, p = 0.066).

**[Figure 2 about here]**

Although semantic preservation was comparable across resource levels, high-resource languages showed better alignment with professional translations (COMET: 0.879 vs 0.837, p < 0.001). BLEU scores varied substantially by language (range: 15.5-54.3), while semantic metrics remained consistently high across all languages (LaBSE range: 0.937-0.976).

### LLM vs Professional Translation

LLM translations approached professional quality across all models (Table 2). Kruskal-Wallis testing showed no significant differences between models for COMET (H = 2.07, p = 0.56) or BLEU (H = 5.50, p = 0.14). BERTScore showed a significant effect (H = 13.58, p = 0.004), with post-hoc tests revealing Claude Opus 4.5 significantly outperformed GPT-5.1 (p = 0.04) and Kimi K2 (p = 0.004).

**[Table 2 about here]**

Cancer education materials achieved higher back-translation fidelity (mean LaBSE: 0.984) than Vaccine Information Statements (mean LaBSE: 0.919; Mann-Whitney U, p < 0.001).

---

## Discussion

This study addressed three research questions regarding LLM medical translation capabilities, with findings that have important implications for health equity. First, we found that all frontier LLMs reliably preserve medical meaning through translation, with all models achieving high semantic fidelity (LaBSE > 0.92) across all language-document combinations. Second, translation fidelity did not differ significantly by language resource level: low-resource languages (Tagalog, Haitian Creole) achieved semantic similarity scores statistically indistinguishable from high-resource languages (p = 0.066). Third, LLM translations approached professional quality, with COMET scores of 0.87-0.88 and no significant differences between models on this measure.

### Key Findings

**Equivalent fidelity for low-resource languages.** Tagalog and Haitian Creole (languages comprising less than 0.01% of CommonCrawl) achieved semantic similarity scores that were not statistically distinguishable from those of Spanish and Vietnamese (p = 0.066). This represents a meaningful advance: earlier evaluations of LLMs demonstrated significant performance degradation for digitally underrepresented languages.22 A 2024 study found that ChatGPT and Google Translate had significantly more clinically significant errors for Haitian Creole compared to Spanish and Portuguese when translating pediatric discharge instructions.13 Our finding of equivalent performance for Haitian Creole suggests frontier models released in 2025 may have substantially improved multilingual capabilities for formal patient education materials.

However, lexical overlap with professional translations (BLEU) was lower for low-resource languages, indicating that while LLMs accurately convey the information, they may phrase it differently from a human translator. The likely explanation is that professional translation conventions are more established for high-resource languages such as Spanish and Chinese, providing LLMs with more examples to learn from during training.

**Scalable evaluation methodology.** Automated multilingual metrics enabled rigorous comparison across eight languages without requiring bilingual experts for each pair, a practical necessity when expert evaluators are scarce or unavailable for low-resource languages or for the volume of clinical documentation required to fully engage patients in their care.

**Semantic preservation is more consistent than lexical overlap.** While BLEU scores varied widely by language (range: 15.5-54.3, reflecting morphological and syntactic differences), semantic metrics remained consistently high across all languages (LaBSE range: 0.937-0.976). This validates the importance of using multilingual embedding-based metrics rather than relying solely on n-gram overlap for evaluating translation quality across typologically diverse languages.

**Model convergence.** All four frontier models performed within a narrow band, suggesting that model selection is less critical than language-pair selection. This convergence may reflect shared training approaches, similar underlying architectures, or saturation of translation capabilities at the frontier. Claude Opus 4.5 achieved the highest semantic preservation through back-translation, while Gemini 3 Pro led on lexical agreement with professional translations. These complementary strengths suggest potential for ensemble approaches in production systems.

### Clinical Implications

These findings have implications for the delivery of equitable healthcare at scale. Medical translation services are often unavailable or delayed for speakers of less common languages, creating barriers to informed healthcare decision-making. Our results suggest that for formal patient education materials, LLMs can reliably convey medical information to Tagalog and Haitian Creole speakers with meaning preservation comparable to that achieved for Spanish.

Recent HHS guidance on Section 1557 acknowledges that "exigent circumstances" may arise where machine translation is used before qualified human review is feasible, provided that "the machine translation must be subsequently checked by a qualified human translator as soon as practicable."29 Our findings provide empirical support for such use: frontier LLMs maintain semantic fidelity across resource levels for the types of standardized materials studied here.

### Policy Implications

Current federal rules implementing Section 1557 require that machine translations of critical medical documents be reviewed by a "qualified human translator."6 While intended to ensure quality, this requirement may inadvertently limit access for speakers of low-resource languages where qualified translators are scarce or unavailable. Our findings suggest that for standardized patient education materials, frontier LLMs achieve semantic fidelity comparable across resource levels—raising the question of whether performance-based criteria might better balance quality assurance with equitable access.

### Limitations

**Potential training data contamination.** The medical documents evaluated (CDC Vaccine Information Statements, American Cancer Society patient education materials) are publicly available resources that may be present in LLM training corpora. This potential contamination could artificially inflate performance if models memorized specific content rather than developing generalizable translation capabilities. The comparable performance of low-resource languages raised concern about this possibility. To address this, we conducted a sentence-reordering sensitivity analysis (Supplementary Analysis S1): we randomly shuffled sentence order within documents and repeated the translation pipeline. The hypothesis was that memorized documents would show significant performance degradation when the structure was disrupted. Results showed no significant change in 83% of model-language combinations, suggesting our results primarily reflect translation capability rather than memorization.

**Lexical borrowing in low-resource languages.** Strong back-translation performance of Tagalog and Haitian Creole may partly reflect patterns of lexical borrowing from English.30 Medical Tagalog frequently retains English terminology (e.g., "chemotherapy," "diabetes," "vaccine"), as do many post-colonial languages in technical domains. Similarly, Haitian Creole incorporates substantial French and English vocabulary in medical contexts. This lexical overlap could inflate back-translation fidelity scores relative to languages such as Chinese or Russian, which use entirely distinct native medical terminology. Recent work suggests LLMs exhibit bias toward loanwords and struggle to distinguish borrowed from native vocabulary,31 which may compound this effect. Future work should examine whether translation performance varies systematically between borrowed versus native terminology.

**Automated metrics only.** While we employed multiple validated metrics, automated evaluation cannot fully capture the nuances of medical terminology, cultural appropriateness, or potential for patient misunderstanding. Future work should incorporate human evaluation for a subset of translations.

**Limited document types.** Our corpus consisted solely of patient education materials. Results may not generalize to clinical notes, consent forms, or other medical document types with different linguistic characteristics.

**Single translation direction.** We evaluated English-to-target translation only. Target-to-English translation (relevant for patient-provider communication) may show different patterns.

**Back-translation through the same model.** Using the same LLM for forward and back translation may inflate fidelity scores if the model exhibits consistent translation biases. Future work could employ different models for each direction.

**Snapshot evaluation.** LLM capabilities evolve rapidly; these results reflect model versions available in late 2025 and may not reflect future or past capabilities.

### Future Directions

Several extensions of this work warrant investigation. First, evaluation should be expanded to include additional clinical document types, such as clinician notes, medication instructions, and informed consent forms. Second, given the rapid evolution of LLMs, longitudinal assessment is needed to track translation performance as models are updated. Third, ensemble approaches should be tested to determine whether combining outputs from multiple models yields more reliable translations than a single model. Fourth, evaluation should extend to real-world understanding of patients of medical information and whether these efforts enhance their ability to understand and participate fully in their care. Finally, the technology should be further assessed on the ability to not just translate paper documents, but also to enhance meaningful patient education by providing information in a specified language, at a desired reading level, and in oral or video formats.

---

## Conclusion

Frontier LLMs reliably preserve medical meaning through translation across both high-resource and low-resource languages. Critically, low-resource languages achieve semantic preservation comparable to that of high-resource languages, suggesting that LLMs could extend medical translation access to historically underserved populations.

These findings suggest significant advancement in LLM performance in medical translation of formal patient education information. Should continued assessment show similar performance for other types of medical information, machine translation may open new pathways for patient education in clinical settings.

---

## Data Sharing Statement

All source documents, translation outputs, and evaluation metrics are available at: https://github.com/hallixrap/llm-translation-study

---

## References

1. Simonsmeier BA, Flaig M, Simacek T, Schneider M. What sixty years of research says about the effectiveness of patient education on health: a second order meta-analysis. Health Psychol Rev. 2022;16(3):450-474.

2. U.S. Census Bureau. American Community Survey 2023 1-Year Estimates, Table B16001: Language Spoken at Home by Ability to Speak English for the Population 5 Years and Over. U.S. Census Bureau; 2024. Accessed January 31, 2026. https://data.census.gov/

3. Twersky SE, Jefferson R, Garcia-Ortiz L. The impact of limited English proficiency on healthcare access and outcomes in the U.S.: a scoping review. Healthcare. 2024;12(3):364.

4. Divi C, Koss RG, Schmaltz SP, Loeb JM. Language proficiency and adverse events in US hospitals: a pilot study. Int J Qual Health Care. 2007;19(2):60-67.

5. The Joint Commission. Advancing Effective Communication, Cultural Competence, and Patient- and Family-Centered Care: A Roadmap for Hospitals. 2010.

6. Department of Health and Human Services. Nondiscrimination in Health Programs and Activities. Fed Regist. 2024;89(88):37522-37703.

7. Office of Minority Health. National Standards for Culturally and Linguistically Appropriate Services (CLAS) in Health and Health Care. U.S. Department of Health and Human Services; 2013.

8. Davis SH, Rosenberg J, Nguyen J, et al. Translating discharge instructions for limited English-proficient families: strategies and barriers. Hosp Pediatr. 2019;9(10):779-787.

9. Lopez I, Velasquez DE, Chen JH, Rodriguez JA. Operationalizing machine-assisted translation in healthcare. npj Digit Med. 2025;8:584.

10. Choe AY, Schondelmeyer AC, Thomson J, et al. Improving discharge instructions for hospitalized children with limited English proficiency. Hosp Pediatr. 2021;11(11):1213-1222.

11. Brown T, Mann B, Ryder N, et al. Language models are few-shot learners. Advances in Neural Information Processing Systems. 2020;33:1877-1901.

12. Quan K, Lynch J. The High Costs of Language Barriers in Medical Malpractice. National Health Law Program; 2010.

13. Brewster RC, Gonzalez P, Khazanchi R, et al. Performance of ChatGPT and Google Translate for pediatric discharge instruction translation. Pediatrics. 2024;154(1):e2023065573.

14. American Medical Association. Physician sentiments around the use of AI in health care: motivations, opportunities, risks, and use cases—Shifts from 2023 to 2024. Published February 2025. https://www.ama-assn.org/system/files/physician-ai-sentiment-report.pdf

15. Feng F, Yang Y, Cer D, et al. Language-agnostic BERT sentence embedding. Proceedings of ACL. 2022:878-891.

16. Zhang T, Kishore V, Wu F, Weinberger KQ, Artzi Y. BERTScore: Evaluating text generation with BERT. Proceedings of ICLR. 2020.

17. Rei R, Stewart C, Farinha AC, Lavie A. COMET: A neural framework for MT evaluation. Proceedings of EMNLP. 2020:2685-2702.

18. Brislin RW. Back-translation for cross-cultural research. Journal of Cross-Cultural Psychology. 1970;1(3):185-216.

19. Tyupa S. A theoretical framework for back-translation as a quality assessment tool. New Voices in Translation Studies. 2011;7(1):35-46.

20. Immunize.org. Vaccine Information Statements (VIS). https://www.immunize.org/vis/. Accessed December 20, 2025.

21. American Cancer Society. Cancer Information. https://www.cancer.org/cancer.html. Accessed December 20, 2025.

22. Lai VD, Ngo NT, Pouran Ben Veyseh A, et al. ChatGPT beyond English: towards a comprehensive evaluation of large language models in multilingual learning. Findings of the Association for Computational Linguistics: EMNLP 2023. Singapore: Association for Computational Linguistics; 2023:13171-99.

23. Common Crawl. Statistics of Common Crawl Monthly Archives: Languages. https://commoncrawl.github.io/cc-crawl-statistics/plots/languages.html. Accessed December 20, 2025.

24. Papineni K, Roukos S, Ward T, Zhu WJ. BLEU: a method for automatic evaluation of machine translation. Proceedings of ACL. 2002:311-318.

25. Conneau A, Khandelwal K, Goyal N, et al. Unsupervised cross-lingual representation learning at scale. Proceedings of ACL. 2020:8440-8451.

26. Devlin J, Chang MW, Lee K, Toutanova K. BERT: Pre-training of deep bidirectional transformers for language understanding. Proceedings of NAACL. 2019:4171-4186.

27. Popović M. chrF: character n-gram F-score for automatic MT evaluation. Proceedings of WMT. 2015:392-395.

28. Dunn OJ. Multiple comparisons using rank sums. Technometrics. 1964;6(3):241-252.

29. Office for Civil Rights, U.S. Department of Health and Human Services. Dear Colleague Letter: Language Access and Section 1557 of the Affordable Care Act. October 2024. https://www.hhs.gov/sites/default/files/ocr-dcl-section-1557-language-access.pdf

30. Baklanova E. Types of borrowings in Tagalog/Filipino. Kritika Kultura. 2017;28:35-54.

31. Silva MS, Ahmadi S. Language models are borrowing-blind: a multilingual evaluation of loanword identification across 10 languages. arXiv preprint arXiv:2510.26254. 2025.

---

## Acknowledgments

We thank the CDC, Immunize.org, and the American Cancer Society for making professionally-translated health education materials publicly available.

## Author Contributions

Concept and design: Anyaegbuna, Ma, Steele, Liang, Chen, Schulman
Acquisition, analysis, or interpretation of data: Anyaegbuna, Ma, Liang, Steele, Perez Guerrero, Liu
Drafting of the manuscript: Anyaegbuna
Critical revision of the manuscript for important intellectual content: All authors
Statistical analysis: Anyaegbuna, Keyes
Administrative, technical, or material support: All authors
Supervision: Chen, Schulman

## Funding

Support for this research was provided by the Commonwealth Fund. The views presented here are those of the authors and should not be attributed to the Commonwealth Fund or its directors, officers, or staff.

## Conflicts of Interest

The authors declare no conflicts of interest.

---

## Tables

### Table 1. Back-Translation Fidelity by Model

| Model | n | LaBSE (Mean ± SD) | BLEU (Mean ± SD) |
|-------|---|-------------------|------------------|
| Claude Opus 4.5 | 176 | 0.987 ± 0.013 | 68.7 ± 8.3 |
| GPT-5.1 | 176 | 0.957 ± 0.045 | 64.3 ± 7.4 |
| Kimi K2 | 174 | 0.940 ± 0.053 | 54.9 ± 8.7 |
| Gemini 3 Pro | 176 | 0.921 ± 0.065 | 61.5 ± 9.3 |

Kruskal-Wallis: LaBSE H = 156.67, p < 0.001; BLEU H = 170.69, p < 0.001.

### Table 2. LLM vs Professional Translation Quality

| Model | n | BLEU | BERTScore | COMET |
|-------|---|------|-----------|-------|
| Gemini 3 Pro | 176 | 39.4 ± 14.9 | 0.845 ± 0.060 | 0.876 ± 0.054 |
| Claude Opus 4.5 | 176 | 37.3 ± 14.4 | 0.859 ± 0.043 | 0.874 ± 0.054 |
| GPT-5.1 | 176 | 36.0 ± 13.8 | 0.844 ± 0.052 | 0.871 ± 0.052 |
| Kimi K2 | 174 | 36.0 ± 14.3 | 0.840 ± 0.052 | 0.872 ± 0.052 |

---

## Figure Legends

**Figure 1. LLM Translation and Evaluation Pipeline.** Original English source documents (CDC/ACS) undergo forward translation into the target language, followed by back-translation into English by the same LLM. Professional translations serve as a baseline for validation. All outputs are compared to the original English using automated multilingual metrics (BLEU, LaBSE, BERTScore, COMET).

**Figure 2. Semantic vs Lexical Fidelity by Language and Resource Level.** (A) Semantic fidelity (LaBSE score) shows consistent preservation of meaning across languages, with low-resource languages (Tagalog, Haitian Creole) achieving scores comparable to those of high-resource languages. The dashed line indicates a 0.95 high-fidelity threshold. (B) Lexical fidelity (BLEU score vs. professional translation) varies substantially across languages, reflecting morphological and syntactic differences rather than translation quality. Colors indicate resource level: blue = high-resource (>1% CommonCrawl), purple = medium-resource (0.1-1%), orange = low-resource (<0.1%).
