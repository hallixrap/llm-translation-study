# Supplementary tables, regenerated

All values recomputed on 150-word aligned segments over the 702 analyzed
translations. BLEU has been replaced throughout by chrF, which is comparable
across the eight writing systems in this corpus.

## Supplementary Table S2. Professional translation back-translation fidelity

Each model was also asked to back-translate the professional human translation.
This establishes what the round trip scores when the forward translation is
known to be of professional quality, giving the benchmark against which the
LLM round trip is read.

| Back-translating model | chrF vs English source | SD | n |
|---|---|---|---|
| Claude Opus 4.5 | 78.5 | 5.1 | 175 |
| Gemini 3 Pro | 75.0 | 8.6 | 176 |
| GPT-5.1 | 79.3 | 5.3 | 176 |
| Kimi K2 Thinking | 72.3 | 6.1 | 173 |

chrF of the back-translated professional text against the English source.
Segment-level LaBSE was not recomputed for the professional back-translation arm,
so this table reports chrF only.

## Supplementary Table S3. Translation fidelity by language

| Language | Resource level | Back-translation LaBSE | SD | chrF vs professional | n |
|---|---|---|---|---|---|
| Arabic | Medium | 0.921 | 0.055 | 69.3 | 87 |
| Tagalog | Low | 0.892 | 0.091 | 72.7 | 87 |
| Spanish | High | 0.891 | 0.095 | 77.1 | 88 |
| Vietnamese | High | 0.887 | 0.088 | 66.7 | 88 |
| Haitian Creole | Low | 0.878 | 0.082 | 63.7 | 88 |
| Russian | High | 0.875 | 0.088 | 65.6 | 88 |
| Chinese (Simplified) | High | 0.866 | 0.087 | 44.0 | 88 |
| Korean | Medium | 0.856 | 0.083 | 43.6 | 88 |

Means across all four models and 22 documents. LaBSE compares each back-translation
with the English source; chrF compares each forward translation with the professional
translation. The two rank languages differently because chrF is depressed for languages
that do not map word-for-word onto English, which is a property of the writing system
rather than of translation quality.

## Supplementary Table S4. Inter-model concordance by language

| Language | Resource level | n pairs | LaBSE | SD |
|---|---|---|---|---|
| Arabic | Medium | 126 | 0.935 | 0.046 |
| Chinese (Simplified) | High | 132 | 0.899 | 0.124 |
| Tagalog | Low | 129 | 0.894 | 0.087 |
| Spanish | High | 132 | 0.893 | 0.091 |
| Korean | Medium | 132 | 0.889 | 0.073 |
| Russian | High | 132 | 0.882 | 0.088 |
| Haitian Creole | Low | 132 | 0.869 | 0.086 |
| Vietnamese | High | 132 | 0.867 | 0.090 |

Pairwise comparisons between the forward translations of independently developed
models, 1047 in total. Agreement is not greatest in the languages with the
most training text, which is one of two observations arguing against a strong
memorization account.

## Supplementary Table S5. Verbatim retention of English medical terminology

| Language | Resource level | Professional % | LLM % | LLM SD | Spearman rho vs LaBSE | p | n |
|---|---|---|---|---|---|---|---|
| Tagalog | Low | 60.8 | 69.0 | 15.6 | +0.146 | 0.178 | 87 |
| Vietnamese | High | 30.3 | 25.1 | 12.6 | -0.266 | 0.012 | 88 |
| Haitian Creole | Low | 30.5 | 24.3 | 14.0 | -0.417 | <0.001 | 88 |
| Korean | Medium | 28.3 | 22.3 | 13.8 | -0.248 | 0.020 | 88 |
| Spanish | High | 31.6 | 21.2 | 11.4 | -0.464 | <0.001 | 88 |
| Arabic | Medium | 26.7 | 20.4 | 12.8 | -0.132 | 0.227 | 86 |
| Chinese (Simplified) | High | 27.7 | 19.4 | 10.7 | -0.481 | <0.001 | 88 |
| Russian | High | 29.3 | 16.7 | 9.4 | -0.328 | 0.002 | 88 |

**Summary**

| Group | n | Professional % | LLM % |
|---|---|---|---|
| Low-resource combined | 175 | 45.5 | 46.5 |
| All languages | 701 | 33.1 | 27.3 |

Retention rate: of the 213 English medical terms present in a document's English
source, the share reproduced verbatim in the translation. Word-boundary matching,
case-insensitive, averaged per translation. The two zero-byte translations are excluded,
so this analysis covers the same 702 translations as the rest of the paper.

Professional translators retain more English terminology than the models in 7 of 8 languages, which is the comparison the main text reports. By forward model, LLM retention was GPT-5.1 34.6%, Gemini 3 Pro 26.8%, Claude Opus 4.5 24.1%, Kimi K2 Thinking 23.5%.

The Spearman column tests the separate question of whether retaining more English
predicts a higher fidelity score.

Across all languages the correlation is -0.218 (p=<0.001), and it is negative in 7 of 8 languages individually (6 significantly so). Verbatim retention therefore does not inflate the fidelity metric.

## Supplementary Table S7. Cross-model sensitivity restricted to the three back-translating models

Kimi K2 never served as a back-translator, so the main-text Table 2 draws on a
different number of back-translations per forward model. To check that this asymmetry
does not drive the result, both columns are restricted here to forward models that
also acted as back-translators.

| Forward model | Same-model | Cross-model | Difference | p | n |
|---|---|---|---|---|---|
| Claude Opus 4.5 | 0.940 | 0.915 | -0.025 | <0.001 | 175 |
| Gemini 3 Pro | 0.853 | 0.859 | +0.006 | 0.008 | 176 |
| GPT-5.1 | 0.880 | 0.883 | +0.003 | 0.289 | 174 |
| **Overall** | **0.891** | **0.886** | **-0.005** | **0.376** | **525** |

The pattern of the main analysis is preserved: the highest-scoring model is the only
one that declines when a different model performs the back-translation.

## Supplementary Table S8. Whole-document and segment-level values compared

The metric as originally implemented scored each document as a single unit, which
truncated it to the model's maximum input length. This table gives both values for
every comparison the main text reports, so the effect of the correction is visible.

| Group | Whole-document LaBSE | Segment-level LaBSE | Difference | n |
|---|---|---|---|---|
| All translations | 0.951 | 0.883 | -0.068 | 704 |
| Low-resource | 0.952 | 0.885 | -0.067 | 176 |
| High-resource | 0.948 | 0.880 | -0.069 | 352 |
| Cancer materials | 0.983 | 0.934 | -0.049 | 352 |
| Vaccine statements | 0.919 | 0.832 | -0.087 | 352 |

| Distribution | Whole-document | Segment-level |
|---|---|---|
| Share scoring above 0.98 | 54.1% | 10.5% |
| Interquartile range | 0.085 | 0.155 |

Scoring whole documents placed 54.1% of translations in the top 2% of the scale, against 10.5% under segment-level scoring, and the interquartile range widens from 0.085 to 0.155. The resource-level comparison in the main text is therefore made on a measure with the dynamic range to have detected a difference had one been present.

## Supplementary Table S9. Continuation probe for memorization

| Model | Published text chrF | Unpublished control chrF | Difference | p | n |
|---|---|---|---|---|---|
| Claude Opus 4.5 | 39.4 | 43.8 | +4.4 | <0.001 | 160 |
| GPT-5.1 | 39.2 | 40.3 | +1.1 | 0.006 | 157 |
| **All items** | **39.3** | **42.0** | **+2.8** | **<0.001** | **317** |

| Resource level | Control minus published | n |
|---|---|---|
| High | +4.0 | 142 |
| Medium | +2.6 | 88 |
| Low | +1.0 | 87 |

High versus low resource: p=0.23. Memorization would predict closer agreement with the published text than with the control, and a larger signal where training text is most abundant. Neither is observed.

## Supplementary Analysis S2. Clustered resource-level test

Each document was translated by four models into eight languages, so the 702
translations are not independent. All group comparisons were therefore repeated
after averaging within each document-language combination.

| Resource level | n clusters | Mean segment-level LaBSE | SD |
|---|---|---|---|
| High | 88 | 0.880 | 0.068 |
| Medium | 44 | 0.889 | 0.062 |
| Low | 44 | 0.885 | 0.069 |

- Low minus high resource: +0.005 (95% CI -0.020 to 0.029, 10,000 bootstrap resamples)
- Mann-Whitney, high versus low: p=0.57
- Kruskal-Wallis across three resource levels: H=0.28, p=0.87

The confidence interval indicates the size of difference that could still have been
missed. Absence of a detected difference is not demonstrated equivalence.
