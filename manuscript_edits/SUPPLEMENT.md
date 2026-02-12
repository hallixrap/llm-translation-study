# Online Supplementary Materials

**Manuscript:** Evaluating Large Language Model Translation Fidelity for Medical Documents Across High- and Low-Resource Languages

---

## Supplementary Table S1: Language Classification Details

| Language | Resource Level | CommonCrawl % | U.S. Speakers (millions) |
|----------|----------------|---------------|--------------------------|
| Russian | High | 6.48 | 0.9 |
| Chinese (Simplified) | High | 6.18 | 3.5 |
| Spanish | High | 4.41 | 41.8 |
| Vietnamese | High | 1.08 | 1.6 |
| Korean | Medium | 0.80 | 1.1 |
| Arabic | Medium | 0.67 | 1.3 |
| Tagalog | Low | 0.008 | 1.8 |
| Haitian Creole | Low | 0.003 | 0.9 |

High-resource: >1%; medium-resource: 0.1–1%; low-resource: <0.1%. U.S. speaker populations from American Community Survey.

---

## Supplementary Analysis S1: Sentence Reordering Sensitivity Analysis

To address training data contamination concerns, we tested whether performance reflects document memorization versus true translation capability by randomly shuffling sentence order in 10 documents and comparing performance.

**Results:** No significant performance change in 10 of 12 model-language combinations (83%). Two comparisons reached significance: Claude Opus 4.5 with Tagalog showed 6.0% decrease (p=0.041); Gemini 3 Pro with Tagalog showed 3.0% increase (p=0.026), opposite to what memorization would predict.

**Negative Control:** A direct comparison of the original and shuffled documents (without translation) yielded a LaBSE of 0.81, confirming that the metric is sensitive to structural changes. Back-translations from both conditions achieved ~0.95, well above this baseline, indicating semantic preservation rather than memorization.

---

## Supplementary Table S2: Professional Translation Back-Translation Fidelity

| Model | BLEU | BERTScore | LaBSE |
|-------|------|-----------|-------|
| GPT-5.1 | 55.8 | 0.919 | 0.940 |
| Claude Opus 4.5 | 54.7 | 0.924 | 0.942 |
| Gemini 3 Pro | 48.3 | 0.913 | 0.928 |
| Kimi K2 | 43.9 | 0.912 | 0.934 |

---

## Supplementary Table S3: Translation Fidelity by Language

| Language | Resource | Back-Translation LaBSE | vs Professional BLEU |
|----------|----------|------------------------|---------------------|
| Arabic | Medium | 0.976 | 41.6 |
| Haitian Creole | Low | 0.955 | 37.2 |
| Spanish | High | 0.954 | 54.3 |
| Vietnamese | High | 0.953 | 50.1 |
| Tagalog | Low | 0.950 | 43.8 |
| Russian | High | 0.945 | 33.4 |
| Chinese | High | 0.942 | 15.5 |
| Korean | Medium | 0.937 | 21.7 |
