# STARD 2015 Checklist

**Manuscript:** Evaluating Large Language Model Translation Fidelity for Medical Documents Across High- and Low-Resource Languages

| Section & Topic | No | STARD 2015 Item | Location in Manuscript |
|---|---|---|---|
| **TITLE/ABSTRACT** | | | |
| Title | 1 | Identification as a study of diagnostic accuracy using at least one measure of accuracy | Title and Abstract (LaBSE, BLEU, COMET, BERTScore reported) |
| Abstract | 2 | Structured summary of study design, methods, results, and conclusions | Abstract, lines 6–20 |
| **INTRODUCTION** | | | |
| | 3 | Scientific and clinical background, including the intended use and clinical role of the index test | Introduction, paragraphs 1–4 (language barriers, LEP population, clinical need for translation) |
| | 4 | Study objectives and hypotheses | Methods — Study Objectives, line 52–56 |
| **METHODS** | | | |
| Study design | 5 | Whether data collection was planned before the index test and reference standard were performed (prospective study) or after (retrospective study) | Methods — Study Design, line 58–60: Prospective evaluation; all translations performed for this study |
| Participants | 6 | Eligibility criteria | Methods — Data Sample, lines 68–74: 22 documents from CDC VIS and ACS, selected based on availability of professional translations in all 8 languages |
| | 7 | On what basis potentially eligible participants were identified | Methods — Data Sample, lines 68–74: Documents selected from Immunize.org and American Cancer Society based on availability of professional translations |
| | 8 | Where and when potentially eligible participants were identified (setting, location and dates) | Methods — Study Design, line 62: Models accessed via APIs; documents from Immunize.org and ACS. Accessed December 2025 |
| | 9 | Whether participants formed a consecutive, random, or convenience series | Methods — Data Sample, lines 68–74: All available documents meeting inclusion criteria (complete professional translations in all 8 languages) |
| Test methods | 10a | Index test, in sufficient detail to allow replication | Methods — Translation Pipeline, lines 82–88: Forward translation (English → target) and back-translation (target → English) using same LLM via API with default parameters |
| | 10b | Reference standard, in sufficient detail to allow replication | Methods — Data Sample, lines 68–74: Professionally translated documents from CDC/Immunize.org and ACS, publicly available |
| | 11 | Rationale for choosing the reference standard (if alternatives exist) | Methods — Evaluation Metrics, lines 94–100: Professional translations represent the clinical standard against which LLM output should be compared |
| | 12a | Definition of and rationale for test positivity cut-offs or result categories of the index test, distinguishing pre-specified from exploratory | Methods — Evaluation Metrics, lines 94–100: LaBSE >0.90 = high semantic preservation; differences of 0.05 = meaningful variation. BLEU >50 = strong word-level agreement. Pre-specified thresholds |
| | 12b | Definition of and rationale for test positivity cut-offs or result categories of the reference standard, distinguishing pre-specified from exploratory | Methods — Methodological Validation, line 96: Professional back-translation fidelity (LaBSE 0.92–0.94) establishes the benchmark |
| | 13a | Whether clinical information was available to the performers/readers of the index test | Methods — Translation Pipeline, line 88: Back-translation had no access to original English text (separate API calls) |
| | 13b | Whether clinical information was available to the assessors of the reference standard | Methods — Evaluation Metrics, lines 94–100: Automated metrics computed without human judgment; all metrics applied identically to LLM and professional translations |
| Analysis | 14 | Methods for estimating or comparing measures of diagnostic accuracy | Methods — Statistical Analysis, lines 102–104: Kruskal-Wallis with Dunn's post-hoc correction; Mann-Whitney U for resource-level comparisons; p < 0.05 |
| | 15 | How indeterminate index test or reference standard results were handled | Results, line 110: 2 of 704 translations failed (Kimi K2 content filtering); excluded from analysis |
| | 16 | How missing data on the index test and reference standard were handled | Results, line 110: 702 of 704 completed (99.7%); 2 failures excluded |
| | 17 | Any analyses of variability in diagnostic accuracy, distinguishing pre-specified from exploratory | Methods/Results: Pre-specified comparisons by model (Table 1), resource level (Figure 2), and document category (cancer vs. vaccine). Sensitivity analysis (Supplement S1) |
| | 18 | Intended sample size and how it was determined | Methods — Data Sample, lines 68–74: Complete enumeration — all 22 documents × 8 languages × 4 models = 704 pairs. Sample determined by available professionally translated documents |
| **RESULTS** | | | |
| Participants | 19 | Flow of participants, using a diagram | Figure 1: Translation and evaluation pipeline diagram |
| | 20 | Baseline demographic and clinical characteristics of participants | Supplementary Table S1: Language classifications with CommonCrawl percentages and U.S. speaker populations; Data Sample describes document sources and domains |
| | 21a | Distribution of severity of disease in those with the target condition | Not directly applicable. Analogous: Table S3 shows performance distribution across languages/resource levels |
| | 21b | Distribution of alternative diagnoses in those without the target condition | Not directly applicable |
| Test results | 22 | Time interval and any clinical interventions between index test and reference standard | Not applicable — LLM and professional translations evaluated simultaneously using same automated metrics |
| | 23 | Cross tabulation of the index test results by the results of the reference standard | Table 1 (back-translation fidelity by model), Table 2 (LLM vs professional translation), Table S3 (by language) |
| | 24 | Estimates of diagnostic accuracy and their precision (such as 95% confidence intervals) | Tables 1–2: Mean ± SD for all metrics; H-statistics and p-values for all comparisons |
| | 25 | Any adverse events from performing the index test or reference standard | Results, line 110: 2 content filtering failures from Kimi K2; no other adverse events |
| **DISCUSSION** | | | |
| | 26 | Study limitations, including sources of potential bias, statistical uncertainty, and generalizability | Discussion — Limitations, lines 166–181: Training data contamination, lexical borrowing, automated metrics only, limited document types, single translation direction, same-model back-translation, snapshot evaluation |
| | 27 | Implications for practice, including the intended use and clinical role of the index test | Discussion — Clinical Implications, lines 156–161; Policy Implications, lines 163–164 |
| **OTHER INFORMATION** | | | |
| | 28 | Registration number and name of registry | Not registered (not a clinical trial) |
| | 29 | Where the full study protocol can be accessed | Data Sharing Statement, line 198: https://github.com/hallixrap/llm-translation-study |
| | 30 | Sources of funding and other support; role of funders | Funding, lines 282–284: Commonwealth Fund; views are authors' own |
