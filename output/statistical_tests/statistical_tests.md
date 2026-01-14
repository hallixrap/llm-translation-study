# Statistical Test Results

Generated automatically to address April's Comment #1

## Table 1: Model Performance Comparisons

*Kruskal-Wallis test with Dunn's post-hoc (Bonferroni correction)*


### LaBSE (Goal 1)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 0.9568 ± 0.0452 | 176 |
| claude-opus-4.5 | 0.9871 ± 0.0135 | 175 |
| gemini-3-pro | 0.9214 ± 0.0650 | 176 |
| kimi-k2 | 0.9402 ± 0.0526 | 174 |

**Kruskal-Wallis test**: H = 155.36, p = 0.0000 ***

*Significant difference detected between models (p < 0.05)*

**Dunn's post-hoc pairwise comparisons** (corrected p-values):

| | claude-opus-4.5 | gemini-3-pro | gpt-5.1 | kimi-k2 |
|-|-|-|-|-|
| claude-opus-4.5 | 1.0000 ns | 0.0000 *** | 0.0000 *** | 0.0000 *** |
| gemini-3-pro | 0.0000 *** | 1.0000 ns | 0.0000 *** | 1.0000 ns |
| gpt-5.1 | 0.0000 *** | 0.0000 *** | 1.0000 ns | 0.0031 ** |
| kimi-k2 | 0.0000 *** | 1.0000 ns | 0.0031 ** | 1.0000 ns |


### BLEU Back-trans (Goal 1)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 64.2757 ± 7.3732 | 176 |
| claude-opus-4.5 | 68.5607 ± 8.3275 | 175 |
| gemini-3-pro | 61.4540 ± 9.3013 | 176 |
| kimi-k2 | 54.9489 ± 8.6969 | 174 |

**Kruskal-Wallis test**: H = 169.40, p = 0.0000 ***

*Significant difference detected between models (p < 0.05)*

**Dunn's post-hoc pairwise comparisons** (corrected p-values):

| | claude-opus-4.5 | gemini-3-pro | gpt-5.1 | kimi-k2 |
|-|-|-|-|-|
| claude-opus-4.5 | 1.0000 ns | 0.0000 *** | 0.0003 *** | 0.0000 *** |
| gemini-3-pro | 0.0000 *** | 1.0000 ns | 0.0423 * | 0.0000 *** |
| gpt-5.1 | 0.0003 *** | 0.0423 * | 1.0000 ns | 0.0000 *** |
| kimi-k2 | 0.0000 *** | 0.0000 *** | 0.0000 *** | 1.0000 ns |


### COMET (Goal 2)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 0.8714 ± 0.0522 | 176 |
| claude-opus-4.5 | 0.8734 ± 0.0542 | 175 |
| gemini-3-pro | 0.8756 ± 0.0536 | 176 |
| kimi-k2 | 0.8725 ± 0.0524 | 174 |

**Kruskal-Wallis test**: H = 2.04, p = 0.5633 ns

*No significant difference between models*


### BLEU (Goal 2)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 36.0225 ± 13.7866 | 176 |
| claude-opus-4.5 | 37.2537 ± 14.4386 | 175 |
| gemini-3-pro | 39.4386 ± 14.8889 | 176 |
| kimi-k2 | 35.9858 ± 14.3452 | 174 |

**Kruskal-Wallis test**: H = 5.44, p = 0.1421 ns

*No significant difference between models*


### BERTScore (Goal 2)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 0.8437 ± 0.0523 | 176 |
| claude-opus-4.5 | 0.8589 ± 0.0430 | 175 |
| gemini-3-pro | 0.8448 ± 0.0595 | 176 |
| kimi-k2 | 0.8401 ± 0.0515 | 174 |

**Kruskal-Wallis test**: H = 13.03, p = 0.0046 **

*Significant difference detected between models (p < 0.05)*

**Dunn's post-hoc pairwise comparisons** (corrected p-values):

| | claude-opus-4.5 | gemini-3-pro | gpt-5.1 | kimi-k2 |
|-|-|-|-|-|
| claude-opus-4.5 | 1.0000 ns | 0.1435 ns | 0.0417 * | 0.0039 ** |
| gemini-3-pro | 0.1435 ns | 1.0000 ns | 1.0000 ns | 1.0000 ns |
| gpt-5.1 | 0.0417 * | 1.0000 ns | 1.0000 ns | 1.0000 ns |
| kimi-k2 | 0.0039 ** | 1.0000 ns | 1.0000 ns | 1.0000 ns |


### LaBSE Prof (Goal 3)

| Model | Mean ± SD | n |
|-------|-----------|---|
| gpt-5.1 | 0.9403 ± 0.0442 | 176 |
| claude-opus-4.5 | 0.9423 ± 0.0440 | 175 |
| gemini-3-pro | 0.9281 ± 0.0533 | 176 |
| kimi-k2 | 0.9339 ± 0.0484 | 172 |

**Kruskal-Wallis test**: H = 7.53, p = 0.0568 ns

*No significant difference between models*


## Table 2: Language Resource Level Comparisons

*Mann-Whitney U test comparing high-resource vs low-resource languages*

| Metric | High-Resource | Low-Resource | Difference | p-value | Interpretation |
|--------|---------------|--------------|------------|---------|----------------|
| LaBSE (Goal 1) | 0.9445 | 0.9521 | +0.0076 | 0.0022 ** | Low-resource BETTER |
| BLEU Back-trans (Goal 1) | 59.3772 | 65.2854 | +5.9082 | 0.0000 *** | Low-resource BETTER |
| COMET (Goal 2) | 0.8790 | 0.8369 | -0.0421 | 0.0000 *** | High-resource BETTER |
| BLEU (Goal 2) | 31.2304 | 40.5055 | +9.2751 | 0.0000 *** | Low-resource BETTER |
| BERTScore (Goal 2) | 0.8428 | 0.8338 | -0.0090 | 0.0586 ns | No significant difference |
| LaBSE Prof (Goal 3) | 0.9307 | 0.9347 | +0.0040 | 0.3394 ns | No significant difference |

## Significance Key

- *** : p < 0.001
- ** : p < 0.01
- * : p < 0.05
- ns : not significant (p ≥ 0.05)
