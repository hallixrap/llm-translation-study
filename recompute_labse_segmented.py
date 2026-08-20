#!/usr/bin/env python3
"""
Segment-level LaBSE recomputation for the JGIM revision.

WHY
---
sentence-transformers/LaBSE ships max_seq_length = 256 wordpiece tokens. The
published pipeline calls model.encode() on whole documents (mean 900 words,
~1,200-1,800 wordpieces) with no chunking, so sentence-transformers silently
truncates: every published LaBSE score reflects only the opening ~175-200 words.

This script recomputes every LaBSE-based number in the paper using segment-level
scoring, so the metric reads the entire document. It reports the published value
and the recomputed value side by side, and re-runs the key statistical tests.

WHAT IT PRODUCES
----------------
  labse_segmented_pairs.csv            per-pair published vs recomputed
  labse_segmented_crossmodel.csv       Layer 3, recomputed
  labse_segmented_concordance.csv      Layer 4, recomputed
  labse_segmented_summary.txt          side-by-side tables + re-run tests

USAGE
-----
    cd /path/to/llm-translation-study
    python recompute_labse_segmented.py

    # options
    --window 150        words per segment (default 150, safely under the cap)
    --device mps        mps | cuda | cpu   (default: auto-detect)
    --skip-crossmodel   only redo Layers 1-2 (much faster)

Runtime: roughly 15-30 min on Apple silicon for everything, a few minutes with
--skip-crossmodel. The model is already in your HuggingFace cache from the
original run, so nothing is downloaded.
"""
import argparse, json, os, sys, csv, hashlib
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
STALE_MARKER = "This translation is out of date"


def level(lang):
    return 'high' if lang in HIGH else ('low' if lang in LOW else 'medium')


# ---------------------------------------------------------------- embedding
class Embedder:
    """Chunk -> embed -> cache. Dedupes identical texts (the 22 English sources
    recur across 704 records, so caching cuts the work by roughly a third)."""

    def __init__(self, model, window, batch=64):
        self.m, self.window, self.batch = model, window, batch
        self._doc = {}
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

    def doc_embedding(self, text):
        """Mean-pooled over segments: a whole-document vector that, unlike the
        published approach, actually contains every segment."""
        k = self._key(text)
        if k not in self._doc:
            e = self.chunk_embeddings(text)
            self._doc[k] = e.mean(axis=0) if len(e) else None
        return self._doc[k]


def cos(a, b):
    if a is None or b is None:
        return None
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / d) if d else None


def pooled_similarity(emb, t1, t2):
    """Variant A - mean-pool each document, then compare."""
    return cos(emb.doc_embedding(t1), emb.doc_embedding(t2))


def aligned_similarity(emb, t1, t2):
    """Variant B - compare segment k of one text against segment k of the other
    and average. Stricter: local divergence anywhere in the document shows up,
    where mean-pooling can average it away."""
    e1, e2 = emb.chunk_embeddings(t1), emb.chunk_embeddings(t2)
    if not len(e1) or not len(e2):
        return None
    n = max(len(e1), len(e2))
    out = []
    for i in range(n):                      # positional alignment; a shorter
        a = e1[min(i, len(e1) - 1)]         # text reuses its final segment, so
        b = e2[min(i, len(e2) - 1)]         # truncated output is penalised
        out.append(cos(a, b))
    return float(np.mean(out))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=150)
    ap.add_argument('--device', default=None)
    ap.add_argument('--out', default='output/labse_segmented')
    ap.add_argument('--skip-crossmodel', action='store_true')
    a = ap.parse_args()

    if not os.path.exists('output/medlineplus_results/all_results.json'):
        sys.exit("Run me from the root of the llm-translation-study repo.")
    os.makedirs(a.out, exist_ok=True)

    dev = a.device
    if dev is None:
        try:
            import torch
            dev = ('mps' if torch.backends.mps.is_available()
                   else 'cuda' if torch.cuda.is_available() else 'cpu')
        except Exception:
            dev = 'cpu'
    print(f"[init] loading LaBSE on {dev} (window={a.window} words)")
    model = SentenceTransformer('sentence-transformers/LaBSE', device=dev)
    print(f"[init] model.max_seq_length = {model.max_seq_length} tokens "
          f"<- this is the cap the published run silently hit")
    emb = Embedder(model, a.window)

    results = json.load(open('output/medlineplus_results/all_results.json'))
    metrics = {(r['doc_id'], r['model'], r['language']): r
               for r in json.load(open('output/medlineplus_metrics/all_metrics.json'))}

    # ---------------- Layers 1 & 2 -------------------------------------
    print(f"[layer 1-2] recomputing {len(results)} pairs")
    rows = []
    for i, r in enumerate(results, 1):
        if i % 100 == 0:
            print(f"           {i}/{len(results)}")
        key = (r['doc_id'], r['model'], r['language'])
        pub = metrics.get(key, {}).get('cross_lang_labse')
        en = r.get('english_original') or ''
        bt = r.get('llm_back_translation') or ''
        pbt = r.get('professional_back_translation') or ''
        if not en.strip():
            continue
        row = dict(
            doc_id=r['doc_id'], model=r['model'], language=r['language'],
            resource_level=level(r['language']),
            doc_category=r['doc_id'].split('/')[0],
            source_words=len(en.split()),
            stale_reference=STALE_MARKER in (r.get('professional_translation') or '')[:300],
            labse_published=pub,
            labse_pooled=pooled_similarity(emb, bt, en) if bt.strip() else None,
            labse_aligned=aligned_similarity(emb, bt, en) if bt.strip() else None,
            prof_labse_published=metrics.get(key, {}).get('prof_backtrans_labse'),
            prof_labse_pooled=pooled_similarity(emb, pbt, en) if pbt.strip() else None,
        )
        rows.append(row)

    with open(f'{a.out}/labse_segmented_pairs.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[layer 1-2] wrote {len(rows)} rows")

    # ---------------- Layer 4: concordance ------------------------------
    print("[layer 4] recomputing inter-model concordance")
    fwd = {(r['doc_id'], r['model'], r['language']): (r.get('llm_translation') or '')
           for r in results}
    conc = []
    for c in json.load(open('output/inter_model_concordance/'
                            'inter_model_concordance_results.json')):
        ta = fwd.get((c['doc_id'], c['model_a'], c['language']), '')
        tb = fwd.get((c['doc_id'], c['model_b'], c['language']), '')
        if not ta.strip() or not tb.strip():
            continue
        conc.append(dict(
            doc_id=c['doc_id'], language=c['language'],
            resource_level=c['resource_level'], model_pair=c['model_pair'],
            labse_published=c['labse_similarity'],
            labse_pooled=pooled_similarity(emb, ta, tb),
            labse_aligned=aligned_similarity(emb, ta, tb)))
    if conc:
        with open(f'{a.out}/labse_segmented_concordance.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(conc[0].keys()))
            w.writeheader()
            w.writerows(conc)
    print(f"[layer 4] wrote {len(conc)} rows")

    # ---------------- Layer 3: cross-model ------------------------------
    cross = []
    if not a.skip_crossmodel:
        cm = json.load(open('output/cross_model_backtranslation/'
                            'all_cross_model_results.json'))
        print(f"[layer 3] recomputing {len(cm)} cross-model pairs")
        for i, c in enumerate(cm, 1):
            if i % 200 == 0:
                print(f"          {i}/{len(cm)}")
            o = c.get('original_text') or ''
            b = c.get('back_translated_text') or ''
            if not o.strip() or not b.strip():
                continue
            cross.append(dict(
                doc_id=c['doc_id'], language=c['language'],
                resource_level=level(c['language']),
                forward_model=c['forward_model'], back_model=c['back_model'],
                labse_published=c.get('labse_score'),
                labse_pooled=pooled_similarity(emb, b, o),
                labse_aligned=aligned_similarity(emb, b, o)))
        if cross:
            with open(f'{a.out}/labse_segmented_crossmodel.csv', 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(cross[0].keys()))
                w.writeheader()
                w.writerows(cross)
        print(f"[layer 3] wrote {len(cross)} rows")

    # ---------------- summary + re-run tests ----------------------------
    out = []

    def say(s=''):
        print(s)
        out.append(s)

    def mean(v):
        v = [x for x in v if x is not None]
        return float(np.mean(v)) if v else float('nan')

    say("=" * 78)
    say(f"SEGMENT-LEVEL LaBSE RECOMPUTATION  (window = {a.window} words)")
    say("=" * 78)
    say("published = whole document passed to encode(), truncated at 256 tokens")
    say("pooled    = document chunked, every chunk embedded, mean-pooled")
    say("aligned   = per-segment cosine, averaged (strictest)")

    say("\n--- Layer 1: back-translation fidelity, by model ---")
    say(f"{'model':22}{'published':>12}{'pooled':>12}{'aligned':>12}{'shift':>10}")
    bym = defaultdict(list)
    for r in rows:
        bym[r['model']].append(r)
    for m, rs in sorted(bym.items()):
        p, q, al = (mean([x['labse_published'] for x in rs]),
                    mean([x['labse_pooled'] for x in rs]),
                    mean([x['labse_aligned'] for x in rs]))
        say(f"{m:22}{p:>12.4f}{q:>12.4f}{al:>12.4f}{q - p:>+10.4f}")

    say("\n--- Layer 1: by language ---")
    say(f"{'language':22}{'level':>9}{'published':>12}{'pooled':>12}{'aligned':>12}")
    byl = defaultdict(list)
    for r in rows:
        byl[r['language']].append(r)
    for l, rs in sorted(byl.items(), key=lambda x: -mean([y['labse_pooled'] for y in x[1]])):
        say(f"{l:22}{level(l):>9}"
            f"{mean([x['labse_published'] for x in rs]):>12.4f}"
            f"{mean([x['labse_pooled'] for x in rs]):>12.4f}"
            f"{mean([x['labse_aligned'] for x in rs]):>12.4f}")

    def compare(rs, field, split, la, lb, title):
        A = [x[field] for x in rs if split(x) == la and x[field] is not None]
        B = [x[field] for x in rs if split(x) == lb and x[field] is not None]
        if not A or not B:
            return
        u, p = stats.mannwhitneyu(A, B)
        flag = 'ns' if p >= .05 else ('*' if p >= .01 else ('**' if p >= .001 else '***'))
        say(f"  {title:26}{field:18}{la}={np.mean(A):.4f} (n={len(A)})  "
            f"{lb}={np.mean(B):.4f} (n={len(B)})  p={p:.3g} {flag}")

    say("\n--- THE HEADLINE TEST: low vs high resource ---")
    for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
        compare(rows, f, lambda x: x['resource_level'], 'low', 'high', 'all cells')
    say("  (restricted to cells whose professional reference is NOT out of date)")
    cur = [x for x in rows if not x['stale_reference']]
    for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
        compare(cur, f, lambda x: x['resource_level'], 'low', 'high', 'current refs only')

    say("\n--- clustered by (document, language), model pseudoreplication removed ---")
    for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
        cl = defaultdict(list)
        for x in rows:
            if x[f] is not None:
                cl[(x['doc_id'], x['language'], x['resource_level'])].append(x[f])
        A = [np.mean(v) for k, v in cl.items() if k[2] == 'low']
        B = [np.mean(v) for k, v in cl.items() if k[2] == 'high']
        u, p = stats.mannwhitneyu(A, B)
        say(f"  {f:18} low={np.mean(A):.4f} (n={len(A)})  "
            f"high={np.mean(B):.4f} (n={len(B)})  p={p:.3g}")

    say("\n--- DOES THE 'DOCUMENT TYPE' CLAIM SURVIVE? cancer vs vaccine ---")
    say("  (published LaBSE says cancer >> vaccine; full-document chrF says the")
    say("   opposite. If that gap was a truncation artefact it should shrink here.)")
    for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
        compare(rows, f, lambda x: x['doc_category'], 'cancer', 'immunize', 'category')

    say("\n--- ceiling diagnostics (AE comment 2: metric saturation) ---")
    for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
        v = np.array([x[f] for x in rows if x[f] is not None])
        say(f"  {f:18} >0.98: {100 * (v > .98).mean():5.1f}%   "
            f">0.95: {100 * (v > .95).mean():5.1f}%   SD={v.std():.4f}   "
            f"IQR={np.percentile(v, 75) - np.percentile(v, 25):.4f}")

    if conc:
        say("\n--- Layer 4: inter-model concordance ---")
        for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
            say(f"  {f:18} overall = {mean([c[f] for c in conc]):.4f}")
    if cross:
        say("\n--- Layer 3: cross-model back-translation ---")
        for f in ['labse_published', 'labse_pooled', 'labse_aligned']:
            say(f"  {f:18} overall = {mean([c[f] for c in cross]):.4f}")

    say("\n" + "=" * 78)
    with open(f'{a.out}/labse_segmented_summary.txt', 'w') as f:
        f.write("\n".join(out))
    print(f"\nWrote {a.out}/  — send me labse_segmented_summary.txt and the CSVs.")


if __name__ == '__main__':
    main()
