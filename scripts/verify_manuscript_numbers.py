#!/usr/bin/env python3
"""
Audit every number in the JGIM revision against the repository data.

This recomputes each quantitative claim in the manuscript from source and prints
PASS, FAIL, or SKIP (input file not found) for each one. Nothing is taken on
trust from an earlier analysis session.

Run from the repository root:

    python verify_manuscript_numbers.py

Optional flags let you point at files that live somewhere unexpected:

    --repo PATH            repository root (default: current directory)
    --results PATH         all_results.json
    --segmented PATH       segmented LaBSE CSV (needs a labse_aligned column)
    --bertscore PATH       segmented BERTScore/COMET CSV
    --cross PATH           cross-model CSV (needs forward_model, back_model)
    --concordance PATH     inter-model concordance CSV
    --memorisation PATH    memorisation_probe.csv
    --terms PATH           supplementary_data_1_medical_terms.csv

Dependencies: pandas, numpy, scipy, sacrebleu. textstat is optional and only
needed for the readability checks; without it those two rows report SKIP.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BOOTSTRAP_N = 10_000
SEED = 20260728

RESOURCE_LEVEL = {
    "spanish": "high", "chinese_simplified": "high", "russian": "high",
    "vietnamese": "high", "korean": "medium", "arabic": "medium",
    "tagalog": "low", "haitian_creole": "low",
}

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""

RESULTS: list[tuple[str, str, str, str, str]] = []


def check(label: str, manuscript, computed, tol=None, note=""):
    """Record one comparison. tol=None means the values must match as strings."""
    if computed is None:
        RESULTS.append((label, str(manuscript), "-", "SKIP", note))
        return
    if tol is None:
        ok = str(manuscript) == str(computed)
    else:
        ok = abs(float(manuscript) - float(computed)) <= tol + 1e-9  # guard float noise
    RESULTS.append((label, str(manuscript), str(computed), "PASS" if ok else "FAIL", note))


def skip(label: str, manuscript, why: str):
    RESULTS.append((label, str(manuscript), "-", "SKIP", why))


def fmt(x, nd=3):
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


# ---------------------------------------------------------------- discovery
def find_file(repo: Path, explicit, candidates, required_cols=None):
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for pattern in candidates:
        for p in sorted(repo.glob(pattern)):
            if required_cols:
                try:
                    cols = set(pd.read_csv(p, nrows=1).columns)
                except Exception:
                    continue
                if not required_cols <= cols:
                    continue
            return p
    return None


def load_chrf():
    try:
        from sacrebleu.metrics import CHRF
    except ImportError:
        return None
    metric = CHRF()
    return lambda hyp, ref: metric.sentence_score(hyp, [ref]).score


def boot_ci(x, y, n=BOOTSTRAP_N, seed=SEED):
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x), np.asarray(y)
    d = [rng.choice(x, x.size, True).mean() - rng.choice(y, y.size, True).mean() for _ in range(n)]
    return np.percentile(d, [2.5, 97.5])


# ---------------------------------------------------------------- checks
def check_segmented(path: Path):
    """Primary outcome: segment-level LaBSE, back-translation against source."""
    if path is None:
        for lbl, val in [
            ("Resource level, low", 0.885), ("Resource level, high", 0.880),
            ("Resource level, difference", 0.005), ("Resource level, p", 0.57),
            ("Document type, cancer", 0.934), ("Document type, vaccine", 0.832),
            ("Document type, difference", 0.102),
            ("Model, Claude Opus 4.5", 0.941), ("Model, GPT-5.1", 0.879),
            ("Model, Kimi K2", 0.861), ("Model, Gemini 3 Pro", 0.853),
            ("Ceiling, >0.98 whole-document", "54.1%"), ("Ceiling, >0.98 segmented", "10.5%"),
            ("Stale references, documents", 10), ("Stale references, Arabic", 10),
            ("Stale references, Spanish", 0),
        ]:
            skip(lbl, val, "segmented LaBSE CSV not found")
        return None

    p = pd.read_csv(path)
    p["resource_level"] = p["language"].map(RESOURCE_LEVEL).fillna(p.get("resource_level"))
    check("Pairs analyzed", 702, int(p["labse_aligned"].notna().sum()))

    cl = p.groupby(["doc_id", "language", "resource_level", "doc_category"])["labse_aligned"].mean().reset_index()
    lo = cl.loc[cl.resource_level == "low", "labse_aligned"].values
    hi = cl.loc[cl.resource_level == "high", "labse_aligned"].values
    ci = boot_ci(lo, hi)
    check("Resource level, low", 0.885, round(lo.mean(), 3), 0.0005)
    check("Resource level, high", 0.880, round(hi.mean(), 3), 0.0005)
    check("Resource level, difference", 0.005, round(lo.mean() - hi.mean(), 3), 0.0005)
    check("Resource level, CI lower", -0.019, round(ci[0], 3), 0.002, "bootstrap, seed-sensitive in 3rd dp")
    check("Resource level, CI upper", 0.029, round(ci[1], 3), 0.002, "bootstrap, seed-sensitive in 3rd dp")
    check("Resource level, p", 0.57, round(stats.mannwhitneyu(lo, hi).pvalue, 2), 0.005)

    cat = "cancer"
    ca = cl.loc[cl.doc_category.str.contains(cat, case=False), "labse_aligned"].values
    va = cl.loc[~cl.doc_category.str.contains(cat, case=False), "labse_aligned"].values
    dci = boot_ci(ca, va)
    check("Document type, cancer", 0.934, round(ca.mean(), 3), 0.0005)
    check("Document type, vaccine", 0.832, round(va.mean(), 3), 0.0005)
    check("Document type, difference", 0.102, round(ca.mean() - va.mean(), 3), 0.0005)
    check("Document type, CI lower", 0.090, round(dci[0], 3), 0.002)
    check("Document type, CI upper", 0.114, round(dci[1], 3), 0.002)
    check("Document type, p<0.001", True, bool(stats.mannwhitneyu(ca, va).pvalue < 0.001))

    for lang, val in [("tagalog", 0.892), ("haitian_creole", 0.878), ("spanish", 0.891), ("russian", 0.875)]:
        sub = p.loc[p.language == lang, "labse_aligned"]
        check(f"Language mean, {lang}", val, round(sub.mean(), 3), 0.0005)

    means = p.groupby("model")["labse_aligned"].mean().round(3)
    for model, val in [("claude-opus-4.5", 0.941), ("gpt-5.1", 0.879), ("kimi-k2", 0.861), ("gemini-3-pro", 0.853)]:
        check(f"Model mean, {model}", val, means.get(model), 0.0005)
    groups = [g["labse_aligned"].dropna().values for _, g in p.groupby("model")]
    check("Model comparison, p<0.001", True, bool(stats.kruskal(*groups).pvalue < 0.001))

    if "labse_published" in p.columns:
        check("Ceiling, >0.98 whole-document", "54.1%", f"{100*(p.labse_published>0.98).mean():.1f}%")
        check("Ceiling, IQR whole-document", 0.085,
              round(p.labse_published.quantile(.75) - p.labse_published.quantile(.25), 3), 0.0005)
    check("Ceiling, >0.98 segmented", "10.5%", f"{100*(p.labse_aligned>0.98).mean():.1f}%")
    check("Ceiling, IQR segmented", 0.155,
          round(p.labse_aligned.quantile(.75) - p.labse_aligned.quantile(.25), 3), 0.0005)

    if "stale_reference" in p.columns:
        st = p[p.stale_reference.astype(bool)]
        check("Stale references, documents", 10, st.doc_id.nunique())
        check("Stale references, all vaccine", True, bool(set(st.doc_category.unique()) == {"immunize"}))
        per = st.groupby("language")["doc_id"].nunique()
        check("Stale references, Arabic", 10, int(per.get("arabic", 0)))
        check("Stale references, Spanish", 0, int(per.get("spanish", 0)))
    return p


def check_bertscore(path: Path):
    if path is None:
        for lbl, val in [("BERTScore vs source, low", 0.925), ("BERTScore vs source, high", 0.921),
                         ("BERTScore vs professional, low", 0.798), ("BERTScore vs professional, high", 0.799),
                         ("BERTScore, document type cancer", 0.856), ("BERTScore, document type vaccine", 0.749)]:
            skip(lbl, val, "segmented BERTScore CSV not found")
        return
    b = pd.read_csv(path)
    b["resource_level"] = b["language"].map(RESOURCE_LEVEL).fillna(b.get("resource_level"))

    for col, lo_v, hi_v, p_v, name in [
        ("backtrans_bertscore_segmented", 0.925, 0.921, 0.25, "vs source"),
        ("bertscore_segmented", 0.798, 0.799, 0.98, "vs professional"),
    ]:
        if col not in b.columns:
            skip(f"BERTScore {name}", f"{lo_v} / {hi_v}", f"column {col} missing")
            continue
        cl = b.groupby(["doc_id", "language", "resource_level"])[col].mean().reset_index().dropna(subset=[col])
        lo = cl.loc[cl.resource_level == "low", col].values
        hi = cl.loc[cl.resource_level == "high", col].values
        check(f"BERTScore {name}, low", lo_v, round(lo.mean(), 3), 0.0005)
        check(f"BERTScore {name}, high", hi_v, round(hi.mean(), 3), 0.0005)
        check(f"BERTScore {name}, p", p_v, round(stats.mannwhitneyu(lo, hi).pvalue, 2), 0.015)

    if "bertscore_segmented" in b.columns:
        cl = b.groupby(["doc_id", "language", "doc_category"])["bertscore_segmented"].mean().reset_index()
        ca = cl.loc[cl.doc_category.str.contains("cancer", case=False), "bertscore_segmented"].values
        va = cl.loc[~cl.doc_category.str.contains("cancer", case=False), "bertscore_segmented"].values
        check("BERTScore, document type cancer", 0.856, round(ca.mean(), 3), 0.0005)
        check("BERTScore, document type vaccine", 0.749, round(va.mean(), 3), 0.0005)
        check("BERTScore, document type p<0.001", True, bool(stats.mannwhitneyu(ca, va).pvalue < 0.001))


def check_cross(cross_path: Path, seg: pd.DataFrame):
    expected = {"claude-opus-4.5": (0.940, 0.915, -0.025), "gpt-5.1": (0.880, 0.883, 0.003),
                "kimi-k2": (0.861, 0.874, 0.014), "gemini-3-pro": (0.853, 0.859, 0.006)}
    if cross_path is None or seg is None:
        for m, (s, c, d) in expected.items():
            skip(f"Table 2, {m}", f"{s} / {c} / {d:+}", "cross-model CSV or segmented CSV not found")
        return
    c = pd.read_csv(cross_path)
    check("Cross-model pairs analyzed", 1550, len(c))
    check("Kimi never a back-translator", True, bool("kimi-k2" not in set(c.back_model)))

    cm = c.groupby(["doc_id", "language", "forward_model"])["labse_aligned"].mean().reset_index()
    cm.columns = ["doc_id", "language", "model", "cross"]
    mg = cm.merge(seg[["doc_id", "language", "model", "labse_aligned"]], on=["doc_id", "language", "model"])
    mg = mg.rename(columns={"labse_aligned": "same"})
    check("Table 2, matched combinations", 699, len(mg))

    for model, (s_v, c_v, d_v) in expected.items():
        g = mg[mg.model == model]
        check(f"Table 2 same-model, {model}", s_v, round(g["same"].mean(), 3), 0.0005)
        check(f"Table 2 cross-model, {model}", c_v, round(g["cross"].mean(), 3), 0.0005)
        check(f"Table 2 difference, {model}", d_v, round((g["cross"] - g["same"]).mean(), 3), 0.0005)

    check("Table 2 overall same-model", 0.883, round(mg["same"].mean(), 3), 0.0005)
    check("Table 2 overall cross-model", 0.883, round(mg["cross"].mean(), 3), 0.0005)

    cl_, gp = mg[mg.model == "claude-opus-4.5"], mg[mg.model == "gpt-5.1"]
    lead_s = cl_["same"].mean() - gp["same"].mean()
    lead_c = cl_["cross"].mean() - gp["cross"].mean()
    check("Claude lead, same-model", 0.060, round(lead_s, 3), 0.0005)
    check("Claude lead, cross-model", 0.032, round(lead_c, 3), 0.0005)
    check("Lead reduction is near half", True, bool(0.40 <= (lead_s - lead_c) / lead_s <= 0.55),
          note=f"actual {100*(lead_s-lead_c)/lead_s:.0f}%")
    check("Claude decline p<0.001", True,
          bool(stats.wilcoxon(cl_["same"], cl_["cross"]).pvalue < 0.001))


def check_concordance(path: Path):
    if path is None:
        skip("Concordance, mean LaBSE", 0.891, "concordance CSV not found")
        skip("Concordance, comparisons", 1047, "concordance CSV not found")
        return
    cn = pd.read_csv(path)
    check("Concordance, comparisons", 1047, len(cn))
    check("Concordance, mean LaBSE", 0.891, round(cn["labse_aligned"].mean(), 3), 0.0005)


def check_translations(results_path: Path, terms_path: Path, chrf):
    """Everything computed from the raw translations: chrF gap, borrowing, readability."""
    labels_chrf = ["chrF gap, model-model", "chrF gap, model-professional", "chrF gap, difference",
                   "chrF gap, positive in all eight languages", "Memorisation reference point"]
    labels_borrow = ["Borrowing, term count", "Borrowing, professional", "Borrowing, LLM",
                     "Borrowing, Tagalog professional", "Borrowing, Tagalog LLM"]
    labels_read = ["Readability, cancer FK grade", "Readability, vaccine FK grade",
                   "Polysyllabic, cancer", "Polysyllabic, vaccine"]

    if results_path is None:
        for lbl in labels_chrf + labels_borrow + labels_read:
            skip(lbl, "-", "all_results.json not found")
        return

    with results_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = next((raw[k] for k in ("results", "records", "data") if isinstance(raw.get(k), list)), raw)

    check("Pairs attempted", 704, len(raw))
    recs = [r for r in raw if r.get("success") is not False and (r.get("llm_translation") or "").strip()]

    # ---- chrF concordance gap -------------------------------------
    if chrf is None:
        for lbl in labels_chrf:
            skip(lbl, "-", "sacrebleu not installed")
    else:
        cells: dict[tuple[str, str], list[dict]] = {}
        for r in recs:
            cells.setdefault((r["doc_id"], r["language"]), []).append(r)
        per_lang: dict[str, list[tuple[float, float]]] = {}
        mm_all, mp_all = [], []
        for (doc_id, language), group in cells.items():
            prof = next((g.get("professional_translation") or "" for g in group if (g.get("professional_translation") or "").strip()), "")
            if not prof or len(group) < 2:
                continue
            mp = [chrf(g["llm_translation"], prof) for g in group]
            mm = [(chrf(a["llm_translation"], b["llm_translation"]) + chrf(b["llm_translation"], a["llm_translation"])) / 2
                  for a, b in combinations(sorted(group, key=lambda g: g["model"]), 2)]
            per_lang.setdefault(language, []).append((float(np.mean(mm)), float(np.mean(mp))))
            mm_all.append(float(np.mean(mm)))
            mp_all.append(float(np.mean(mp)))
        check("chrF gap, model-model", 75.0, round(float(np.mean(mm_all)), 1), 0.35)
        check("chrF gap, model-professional", 62.8, round(float(np.mean(mp_all)), 1), 0.35)
        check("chrF gap, difference", 12.1, round(float(np.mean(mm_all)) - float(np.mean(mp_all)), 1), 0.35)
        all_pos = all(np.mean([a for a, _ in v]) > np.mean([b for _, b in v]) for v in per_lang.values())
        check("chrF gap, positive in all eight languages", True, bool(all_pos and len(per_lang) == 8))
        check("Memorisation reference point", 63, round(float(np.mean(mp_all))), 0.6,
              "the score a model gets translating a document placed in front of it")

    # ---- lexical borrowing ----------------------------------------
    if terms_path is None:
        for lbl in labels_borrow:
            skip(lbl, "-", "medical terms CSV not found")
    else:
        with terms_path.open(encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
        header = [h.strip().lower() for h in rows[0]]
        col = next((i for i, h in enumerate(header) if "term" in h), 0)
        start = 1 if any("term" in h for h in header) else 0
        terms = sorted({r[col].strip().lower() for r in rows[start:] if r and r[col].strip()})
        check("Borrowing, term count", 213, len(terms))

        pats = {t: re.compile(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", re.I) for t in terms}

        def rate(source: str, target: str):
            eligible = [t for t in terms if pats[t].search(source)]
            if not eligible:
                return None
            kept = sum(1 for t in eligible if pats[t].search(target))
            return kept / len(eligible)

        prof_rates, llm_rates = [], []
        tl_prof, tl_llm = [], []
        for r in recs:
            src = r.get("english_original") or ""
            prof = r.get("professional_translation") or ""
            llm = r.get("llm_translation") or ""
            if not src or not prof:
                continue
            pr, lr = rate(src, prof), rate(src, llm)
            if pr is None or lr is None:
                continue
            prof_rates.append(pr)
            llm_rates.append(lr)
            if r["language"] == "tagalog":
                tl_prof.append(pr)
                tl_llm.append(lr)
        if prof_rates:
            check("Borrowing, professional", "33.1%", f"{100*np.mean(prof_rates):.1f}%", None,
                  "word-boundary match, macro-average over the 702 usable translations")
            check("Borrowing, LLM", "27.3%", f"{100*np.mean(llm_rates):.1f}%")
            check("Borrowing, Tagalog professional", "60.8%", f"{100*np.mean(tl_prof):.1f}%")
            check("Borrowing, Tagalog LLM", "69.0%", f"{100*np.mean(tl_llm):.1f}%")
            check("Borrowing, professional exceeds LLM", True, bool(np.mean(prof_rates) > np.mean(llm_rates)))

    # ---- readability of the source documents ----------------------
    try:
        import textstat
    except ImportError:
        for lbl in labels_read:
            skip(lbl, "-", "textstat not installed (pip install textstat)")
        return
    docs = {}
    for r in recs:
        if r.get("english_original"):
            docs.setdefault(r["doc_id"], r["english_original"])
    grades, poly = {}, {}
    for doc_id, text in docs.items():
        cat = doc_id.split("/")[0]
        grades.setdefault(cat, []).append(textstat.flesch_kincaid_grade(text))
        words = re.findall(r"[A-Za-z']+", text)
        if words:
            poly.setdefault(cat, []).append(
                sum(1 for w in words if textstat.syllable_count(w) >= 3) / len(words))
    check("Source documents", 22, len(docs))
    check("Readability, cancer FK grade", 6.4, round(float(np.mean(grades.get("cancer", [np.nan]))), 1), 0.3)
    check("Readability, vaccine FK grade", 10.7, round(float(np.mean(grades.get("immunize", [np.nan]))), 1), 0.3)
    if "cancer" in grades and "immunize" in grades:
        check("Readability, p<0.001", True,
              bool(stats.mannwhitneyu(grades["cancer"], grades["immunize"]).pvalue < 0.001))
    check("Polysyllabic, cancer", "7.1%", f"{100*np.mean(poly.get('cancer',[np.nan])):.1f}%", None,
          "syllable heuristics vary between libraries")
    check("Polysyllabic, vaccine", "17.3%", f"{100*np.mean(poly.get('immunize',[np.nan])):.1f}%", None,
          "syllable heuristics vary between libraries")


def check_memorisation(path: Path):
    labels = [("Memorisation, matched items", 317), ("Memorisation, published chrF", 39.3),
              ("Memorisation, control chrF", 42.1), ("Memorisation, p<0.001", True),
              ("Memorisation, resource-level p", 0.23)]
    if path is None:
        for lbl, val in labels:
            skip(lbl, val, "memorisation_probe.csv not found")
        return
    m = pd.read_csv(path)
    cols = {c.lower(): c for c in m.columns}
    pub = next((cols[c] for c in cols if "prof" in c and "chrf" in c), None) or \
          next((cols[c] for c in cols if c in ("professional", "published", "prof_chrf")), None)
    nov = next((cols[c] for c in cols if ("novel" in c or "control" in c) and "chrf" in c), None) or \
          next((cols[c] for c in cols if c in ("novel", "control", "novel_chrf")), None)
    if pub is None or nov is None:
        skip("Memorisation, matched items", 317,
             f"could not identify the score columns in {path.name}; columns are {list(m.columns)}")
        return
    sub = m[[pub, nov] + ([cols["language"]] if "language" in cols else [])].dropna()
    check("Memorisation, matched items", 317, len(sub))
    check("Memorisation, published chrF", 39.3, round(sub[pub].mean(), 1), 0.15)
    check("Memorisation, control chrF", 42.1, round(sub[nov].mean(), 1), 0.15)
    check("Memorisation, control exceeds published", True, bool(sub[nov].mean() > sub[pub].mean()))
    check("Memorisation, p<0.001", True, bool(stats.wilcoxon(sub[pub], sub[nov]).pvalue < 0.001))
    if "language" in cols:
        sub = sub.copy()
        sub["level"] = sub[cols["language"]].map(RESOURCE_LEVEL)
        sig = sub[nov] - sub[pub]
        lo = sig[sub.level == "low"]
        hi = sig[sub.level == "high"]
        if len(lo) and len(hi):
            check("Memorisation, resource-level p", 0.23,
                  round(stats.mannwhitneyu(lo, hi).pvalue, 2), 0.05)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    for flag in ("results", "segmented", "bertscore", "cross", "concordance", "memorisation", "terms"):
        ap.add_argument(f"--{flag}")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    results = find_file(repo, args.results, ["output/medlineplus_results/all_results.json", "**/all_results.json"])
    segmented = find_file(repo, args.segmented, ["output/labse_segmented/*.csv", "**/*.csv"],
                          {"doc_id", "model", "language", "labse_aligned"})
    bertscore = find_file(repo, args.bertscore, ["output/segmented_bertscore_comet/*.csv", "**/*.csv"],
                          {"doc_id", "language", "bertscore_segmented"})
    cross = find_file(repo, args.cross, ["output/**/*cross*.csv", "**/*.csv"],
                      {"forward_model", "back_model", "labse_aligned"})
    concordance = find_file(repo, args.concordance, ["output/**/*concordance*.csv", "**/*.csv"],
                            {"model_pair", "labse_aligned"})
    memorisation = find_file(repo, args.memorisation, ["output/memorisation_probe/*.csv", "**/memorisation*.csv"])
    terms = find_file(repo, args.terms, ["output/lexical_borrowing/*medical_terms*.csv", "**/*medical_terms*.csv"])

    print(f"repository: {repo}\n")
    print("inputs")
    for name, p in [("translations", results), ("segmented LaBSE", segmented), ("BERTScore/COMET", bertscore),
                    ("cross-model", cross), ("concordance", concordance),
                    ("memorisation", memorisation), ("medical terms", terms)]:
        mark = f"{GREEN}found{RESET}" if p else f"{YELLOW}missing{RESET}"
        print(f"  {name:<18} {mark:<20} {p.relative_to(repo) if p and repo in p.parents else (p or '')}")
    print()

    chrf = load_chrf()
    if chrf is None:
        print(f"{YELLOW}sacrebleu is not installed; chrF checks will be skipped.{RESET}\n")

    seg = check_segmented(segmented)
    check_bertscore(bertscore)
    check_cross(cross, seg)
    check_concordance(concordance)
    check_translations(results, terms, chrf)
    check_memorisation(memorisation)

    # ---- report ---------------------------------------------------
    w = max(len(r[0]) for r in RESULTS) + 2
    print(f"{'claim':<{w}} {'manuscript':>12} {'computed':>12}   result")
    print("-" * (w + 40))
    for label, expected, computed, verdict, note in RESULTS:
        colour = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}[verdict]
        print(f"{label:<{w}} {expected:>12} {computed:>12}   {colour}{verdict}{RESET}"
              + (f"  {DIM}{note}{RESET}" if note and verdict != "PASS" else ""))

    n_pass = sum(1 for r in RESULTS if r[3] == "PASS")
    n_fail = sum(1 for r in RESULTS if r[3] == "FAIL")
    n_skip = sum(1 for r in RESULTS if r[3] == "SKIP")
    print("-" * (w + 40))
    print(f"{n_pass} passed, {n_fail} failed, {n_skip} skipped, {len(RESULTS)} claims checked")
    if n_fail:
        print(f"\n{RED}Claims that did not reproduce:{RESET}")
        for label, expected, computed, verdict, note in RESULTS:
            if verdict == "FAIL":
                print(f"  {label}: manuscript says {expected}, data gives {computed}"
                      + (f" ({note})" if note else ""))
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
