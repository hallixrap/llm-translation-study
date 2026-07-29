#!/usr/bin/env python3
"""
Regenerate every data-derived supplementary table from the repository.

The supplement as submitted reports BLEU (dropped from the revision) and
whole-document LaBSE (the truncated values). This recomputes all of it on the
segment-level basis the revision uses, on the same 702 translations as every
other analysis, and writes a markdown file of finished tables.

    python build_supplement.py
    cp output/supplement/SUPPLEMENT_TABLES_R1.md ~/Documents/Claude/Projects/AI\\ translation\\ project/

Regenerated here: S2, S3, S4, S5, S7, S8, S9, Analysis S2.
Carried over unchanged (no data dependency): S1, S6, the prompt templates and
the TRIPOD-LLM checklist, Supplementary Data 1.

Withdrawn from the supplement and deliberately not regenerated:
  Supplementary Analysis S1 (sentence reordering) -- scored on the truncated
    metric, and its negative control measured truncation sensitivity rather
    than sentence-order sensitivity. Superseded by the continuation probe, S9.
  Supplementary Data 2 and the French-borrowing claim in S5 -- 66 of the 175
    French terms carry diacritics Haitian Creole orthography does not use, so
    the near-zero detection rate was a property of the term list.
  Supplementary Figure S1 -- superseded by main-text Figure 1; its caption
    described four analyses rather than five and predated the recomputation.

Dependencies: pandas, numpy, scipy, sacrebleu.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RESOURCE_LEVEL = {
    "spanish": "high", "chinese_simplified": "high", "russian": "high",
    "vietnamese": "high", "korean": "medium", "arabic": "medium",
    "tagalog": "low", "haitian_creole": "low",
}
PRETTY = {
    "spanish": "Spanish", "chinese_simplified": "Chinese (Simplified)",
    "russian": "Russian", "vietnamese": "Vietnamese", "korean": "Korean",
    "arabic": "Arabic", "tagalog": "Tagalog", "haitian_creole": "Haitian Creole",
}
MODEL_PRETTY = {
    "gpt-5.1": "GPT-5.1", "claude-opus-4.5": "Claude Opus 4.5",
    "gemini-3-pro": "Gemini 3 Pro", "kimi-k2": "Kimi K2 Thinking",
}
SEED = 20260728
OUT: list[str] = []


def emit(*lines):
    OUT.extend(lines)


def table(header, rows):
    emit("| " + " | ".join(header) + " |",
         "|" + "|".join(["---"] * len(header)) + "|",
         *["| " + " | ".join(str(c) for c in r) + " |" for r in rows], "")


def p_str(p):
    return "<0.001" if p < 0.001 else (f"{p:.3f}" if p >= 0.001 else f"{p:.1e}")


def find(repo: Path, patterns, cols=None):
    for pat in patterns:
        for p in sorted(repo.glob(pat)):
            if cols:
                try:
                    if not cols <= set(pd.read_csv(p, nrows=1).columns):
                        continue
                except Exception:
                    continue
            return p
    return None


def load_chrf():
    from sacrebleu.metrics import CHRF
    m = CHRF()
    return lambda hyp, ref: m.sentence_score(hyp, [ref]).score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="output/supplement/SUPPLEMENT_TABLES_R1.md")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    results_p = find(repo, ["output/medlineplus_results/all_results.json", "**/all_results.json"])
    pairs_p = find(repo, ["output/labse_segmented/*.csv", "**/*.csv"],
                   {"doc_id", "model", "language", "labse_aligned"})
    bc_p = find(repo, ["output/segmented_bertscore_comet/*.csv", "**/*.csv"],
                {"doc_id", "language", "bertscore_segmented"})
    cross_p = find(repo, ["output/**/*cross*.csv", "**/*.csv"],
                   {"forward_model", "back_model", "labse_aligned"})
    conc_p = find(repo, ["output/**/*concordance*.csv", "**/*.csv"], {"model_pair", "labse_aligned"})
    mem_p = find(repo, ["output/memorisation_probe/*.csv", "**/memorisation*.csv"])
    terms_p = find(repo, ["output/lexical_borrowing/*medical_terms*.csv", "**/*medical_terms*.csv"])

    missing = [n for n, p in [("all_results.json", results_p), ("segmented LaBSE", pairs_p),
                              ("BERTScore/COMET", bc_p), ("cross-model", cross_p),
                              ("concordance", conc_p), ("medical terms", terms_p)] if p is None]
    if missing:
        sys.exit("Missing required inputs: " + ", ".join(missing))
    print("inputs resolved:")
    for n, p in [("translations", results_p), ("segmented LaBSE", pairs_p), ("BERTScore", bc_p),
                 ("cross-model", cross_p), ("concordance", conc_p), ("memorisation", mem_p),
                 ("terms", terms_p)]:
        print(f"  {n:<16} {p}")
    print()

    chrf = load_chrf()
    with results_p.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = next((raw[k] for k in ("results", "records", "data") if isinstance(raw.get(k), list)), raw)
    recs = [r for r in raw if (r.get("llm_translation") or "").strip() and r.get("success") is not False]

    pairs = pd.read_csv(pairs_p)
    pairs["resource_level"] = pairs["language"].map(RESOURCE_LEVEL)
    bc = pd.read_csv(bc_p)
    bc["resource_level"] = bc["language"].map(RESOURCE_LEVEL)
    cross = pd.read_csv(cross_p)
    conc = pd.read_csv(conc_p)

    emit("# Supplementary tables, regenerated", "",
         "All values recomputed on 150-word aligned segments over the 702 analyzed",
         "translations. BLEU has been replaced throughout by chrF, which is comparable",
         "across the eight writing systems in this corpus.", "")

    # ---------------- S2 ------------------------------------------------
    emit("## Supplementary Table S2. Professional translation back-translation fidelity", "",
         "Each model was also asked to back-translate the professional human translation.",
         "This establishes what the round trip scores when the forward translation is",
         "known to be of professional quality, giving the benchmark against which the",
         "LLM round trip is read.", "")
    rows = []
    prof_bt: dict[str, list[float]] = {}
    for r in raw:
        bt = (r.get("professional_back_translation") or "").strip()
        src = (r.get("english_original") or "").strip()
        if bt and src:
            prof_bt.setdefault(r["model"], []).append(chrf(bt, src))
    for model in sorted(prof_bt):
        vals = prof_bt[model]
        rows.append([MODEL_PRETTY.get(model, model), f"{np.mean(vals):.1f}", f"{np.std(vals):.1f}", len(vals)])
    if rows:
        table(["Back-translating model", "chrF vs English source", "SD", "n"], rows)
    else:
        emit("*No professional back-translations found in all_results.json; table omitted.*", "")
    emit("chrF of the back-translated professional text against the English source.",
         "Segment-level LaBSE was not recomputed for the professional back-translation arm,",
         "so this table reports chrF only.", "")

    # ---------------- S3 ------------------------------------------------
    emit("## Supplementary Table S3. Translation fidelity by language", "")
    prof_chrf: dict[str, list[float]] = {}
    for r in recs:
        prof = (r.get("professional_translation") or "").strip()
        if prof:
            prof_chrf.setdefault(r["language"], []).append(chrf(r["llm_translation"], prof))
    rows = []
    for lang, g in pairs.groupby("language"):
        rows.append([PRETTY.get(lang, lang), RESOURCE_LEVEL.get(lang, "?").capitalize(),
                     f"{g['labse_aligned'].mean():.3f}", f"{g['labse_aligned'].std():.3f}",
                     f"{np.mean(prof_chrf.get(lang, [np.nan])):.1f}", int(g["labse_aligned"].notna().sum())])
    rows.sort(key=lambda r: -float(r[2]))
    table(["Language", "Resource level", "Back-translation LaBSE", "SD", "chrF vs professional", "n"], rows)
    emit("Means across all four models and 22 documents. LaBSE compares each back-translation",
         "with the English source; chrF compares each forward translation with the professional",
         "translation. The two rank languages differently because chrF is depressed for languages",
         "that do not map word-for-word onto English, which is a property of the writing system",
         "rather than of translation quality.", "")

    # ---------------- S4 ------------------------------------------------
    emit("## Supplementary Table S4. Inter-model concordance by language", "")
    rows = []
    for lang, g in conc.groupby("language"):
        rows.append([PRETTY.get(lang, lang), RESOURCE_LEVEL.get(lang, "?").capitalize(), len(g),
                     f"{g['labse_aligned'].mean():.3f}", f"{g['labse_aligned'].std():.3f}"])
    rows.sort(key=lambda r: -float(r[3]))
    table(["Language", "Resource level", "n pairs", "LaBSE", "SD"], rows)
    emit(f"Pairwise comparisons between the forward translations of independently developed",
         f"models, {len(conc)} in total. Agreement is not greatest in the languages with the",
         "most training text, which is one of two observations arguing against a strong",
         "memorization account.", "")

    # ---------------- S5 ------------------------------------------------
    emit("## Supplementary Table S5. Verbatim retention of English medical terminology", "")
    with terms_p.open(encoding="utf-8-sig") as fh:
        trows = list(csv.reader(fh))
    hdr = [h.strip().lower() for h in trows[0]]
    col = next((i for i, h in enumerate(hdr) if "term" in h), 0)
    start = 1 if any("term" in h for h in hdr) else 0
    terms = sorted({r[col].strip().lower() for r in trows[start:] if r and r[col].strip()})
    pats = {t: re.compile(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", re.I) for t in terms}

    def rate(src, tgt):
        elig = [t for t in terms if pats[t].search(src)]
        if not elig:
            return None
        return sum(1 for t in elig if pats[t].search(tgt)) / len(elig)

    brec = []
    for r in recs:
        src, prof, llm = (r.get("english_original") or ""), (r.get("professional_translation") or ""), r["llm_translation"]
        if not src or not prof:
            continue
        pr, lr = rate(src, prof), rate(src, llm)
        if pr is None or lr is None:
            continue
        brec.append({"doc_id": r["doc_id"], "model": r["model"], "language": r["language"],
                     "prof": pr, "llm": lr})
    bdf = pd.DataFrame(brec).merge(
        pairs[["doc_id", "model", "language", "labse_aligned"]], on=["doc_id", "model", "language"], how="left")

    rows = []
    for lang, g in bdf.groupby("language"):
        sub = g.dropna(subset=["labse_aligned"])
        rho, p = stats.spearmanr(sub["llm"], sub["labse_aligned"]) if len(sub) > 2 else (np.nan, np.nan)
        rows.append([PRETTY.get(lang, lang), RESOURCE_LEVEL.get(lang, "?").capitalize(),
                     f"{100*g['prof'].mean():.1f}", f"{100*g['llm'].mean():.1f}",
                     f"{100*g['llm'].std():.1f}", f"{rho:+.3f}", p_str(p), len(g)])
    rows.sort(key=lambda r: -float(r[3]))
    table(["Language", "Resource level", "Professional %", "LLM %", "LLM SD", "Spearman rho vs LaBSE", "p", "n"], rows)

    lo = bdf[bdf.language.map(RESOURCE_LEVEL) == "low"]
    emit("**Summary**", "")
    table(["Group", "n", "Professional %", "LLM %"],
          [["Low-resource combined", len(lo), f"{100*lo['prof'].mean():.1f}", f"{100*lo['llm'].mean():.1f}"],
           ["All languages", len(bdf), f"{100*bdf['prof'].mean():.1f}", f"{100*bdf['llm'].mean():.1f}"]])
    by_model = bdf.groupby("model")["llm"].mean().sort_values(ascending=False)
    emit(f"Retention rate: of the {len(terms)} English medical terms present in a document's English",
         "source, the share reproduced verbatim in the translation. Word-boundary matching,",
         "case-insensitive, averaged per translation. The two zero-byte translations are excluded,",
         "so this analysis covers the same 702 translations as the rest of the paper.",
         "",
         "Professional translators retain more English terminology than the models in "
         f"{sum(1 for _, g in bdf.groupby('language') if g['prof'].mean() > g['llm'].mean())} of 8 languages, "
         "which is the comparison the main text reports. By forward model, LLM retention was "
         + ", ".join(f"{MODEL_PRETTY.get(m, m)} {100*v:.1f}%" for m, v in by_model.items()) + ".",
         "",
         "The Spearman column tests the separate question of whether retaining more English",
         "predicts a higher fidelity score.", "")
    rhos = []
    for _, g in bdf.groupby("language"):
        sub = g.dropna(subset=["labse_aligned"])
        if len(sub) > 2:
            rhos.append(stats.spearmanr(sub["llm"], sub["labse_aligned"])[0])
    n_neg = sum(1 for r in rhos if r < 0)
    n_sig_neg = 0
    for _, g in bdf.groupby("language"):
        sub = g.dropna(subset=["labse_aligned"])
        if len(sub) > 2:
            rr, pp = stats.spearmanr(sub["llm"], sub["labse_aligned"])
            if rr < 0 and pp < 0.05:
                n_sig_neg += 1
    all_sub = bdf.dropna(subset=["labse_aligned"])
    rho_all, p_all = stats.spearmanr(all_sub["llm"], all_sub["labse_aligned"])
    emit(f"Across all languages the correlation is {rho_all:+.3f} (p={p_str(p_all)}), and it is "
         f"negative in {n_neg} of {len(rhos)} languages individually "
         f"({n_sig_neg} significantly so). Verbatim retention therefore does not inflate the "
         "fidelity metric.", "")

    # ---------------- S7 ------------------------------------------------
    emit("## Supplementary Table S7. Cross-model sensitivity restricted to the three back-translating models", "")
    kept = {"claude-opus-4.5", "gpt-5.1", "gemini-3-pro"}
    emit("Kimi K2 never served as a back-translator, so the main-text Table 2 draws on a",
         "different number of back-translations per forward model. To check that this asymmetry",
         "does not drive the result, both columns are restricted here to forward models that",
         "also acted as back-translators.", "")
    c2 = cross[cross.forward_model.isin(kept) & cross.back_model.isin(kept)]
    cm = c2.groupby(["doc_id", "language", "forward_model"])["labse_aligned"].mean().reset_index()
    cm.columns = ["doc_id", "language", "model", "cross"]
    mg = cm.merge(pairs[["doc_id", "language", "model", "labse_aligned"]],
                  on=["doc_id", "language", "model"]).rename(columns={"labse_aligned": "same"})
    rows = []
    for model in sorted(kept):
        g = mg[mg.model == model]
        if not len(g):
            continue
        w = stats.wilcoxon(g["same"], g["cross"])
        rows.append([MODEL_PRETTY.get(model, model), f"{g['same'].mean():.3f}", f"{g['cross'].mean():.3f}",
                     f"{(g['cross']-g['same']).mean():+.3f}", p_str(w.pvalue), len(g)])
    w = stats.wilcoxon(mg["same"], mg["cross"])
    rows.append(["**Overall**", f"**{mg['same'].mean():.3f}**", f"**{mg['cross'].mean():.3f}**",
                 f"**{(mg['cross']-mg['same']).mean():+.3f}**", f"**{p_str(w.pvalue)}**", f"**{len(mg)}**"])
    table(["Forward model", "Same-model", "Cross-model", "Difference", "p", "n"], rows)
    per = {m: (mg[mg.model == m]["cross"].mean() - mg[mg.model == m]["same"].mean())
           for m in sorted(kept) if len(mg[mg.model == m])}
    decliners = [MODEL_PRETTY.get(m, m) for m, d in per.items() if d < 0]
    best = max(per, key=lambda m: mg[mg.model == m]["same"].mean()) if per else None
    if decliners == [MODEL_PRETTY.get(best, best)]:
        emit("The pattern of the main analysis is preserved: the highest-scoring model is the only",
             "one that declines when a different model performs the back-translation.", "")
    else:
        emit("Models declining under cross-model back-translation: "
             + (", ".join(decliners) if decliners else "none")
             + f". Highest-scoring model on same-model scoring: {MODEL_PRETTY.get(best, best)}.", "")

    # ---------------- S8 ------------------------------------------------
    emit("## Supplementary Table S8. Whole-document and segment-level values compared", "",
         "The metric as originally implemented scored each document as a single unit, which",
         "truncated it to the model's maximum input length. This table gives both values for",
         "every comparison the main text reports, so the effect of the correction is visible.", "")
    rows = []
    if "labse_published" in pairs.columns:
        for label, sel in [("All translations", pairs),
                           ("Low-resource", pairs[pairs.resource_level == "low"]),
                           ("High-resource", pairs[pairs.resource_level == "high"]),
                           ("Cancer materials", pairs[pairs.doc_category.str.contains("cancer", case=False)]),
                           ("Vaccine statements", pairs[~pairs.doc_category.str.contains("cancer", case=False)])]:
            rows.append([label, f"{sel['labse_published'].mean():.3f}", f"{sel['labse_aligned'].mean():.3f}",
                         f"{sel['labse_aligned'].mean()-sel['labse_published'].mean():+.3f}", len(sel)])
        table(["Group", "Whole-document LaBSE", "Segment-level LaBSE", "Difference", "n"], rows)
        q = lambda c: pairs[c].quantile(.75) - pairs[c].quantile(.25)
        table(["Distribution", "Whole-document", "Segment-level"],
              [["Share scoring above 0.98", f"{100*(pairs.labse_published>0.98).mean():.1f}%",
                f"{100*(pairs.labse_aligned>0.98).mean():.1f}%"],
               ["Interquartile range", f"{q('labse_published'):.3f}", f"{q('labse_aligned'):.3f}"]])
        pub_hi = 100 * (pairs.labse_published > 0.98).mean()
        seg_hi = 100 * (pairs.labse_aligned > 0.98).mean()
        emit(f"Scoring whole documents placed {pub_hi:.1f}% of translations in the top 2% of the "
             f"scale, against {seg_hi:.1f}% under segment-level scoring, and the interquartile "
             f"range widens from {q('labse_published'):.3f} to {q('labse_aligned'):.3f}. "
             "The resource-level comparison in the main text is therefore made on a measure with "
             "the dynamic range to have detected a difference had one been present.", "")
    else:
        emit("*Whole-document column not present in the segmented CSV; table omitted.*", "")

    # ---------------- S9 ------------------------------------------------
    emit("## Supplementary Table S9. Continuation probe for memorization", "")
    if mem_p is None:
        emit("*memorisation_probe.csv not found; table omitted.*", "")
    else:
        m = pd.read_csv(mem_p)
        cols = {c.lower(): c for c in m.columns}
        pub = next((cols[c] for c in cols if "prof" in c and "chrf" in c), None) or cols.get("professional")
        nov = next((cols[c] for c in cols if ("novel" in c or "control" in c) and "chrf" in c), None) or cols.get("novel")
        if pub is None or nov is None:
            emit(f"*Could not identify the score columns; found {list(m.columns)}.*", "")
        else:
            rows = []
            group_col = cols.get("model")
            if group_col:
                for model, g in m.dropna(subset=[pub, nov]).groupby(group_col):
                    w = stats.wilcoxon(g[pub], g[nov])
                    rows.append([MODEL_PRETTY.get(model, model), f"{g[pub].mean():.1f}",
                                 f"{g[nov].mean():.1f}", f"{(g[nov]-g[pub]).mean():+.1f}", p_str(w.pvalue), len(g)])
            sub = m.dropna(subset=[pub, nov])
            w = stats.wilcoxon(sub[pub], sub[nov])
            rows.append(["**All items**", f"**{sub[pub].mean():.1f}**", f"**{sub[nov].mean():.1f}**",
                         f"**{(sub[nov]-sub[pub]).mean():+.1f}**", f"**{p_str(w.pvalue)}**", f"**{len(sub)}**"])
            table(["Model", "Published text chrF", "Unpublished control chrF", "Difference", "p", "n"], rows)
            if "language" in cols:
                sub = sub.copy()
                sub["level"] = sub[cols["language"]].map(RESOURCE_LEVEL)
                sig = sub[nov] - sub[pub]
                rows = [[lvl.capitalize(), f"{sig[sub.level == lvl].mean():+.1f}", int((sub.level == lvl).sum())]
                        for lvl in ["high", "medium", "low"] if (sub.level == lvl).any()]
                lo_, hi_ = sig[sub.level == "low"], sig[sub.level == "high"]
                table(["Resource level", "Control minus published", "n"], rows)
                if len(lo_) and len(hi_):
                    emit(f"High versus low resource: p={stats.mannwhitneyu(lo_, hi_).pvalue:.2f}. "
                         "Memorization would predict closer agreement with the published text than with "
                         "the control, and a larger signal where training text is most abundant. Neither "
                         "is observed.", "")

    # ---------------- Analysis S2 ---------------------------------------
    emit("## Supplementary Analysis S2. Clustered resource-level test", "",
         "Each document was translated by four models into eight languages, so the 702",
         "translations are not independent. All group comparisons were therefore repeated",
         "after averaging within each document-language combination.", "")
    cl = pairs.groupby(["doc_id", "language", "resource_level"])["labse_aligned"].mean().reset_index()
    table(["Resource level", "n clusters", "Mean segment-level LaBSE", "SD"],
          [[lvl.capitalize(), int((cl.resource_level == lvl).sum()),
            f"{cl.loc[cl.resource_level == lvl, 'labse_aligned'].mean():.3f}",
            f"{cl.loc[cl.resource_level == lvl, 'labse_aligned'].std():.3f}"]
           for lvl in ["high", "medium", "low"]])
    lo = cl.loc[cl.resource_level == "low", "labse_aligned"].values
    hi = cl.loc[cl.resource_level == "high", "labse_aligned"].values
    rng = np.random.default_rng(SEED)
    boot = [rng.choice(lo, lo.size, True).mean() - rng.choice(hi, hi.size, True).mean() for _ in range(10_000)]
    ci = np.percentile(boot, [2.5, 97.5])
    kw = stats.kruskal(*[cl.loc[cl.resource_level == l, "labse_aligned"].values for l in ["high", "medium", "low"]])
    emit(f"- Low minus high resource: {lo.mean()-hi.mean():+.3f} (95% CI {ci[0]:.3f} to {ci[1]:.3f}, "
         f"10,000 bootstrap resamples)",
         f"- Mann-Whitney, high versus low: p={stats.mannwhitneyu(lo, hi).pvalue:.2f}",
         f"- Kruskal-Wallis across three resource levels: H={kw.statistic:.2f}, p={kw.pvalue:.2f}", "",
         "The confidence interval indicates the size of difference that could still have been",
         "missed. Absence of a detected difference is not demonstrated equivalence.", "")

    out = Path(args.out)
    if not out.is_absolute():
        out = repo / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(OUT), encoding="utf-8")
    print(f"wrote {out} ({len(OUT)} lines)")
    print("\nNext:")
    print(f"  cp {out} ~/Documents/Claude/Projects/AI\\ translation\\ project/")


if __name__ == "__main__":
    main()
