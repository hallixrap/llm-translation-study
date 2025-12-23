# File Update Checklist for Clean Text Extraction

**Total files: 198** (22 documents × 9 languages)

After updating files, run:
1. `python scripts/run_medlineplus_translations.py` (re-translate with clean English)
2. `python scripts/calculate_medlineplus_metrics.py` (re-calculate all metrics)
3. `python scripts/generate_github_outputs.py` (regenerate reports/charts)

---

## PRIORITY 1: English Source Files (22 files)

These are the source texts that LLMs translate FROM. **Most critical to fix.**

### Immunize (11 VIS documents)
Location: `data/extracted_text/immunize/english/`

- [ ] `flu_inactive.txt` - Influenza (Inactivated) VIS
- [ ] `hepatitis_b.txt` - Hepatitis B VIS
- [ ] `hpv.txt` - HPV VIS
- [ ] `meningococcal_acwy.txt` - Meningococcal ACWY VIS
- [ ] `mmr.txt` - MMR VIS
- [ ] `pcv.txt` - Pneumococcal Conjugate VIS
- [ ] `polio_ipv.txt` - Polio (IPV) VIS
- [ ] `ppsv.txt` - Pneumococcal Polysaccharide VIS
- [ ] `tdap.txt` - Tdap VIS
- [ ] `varicella.txt` - Varicella (Chickenpox) VIS
- [ ] `zoster_recombinant.txt` - Shingles (Recombinant) VIS

### Cancer (11 ACS documents)
Location: `data/extracted_text/cancer/english/`

- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

## PRIORITY 2: Professional Translations (176 files)

These are reference translations for same-language metrics comparison.

### Spanish (22 files) - QUALITY: Good
Location: `data/extracted_text/immunize/spanish/` and `data/extracted_text/cancer/spanish/`

**Immunize:**
- [ ] `spanish_flu_inactive.txt`
- [ ] `spanish_hepatitis_b.txt`
- [ ] `spanish_hpv.txt`
- [ ] `spanish_meningococcal.txt`
- [ ] `spanish_mmr.txt`
- [ ] `spanish_pcv.txt`
- [ ] `spanish_polio_ipv.txt`
- [ ] `spanish_ppsv.txt`
- [ ] `spanish_tdap.txt`
- [ ] `spanish_varicella.txt`
- [ ] `spanish_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Chinese Simplified (22 files) - QUALITY: Poor (numbers separated, garbled URLs)
Location: `data/extracted_text/immunize/chinese/` and `data/extracted_text/cancer/chinese/`

**Immunize:**
- [ ] `chinese_simplified_flu_inactive.txt`
- [ ] `chinese_simplified_hepatitis_b.txt`
- [ ] `chinese_simplified_hpv.txt`
- [ ] `chinese_simplified_meningococcal.txt`
- [ ] `chinese_simplified_mmr.txt`
- [ ] `chinese_simplified_pcv.txt`
- [ ] `chinese_simplified_polio_ipv.txt`
- [ ] `chinese_simplified_ppsv.txt`
- [ ] `chinese_simplified_tdap.txt`
- [ ] `chinese_simplified_varicella.txt`
- [ ] `chinese_simplified_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Vietnamese (22 files) - QUALITY: Good
Location: `data/extracted_text/immunize/vietnamese/` and `data/extracted_text/cancer/vietnamese/`

**Immunize:**
- [ ] `vietnamese_flu_inactive.txt`
- [ ] `vietnamese_hepatitis_b.txt`
- [ ] `vietnamese_hpv.txt`
- [ ] `vietnamese_meningococcal.txt`
- [ ] `vietnamese_mmr.txt`
- [ ] `vietnamese_pcv.txt`
- [ ] `vietnamese_polio_ipv.txt`
- [ ] `vietnamese_ppsv.txt`
- [ ] `vietnamese_tdap.txt`
- [ ] `vietnamese_varicella.txt`
- [ ] `vietnamese_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Russian (22 files) - QUALITY: Unknown
Location: `data/extracted_text/immunize/russian/` and `data/extracted_text/cancer/russian/`

**Immunize:**
- [ ] `russian_flu_inactive.txt`
- [ ] `russian_hepatitis_b.txt`
- [ ] `russian_hpv.txt`
- [ ] `russian_meningococcal.txt`
- [ ] `russian_mmr.txt`
- [ ] `russian_pcv.txt`
- [ ] `russian_polio_ipv.txt`
- [ ] `russian_ppsv.txt`
- [ ] `russian_tdap.txt`
- [ ] `russian_varicella.txt`
- [ ] `russian_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Arabic (22 files) - QUALITY: Medium (RTL issues)
Location: `data/extracted_text/immunize/arabic/` and `data/extracted_text/cancer/arabic/`

**Immunize:**
- [ ] `arabic_flu_inactive.txt`
- [ ] `arabic_hepatitis_b.txt`
- [ ] `arabic_hpv.txt`
- [ ] `arabic_meningococcal.txt`
- [ ] `arabic_mmr.txt`
- [ ] `arabic_pcv.txt`
- [ ] `arabic_polio_ipv.txt`
- [ ] `arabic_ppsv.txt`
- [ ] `arabic_tdap.txt`
- [ ] `arabic_varicella.txt`
- [ ] `arabic_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Korean (22 files) - QUALITY: Poor (numbers separated, spacing issues)
Location: `data/extracted_text/immunize/korean/` and `data/extracted_text/cancer/korean/`

**Immunize:**
- [ ] `korean_flu_inactive.txt`
- [ ] `korean_hepatitis_b.txt`
- [ ] `korean_hpv.txt`
- [ ] `korean_meningococcal.txt`
- [ ] `korean_mmr.txt`
- [ ] `korean_pcv.txt`
- [ ] `korean_polio_ipv.txt`
- [ ] `korean_ppsv.txt`
- [ ] `korean_tdap.txt`
- [ ] `korean_varicella.txt`
- [ ] `korean_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Tagalog (22 files) - QUALITY: Unknown
Location: `data/extracted_text/immunize/tagalog/` and `data/extracted_text/cancer/tagalog/`

**Immunize:**
- [ ] `tagalog_flu_inactive.txt`
- [ ] `tagalog_hepatitis_b.txt`
- [ ] `tagalog_hpv.txt`
- [ ] `tagalog_meningococcal.txt`
- [ ] `tagalog_mmr.txt`
- [ ] `tagalog_pcv.txt`
- [ ] `tagalog_polio_ipv.txt`
- [ ] `tagalog_ppsv.txt`
- [ ] `tagalog_tdap.txt`
- [ ] `tagalog_varicella.txt`
- [ ] `tagalog_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

### Haitian Creole (22 files) - QUALITY: Unknown
Location: `data/extracted_text/immunize/haitian_creole/` and `data/extracted_text/cancer/haitian_creole/`

**Immunize:**
- [ ] `haitian_creole_flu_inactive.txt`
- [ ] `haitian_creole_hepatitis_b.txt`
- [ ] `haitian_creole_hpv.txt`
- [ ] `haitian_creole_meningococcal.txt`
- [ ] `haitian_creole_mmr.txt`
- [ ] `haitian_creole_pcv.txt`
- [ ] `haitian_creole_polio_ipv.txt`
- [ ] `haitian_creole_ppsv.txt`
- [ ] `haitian_creole_tdap.txt`
- [ ] `haitian_creole_varicella.txt`
- [ ] `haitian_creole_zoster_recombinant.txt`

**Cancer:**
- [ ] `after-a-breast-cancer-diagnosis.txt`
- [ ] `after-a-cervical-cancer-diagnosis.txt`
- [ ] `after-a-colorectal-cancer-diagnosis.txt`
- [ ] `after-a-lung-cancer-diagnosis.txt`
- [ ] `after-a-prostate-cancer-diagnosis.txt`
- [ ] `checking-your-skin.txt`
- [ ] `chemotherapy-for-cancer.txt`
- [ ] `getting-help-for-nausea-and-vomiting.txt`
- [ ] `living-with-skin-cancer.txt`
- [ ] `skin-cancer-tests-and-procedures.txt`
- [ ] `skin-cancer-treatments.txt`

---

## Summary by Priority

| Priority | Category | Files | Notes |
|----------|----------|-------|-------|
| 1 | English sources | 22 | Critical - LLMs translate from these |
| 2a | Chinese translations | 22 | Poor quality extraction |
| 2b | Korean translations | 22 | Poor quality extraction |
| 2c | Arabic translations | 22 | Medium quality (RTL issues) |
| 3 | Spanish, Vietnamese, Russian, Tagalog, Haitian Creole | 110 | May still have column ordering issues |

**Total: 198 files**

## Tips for Manual Extraction

1. **Open PDF in Preview/Adobe** and copy-paste text
2. **For 2-column layouts**: Copy left column first, then right column
3. **Save as UTF-8** text files
4. **Check for**: Missing text, wrong order, garbled characters
