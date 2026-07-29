#!/usr/bin/env python3
"""
Recompute the inter-model concordance claim in chrF terms.

The manuscript states that two models translating the same document agreed with
each other more closely than either agreed with the professional translation, by
about 12 chrF points, in all eight languages. That number was computed ad hoc in
an earlier session and is not stored in any repository output file, so this
script recomputes it from the raw translations and prints the exact figures the
manuscript should quote.

It computes two quantities from output/medlineplus_results/all_results.json:

  model vs model         chrF between the forward translations of each pair of
                         models, for the same document and language
  model vs professional  chrF between each model's forward translation and the
                         professional translation of the same document

and reports the gap between them, overall, per language, and as a paired test
across (document, language) cells.

Usage, from the repository root:

    python recompute_concordance_chrf.py
    python recompute_concordance_chrf.py --results path/to/all_results.json

Requires sacrebleu, which the repository already uses for chrF.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from itertools import combinations
from pathlib import Path

RESOURCE_LEVEL = {
    "spanish": "high",
    "chinese_simplified": "high",
    "russian": "high",
    "vietnamese": "high",
    "korean": "medium",
    "arabic": "medium",
    "tagalog": "low",
    "haitian_creole": "low",
}


def load_chrf():
    try:
        from sacrebleu.metrics import CHRF
    except ImportError:
        sys.exit(
            "sacrebleu is not installed in this environment.\n"
            "Activate the repository virtual environment first, or run:\n"
            "    pip install sacrebleu"
        )
    # sacrebleu defaults: char_order=6, word_order=0, beta=2. These are the
    # settings the repository's own chrF calls use.
    metric = CHRF()

    def score(hypothesis: str, reference: str) -> float:
        return metric.sentence_score(hypothesis, [reference]).score

    return score


def load_records(path: Path):
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        for key in ("results", "records", "data"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    if not isinstance(data, list):
        sys.exit(f"Expected a list of records in {path}, found {type(data).__name__}.")

    kept, skipped = [], 0
    for rec in data:
        if rec.get("success") is False:
            skipped += 1
            continue
        llm = (rec.get("llm_translation") or "").strip()
        prof = (rec.get("professional_translation") or "").strip()
        if not llm:
            skipped += 1
            continue
        kept.append(
            {
                "doc_id": rec["doc_id"],
                "model": rec["model"],
                "language": rec["language"],
                "llm_translation": llm,
                "professional_translation": prof,
            }
        )
    return kept, skipped


def mean(xs):
    return statistics.fmean(xs) if xs else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results",
        default="output/medlineplus_results/all_results.json",
        help="path to all_results.json (default: %(default)s)",
    )
    ap.add_argument(
        "--out",
        default="output/inter_model_concordance/concordance_chrf.csv",
        help="where to write the per-cell CSV (default: %(default)s)",
    )
    args = ap.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        sys.exit(
            f"Could not find {results_path}.\n"
            "Run this from the repository root, or pass --results with the full path."
        )

    chrf = load_chrf()
    records, skipped = load_records(results_path)
    print(f"Loaded {len(records)} usable translations ({skipped} skipped).\n")

    # Group by (doc_id, language)
    cells: dict[tuple[str, str], list[dict]] = {}
    for rec in records:
        cells.setdefault((rec["doc_id"], rec["language"]), []).append(rec)

    rows = []
    n_pairs = 0
    n_prof = 0
    for (doc_id, language), group in sorted(cells.items()):
        # model vs professional
        prof_scores = []
        prof_text = next((g["professional_translation"] for g in group if g["professional_translation"]), "")
        if prof_text:
            for g in group:
                prof_scores.append(chrf(g["llm_translation"], prof_text))
                n_prof += 1

        # model vs model, averaged over both directions so the result does not
        # depend on which model is treated as the hypothesis
        pair_scores = []
        for a, b in combinations(sorted(group, key=lambda g: g["model"]), 2):
            forward = chrf(a["llm_translation"], b["llm_translation"])
            reverse = chrf(b["llm_translation"], a["llm_translation"])
            pair_scores.append((forward + reverse) / 2)
            n_pairs += 1

        if not pair_scores or not prof_scores:
            continue

        rows.append(
            {
                "doc_id": doc_id,
                "language": language,
                "resource_level": RESOURCE_LEVEL.get(language, "unknown"),
                "doc_category": doc_id.split("/")[0],
                "n_models": len(group),
                "chrf_model_vs_model": round(mean(pair_scores), 4),
                "chrf_model_vs_professional": round(mean(prof_scores), 4),
                "gap": round(mean(pair_scores) - mean(prof_scores), 4),
            }
        )

    if not rows:
        sys.exit("No usable (document, language) cells found.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{n_pairs} model-model comparisons, {n_prof} model-professional comparisons")
    print(f"per-cell values written to {out_path}\n")

    # ---- per language -------------------------------------------------
    print(f"{'language':<20} {'level':<7} {'model-model':>12} {'vs prof':>9} {'gap':>7}")
    print("-" * 60)
    langs = sorted({r["language"] for r in rows}, key=lambda L: -mean([r["gap"] for r in rows if r["language"] == L]))
    all_positive = True
    for language in langs:
        sub = [r for r in rows if r["language"] == language]
        mm, mp = mean([r["chrf_model_vs_model"] for r in sub]), mean([r["chrf_model_vs_professional"] for r in sub])
        if mm - mp <= 0:
            all_positive = False
        print(f"{language:<20} {RESOURCE_LEVEL.get(language,'?'):<7} {mm:12.1f} {mp:9.1f} {mm-mp:+7.1f}")

    mm = mean([r["chrf_model_vs_model"] for r in rows])
    mp = mean([r["chrf_model_vs_professional"] for r in rows])
    print("-" * 60)
    print(f"{'OVERALL':<20} {'':<7} {mm:12.1f} {mp:9.1f} {mm-mp:+7.1f}")

    # ---- paired test across cells --------------------------------------
    gaps = [r["gap"] for r in rows]
    try:
        from scipy import stats

        w = stats.wilcoxon([r["chrf_model_vs_model"] for r in rows],
                           [r["chrf_model_vs_professional"] for r in rows])
        ptxt = f"Wilcoxon signed-rank p={w.pvalue:.3g}"
    except ImportError:
        ptxt = "(scipy not installed, paired test skipped)"

    print(
        f"\nPaired across {len(rows)} (document, language) cells: "
        f"mean gap {mean(gaps):+.1f} chrF points, "
        f"median {statistics.median(gaps):+.1f}, {ptxt}"
    )
    print(f"Gap positive in all eight languages: {'yes' if all_positive else 'NO'}")

    print("\n--- sentence for the manuscript ---")
    print(
        f"two models translating the same document agreed with each other "
        f"{mean(gaps):.0f} chrF points more closely than either agreed with the "
        f"professional translation"
        + (", in all eight languages" if all_positive else " (NOT true in all eight languages, reword)")
    )


if __name__ == "__main__":
    main()
