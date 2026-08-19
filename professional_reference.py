#!/usr/bin/env python3
"""
The professional-translation reference distribution, at segment level.

WHY
---
The Methods say we "used the professional translations passed through the
identical pipeline as the reference distribution for this corpus." For chrF that
reference is published (Supplementary Table S2). For LaBSE it is not: the pairs
file carries prof_labse_pooled and prof_labse_published, but no aligned value,
so the primary metric has no professional anchor.

The editor asks how to read a LaBSE value of 0.83, and whether the difference
between the two document sets (0.934 against 0.832) means the models handle
vaccine statements badly. Neither question can be answered from the number
alone. Both can be answered by asking what a professional human translation
scores on the same documents, through the same round trip, under the same
scorer. This script computes that.

It uses the same Embedder and the same aligned_similarity as
recompute_labse_segmented.py, and it re-derives the model's own labse_aligned
first and checks it against the published CSV. If that check fails, stop: the
pipeline has drifted and nothing below it can be trusted.

USAGE
-----
    cd ~/Desktop/jgim-reanalysis
    source .venv/bin/activate
    python professional_reference.py

    --window 150     words per segment (must match the main run)
    --device mps     mps | cuda | cpu   (default: auto)

Needs sentence-transformers, scipy and numpy, all already in the environment.
No API keys. No downloads: LaBSE is in your HuggingFace cache from the first run.
Roughly 10-20 minutes on Apple silicon.

OUTPUT
------
    output/professional_reference/professional_reference_pairs.csv
    printed tables, ready to paste back
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, sys
from collections import defaultdict

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    sys.exit("pip install sentence-transformers")
try:
    from scipy import stats
except ImportError:
    sys.exit("pip install scipy")

HIGH = {'spanish', 'chinese_simplified', 'russian', 'vietnamese'}
LOW = {'tagalog', 'haitian_creole'}
RESULTS = 'output/medlineplus_results/all_results.json'
PUBLISHED = 'output/labse_segmented/labse_segmented_pairs.csv'
OUTDIR = 'output/professional_reference'


def level(lang):
    return 'high' if lang in HIGH else ('low' if lang in LOW else 'medium')


# ------------------------------------------------------------------ embedding
# Copied verbatim from recompute_labse_segmented.py so the two cannot drift.
class Embedder:
    def __init__(self, model, window, batch=64):
        self.m, self.window, self.batch = model, window, batch
        self._chunks = {}

    @staticmethod
    def _key(t):
        return hashlib.md5(t.encode('utf-8', 'ignore')).hexdigest()

    def _split(self, text):
        w = text.split()
        if not w:
            return []
        return [' '.join(w[i:i + self.window]) for i in range(0, len(w), self.window)]

    def chunk_embeddings(self, text):
        k = self._key(text)
        if k not in self._chunks:
            ch = self._split(text)
            self._chunks[k] = (self.m.encode(ch, batch_size=self.batch,
                                             show_progress_bar=False)
                               if ch else np.zeros((0, 768)))
        return self._chunks[k]


def cos(a, b):
    if a is None or b is None:
        return None
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / d) if d else None


def aligned_similarity(emb, t1, t2):
    e1, e2 = emb.chunk_embeddings(t1), emb.chunk_embeddings(t2)
    if not len(e1) or not len(e2):
        return None
    n = max(len(e1), len(e2))
    return float(np.mean([cos(e1[min(i, len(e1) - 1)], e2[min(i, len(e2) - 1)])
                          for i in range(n)]))


# ---------------------------------------------------------------- statistics
def mean_sd(v):
    v = [x for x in v if x is not None]
    return (float(np.mean(v)), float(np.std(v, ddof=1)), len(v)) if v else (float('nan'),) * 2 + (0,)


def clustered(rows, field, by):
    """Average within each document-language combination before testing, as
    every group comparison in the paper does. Returns {group: [values]}."""
    acc = defaultdict(list)
    for r in rows:
        if r[field] is not None:
            acc[(r['doc_id'], r['language'], r[by])].append(r[field])
    out = defaultdict(list)
    for (_, _, g), v in acc.items():
        out[g].append(float(np.mean(v)))
    return out


def boot_diff(a, b, n=10000, seed=20260801):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = [rng.choice(a, len(a), True).mean() - rng.choice(b, len(b), True).mean()
         for _ in range(n)]
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def group_table(rows, field, by, order=None):
    acc = defaultdict(list)
    for r in rows:
        if r[field] is not None:
            acc[r[by]].append(r[field])
    for g in (order or sorted(acc)):
        if g in acc:
            m, s, n = mean_sd(acc[g])
            print(f"      {g:<10} mean {m:.3f}   SD {s:.3f}   n {n}")


def compare(rows, field, by, hi, lo, label):
    c = clustered(rows, field, by)
    if hi not in c or lo not in c:
        return
    x, y = c[hi], c[lo]
    diff, l, u = boot_diff(x, y)
    p = stats.mannwhitneyu(x, y).pvalue
    print(f"      {label:<24} {np.mean(x):.3f} vs {np.mean(y):.3f}   diff {diff:+.3f} "
          f"(95% CI {l:+.3f} to {u:+.3f})   P = {p:.3g}   n = {len(x)}/{len(y)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=150)
    ap.add_argument('--device', default=None)
    a = ap.parse_args()

    if not os.path.exists(RESULTS):
        sys.exit(f"Run me from the repository root. Could not find {RESULTS}\n"
                 f"You are in: {os.getcwd()}")

    print(f"loading LaBSE (window {a.window} words) ...")
    emb = Embedder(SentenceTransformer('sentence-transformers/LaBSE', device=a.device), a.window)

    recs = [r for r in json.load(open(RESULTS)) if r.get('success') in (True, 'True')]
    print(f"{len(recs)} successful pairs\n")

    rows = []
    for i, r in enumerate(recs, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(recs)}")
        en = r['english_original']
        bt = (r.get('llm_back_translation') or '').strip()
        pbt = (r.get('professional_back_translation') or '').strip()
        rows.append(dict(
            doc_id=r['doc_id'], model=r['model'], language=r['language'],
            resource_level=level(r['language']), doc_category=r['doc_id'].split('/')[0],
            labse_aligned=aligned_similarity(emb, bt, en) if bt else None,
            prof_labse_aligned=aligned_similarity(emb, pbt, en) if pbt else None))

    os.makedirs(OUTDIR, exist_ok=True)
    path = f'{OUTDIR}/professional_reference_pairs.csv'
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---- validation -------------------------------------------------------
    print("\n" + "=" * 74)
    print("VALIDATION   recomputed labse_aligned against the published CSV")
    print("=" * 74)
    if os.path.exists(PUBLISHED):
        pub = {}
        with open(PUBLISHED) as f:
            for p in csv.DictReader(f):
                if p['labse_aligned']:
                    pub[(p['doc_id'], p['model'], p['language'])] = float(p['labse_aligned'])
        d = [abs(r['labse_aligned'] - pub[k])
             for r in rows
             if r['labse_aligned'] is not None
             and (k := (r['doc_id'], r['model'], r['language'])) in pub]
        worst = max(d) if d else float('nan')
        print(f"  {len(d)} pairs matched | largest difference {worst:.2e} | "
              f"{'IDENTICAL' if worst < 1e-6 else '*** MISMATCH - STOP, DO NOT USE ***'}")
    else:
        print("  published CSV not found, skipping")

    # ---- the reference distribution ---------------------------------------
    both = [r for r in rows if r['labse_aligned'] is not None and r['prof_labse_aligned'] is not None]
    lm, ls, ln = mean_sd([r['labse_aligned'] for r in both])
    pm, ps, _ = mean_sd([r['prof_labse_aligned'] for r in both])
    diff, l, u = boot_diff([r['labse_aligned'] for r in both],
                           [r['prof_labse_aligned'] for r in both])
    w = stats.wilcoxon([r['labse_aligned'] for r in both],
                       [r['prof_labse_aligned'] for r in both])

    print("\n" + "=" * 74)
    print("SEGMENT-LEVEL LaBSE AGAINST THE ENGLISH SOURCE")
    print("=" * 74)
    print(f"\n  overall        model {lm:.3f} (SD {ls:.3f})   "
          f"professional {pm:.3f} (SD {ps:.3f})   n = {ln}")
    print(f"  model - professional  {diff:+.3f} (95% CI {l:+.3f} to {u:+.3f})   "
          f"Wilcoxon P = {w.pvalue:.3g}")

    for field, lab in (('labse_aligned', 'MODEL round trip'),
                       ('prof_labse_aligned', 'PROFESSIONAL round trip')):
        print(f"\n  --- {lab}")
        print("    by document type")
        group_table(rows, field, 'doc_category')
        compare(rows, field, 'doc_category', 'cancer', 'immunize', 'cancer vs vaccine')
        print("    by resource level")
        group_table(rows, field, 'resource_level', ['high', 'medium', 'low'])
        compare(rows, field, 'resource_level', 'low', 'high', 'low vs high resource')

    print("\n  --- by language")
    print(f"    {'language':<20}{'model':>10}{'professional':>15}")
    acc = defaultdict(lambda: ([], []))
    for r in rows:
        if r['labse_aligned'] is not None:
            acc[(r['resource_level'], r['language'])][0].append(r['labse_aligned'])
        if r['prof_labse_aligned'] is not None:
            acc[(r['resource_level'], r['language'])][1].append(r['prof_labse_aligned'])
    for (res, lang) in sorted(acc):
        m, p = acc[(res, lang)]
        print(f"    {lang:<20}{np.mean(m):>10.3f}{np.mean(p):>15.3f}   ({res})")

    print(f"\nwrote {path}")


if __name__ == '__main__':
    main()