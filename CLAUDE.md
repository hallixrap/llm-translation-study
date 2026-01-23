# Claude Code Instructions for This Project

## CRITICAL: Manuscript Statistics Verification Checklist

Before finalizing ANY manuscript, run a comprehensive audit of ALL statistics against the actual data files. This prevents publication crises.

### Pre-Submission Verification Steps

#### 1. Basic Counts
```python
# Verify total records match expected: docs × languages × models
# Check for null/missing values
# Verify n-counts per model/language match what's in tables
```

#### 2. Table-by-Table Verification
For EACH table in the manuscript:
- [ ] Extract claimed values from manuscript
- [ ] Calculate actual values from data files (`output/medlineplus_metrics/all_metrics.json`)
- [ ] Compare and flag ANY discrepancy > 0.001 for proportions or > 0.1 for scores
- [ ] Verify sample sizes (n) match

#### 3. Statistical Tests Verification
- [ ] Re-run ALL Kruskal-Wallis tests and compare H-statistics
- [ ] Re-run ALL Mann-Whitney U tests and compare p-values
- [ ] Re-run ALL post-hoc tests (Dunn's) and verify pairwise comparisons
- [ ] Check that significance conclusions match (p < 0.05 threshold)

#### 4. Range Claims
Search for patterns like "X-Y" or "X to Y" and verify:
- [ ] All numeric ranges cited in abstract
- [ ] All numeric ranges cited in results
- [ ] All numeric ranges cited in discussion
- [ ] Figure captions match actual data

#### 5. Reference Verification
For EACH numbered reference [N]:
- [ ] Verify the citation exists in the References section
- [ ] Verify the reference supports the claim being made
- [ ] Check for broken/placeholder references
- [ ] Verify URLs are still accessible

### Common Pitfalls Found in This Project

1. **Language key mismatch**: Data uses `chinese_simplified` but calculations might use `chinese`
2. **Resource level classification errors**: Vietnamese/Korean were misclassified
3. **Stale statistics**: H-values, p-values can drift with data updates
4. **Document category claims**: Verify ANY claim about subgroup comparisons
5. **Professional translation metrics**: Multiple similar metrics (prof_backtrans_labse vs cross_lang_labse)

### Key Data Files

- `output/medlineplus_metrics/all_metrics.json` - Main metrics data
- `output/medlineplus_results/all_results.json` - Translation results
- `output/statistical_tests/statistical_tests.json` - Pre-computed stats
- `scripts/config.py` - Language classifications (VERIFY THESE MATCH)

### Verification Script Template

```python
import json
import numpy as np
from scipy.stats import kruskal, mannwhitneyu

with open('output/medlineplus_metrics/all_metrics.json', 'r') as f:
    metrics = json.load(f)

# ALWAYS verify language classifications match across files
LANGUAGES = {
    'spanish': 'high',
    'chinese_simplified': 'high',  # NOT 'chinese'
    'vietnamese': 'high',          # >1% CommonCrawl
    'russian': 'high',
    'korean': 'medium',            # 0.1-1% CommonCrawl
    'arabic': 'medium',
    'tagalog': 'low',
    'haitian_creole': 'low'
}

# Verify each table value...
```

### After ANY Data Change

If ANY of these files change, re-verify ALL manuscript statistics:
- `all_metrics.json`
- `all_results.json`
- `config.py` (especially LANGUAGES dict)
- Any script that computes metrics

### Reference Verification Checklist

When verifying references:
1. Check that [1] through [N] all exist in References section
2. Verify no duplicate reference numbers
3. Check that each reference is cited at least once
4. Verify DOIs/URLs are valid
5. Check author names, years, journal names for typos

**Verification Script:**
```bash
# Count citations for each reference number
for i in {1..15}; do
  count=$(grep -cE "\[$i\]|\[$i," MANUSCRIPT.md)
  echo "[$i]: cited $count times"
done
```

**IMPORTANT**: Watch for multi-reference citations like `[6, 7]` which won't match `\[6\]` alone.

### Corrections Made in January 2026 Audit

1. **Table 4 p-values**: Changed LaBSE p=0.246 → p=0.066 (language key mismatch)
2. **Document Category Analysis**: Changed "no significant difference (p=0.34)" to "significant difference (p<0.001)" - vaccine vs cancer docs ARE different
3. **H-statistics**: Updated Table 1 (156.67, 170.69) and Table 2 (2.07, 5.50, 13.58)
4. **Resource classifications**: Fixed Vietnamese (medium→high) and Korean (high→medium)
