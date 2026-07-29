#!/usr/bin/env python3
"""
Pin down the borrowing-rate definition.

The manuscript reports professional 33.2% vs LLM 27.1% overall, and Tagalog
professional 60.8% vs LLM 68.2%. Recomputing from source gives slightly
different values, so the definition used originally must differ in one of three
ways. This prints the rate under all eight combinations and marks which one
reproduces the published figures.

    source-present terms   terms from the 213-term list that appear in the
                           English original of that document
    retained               those terms that also appear in the translation

    match     substring (plain "in" test) or word-boundary (regex)
    records   all 704, or the 702 with a non-empty LLM translation
    average   macro (mean of per-record rates) or micro (total retained
              over total eligible, corpus-wide)

Run from the repository root:

    python diagnose_borrowing.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

TARGETS = {"prof_all": 33.2, "llm_all": 27.1, "prof_tl": 60.8, "llm_tl": 68.2}


def load_terms(path: Path):
    with path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    header = [h.strip().lower() for h in rows[0]]
    col = next((i for i, h in enumerate(header) if "term" in h), 0)
    start = 1 if any("term" in h for h in header) else 0
    return sorted({r[col].strip().lower() for r in rows[start:] if r and r[col].strip()})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="output/medlineplus_results/all_results.json")
    ap.add_argument("--terms", default="output/lexical_borrowing/supplementary_data_1_medical_terms.csv")
    args = ap.parse_args()

    rp, tp = Path(args.results), Path(args.terms)
    if not rp.exists() or not tp.exists():
        sys.exit(f"Missing input: {rp if not rp.exists() else tp}")

    with rp.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = next((raw[k] for k in ("results", "records", "data") if isinstance(raw.get(k), list)), raw)

    terms = load_terms(tp)
    print(f"{len(raw)} records, {len(terms)} terms\n")

    empties = [r for r in raw if not (r.get("llm_translation") or "").strip()]
    print(f"records with an empty LLM translation: {len(empties)}")
    for r in empties:
        print(f"   {r['doc_id']:<40} {r['model']:<18} {r['language']:<18} success={r.get('success')}")
    print()

    pats = {t: re.compile(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", re.I) for t in terms}

    def counts(source: str, target: str, boundary: bool):
        s, t = source.lower(), target.lower()
        if boundary:
            elig = [x for x in terms if pats[x].search(s)]
            kept = sum(1 for x in elig if pats[x].search(t))
        else:
            elig = [x for x in terms if x in s]
            kept = sum(1 for x in elig if x in t)
        return kept, len(elig)

    print(f"{'match':<16}{'records':<12}{'average':<8}"
          f"{'prof all':>10}{'LLM all':>10}{'prof TL':>10}{'LLM TL':>10}   matches published")
    print("-" * 92)

    for boundary in (False, True):
        for only_usable in (False, True):
            recs = [r for r in raw if not only_usable or (r.get("llm_translation") or "").strip()]
            acc = {k: {"rates": [], "kept": 0, "elig": 0} for k in TARGETS}
            for r in recs:
                src = r.get("english_original") or ""
                prof = r.get("professional_translation") or ""
                llm = r.get("llm_translation") or ""
                if not src or not prof:
                    continue
                pk, pe = counts(src, prof, boundary)
                lk, le = counts(src, llm, boundary)
                if pe == 0 or le == 0:
                    continue
                for key, (k_, e_) in (("prof_all", (pk, pe)), ("llm_all", (lk, le))):
                    acc[key]["rates"].append(k_ / e_)
                    acc[key]["kept"] += k_
                    acc[key]["elig"] += e_
                if r["language"] == "tagalog":
                    for key, (k_, e_) in (("prof_tl", (pk, pe)), ("llm_tl", (lk, le))):
                        acc[key]["rates"].append(k_ / e_)
                        acc[key]["kept"] += k_
                        acc[key]["elig"] += e_

            for avg in ("macro", "micro"):
                vals = {}
                for key, a in acc.items():
                    if not a["rates"]:
                        vals[key] = float("nan")
                    elif avg == "macro":
                        vals[key] = 100 * float(np.mean(a["rates"]))
                    else:
                        vals[key] = 100 * a["kept"] / a["elig"] if a["elig"] else float("nan")
                hits = sum(1 for k, target in TARGETS.items() if abs(vals[k] - target) < 0.05)
                mark = {4: "<-- ALL FOUR", 3: "three of four", 2: "two of four"}.get(hits, "")
                print(f"{'substring' if not boundary else 'word-boundary':<16}"
                      f"{('all ' + str(len(recs))) if not only_usable else ('usable ' + str(len(recs))):<12}{avg:<8}"
                      f"{vals['prof_all']:>9.1f}%{vals['llm_all']:>9.1f}%"
                      f"{vals['prof_tl']:>9.1f}%{vals['llm_tl']:>9.1f}%   {mark}")

    print("\npublished figures:".ljust(36)
          + f"{TARGETS['prof_all']:>9.1f}%{TARGETS['llm_all']:>9.1f}%"
            f"{TARGETS['prof_tl']:>9.1f}%{TARGETS['llm_tl']:>9.1f}%")


if __name__ == "__main__":
    main()
