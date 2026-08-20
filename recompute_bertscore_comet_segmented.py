#!/usr/bin/env python3
"""
Segment-level recomputation of BERTScore and COMET.

WHY THIS EXISTS
---------------
The same fixed input window that truncated LaBSE also affects the other two
neural measures, less severely but by the same mechanism:

    LaBSE       256 tokens   ~ first 20% of a 900-word document
    BERTScore   512 tokens   ~ first 40%
    COMET       512 tokens   ~ first 40%

BLEU and chrF are string based and see the whole document.

LaBSE has been recomputed at segment level. If BERTScore and COMET are left as
published, the paper reports one measure computed over whole documents and two
computed over their opening 40%, which is exactly the inconsistency Reviewer 2
asked about. This script fixes that.

It matters most for one claim. On the untruncated lexical measure, low-resource
languages score slightly HIGHER than high-resource against professional
translations; on truncated COMET they score LOWER (0.837 vs 0.879). That
disagreement has the same signature as the LaBSE problem and needs resolving
rather than reporting.

USAGE
-----
    cd <repo root>
    source .venv/bin/activate
    pip install bert-score unbabel-comet

    python recompute_bertscore_comet_segmented.py --metrics bertscore   # ~30-45 min
    python recompute_bertscore_comet_segmented.py --metrics comet       # ~2-4 h, heavy
    python recompute_bertscore_comet_segmented.py --metrics both

COMET downloads a ~2.3GB model on first run and is slow. Run bertscore first;
it is quicker and answers most of the question. Both checkpoint after every
document, so Ctrl+C is safe and re-running resumes.
"""
import argparse, json, os, sys, csv, math
from collections import defaultdict
import numpy as np

HIGH = {'spanish', 'chinese_simplified', 'russian', 'vietnamese'}
LOW = {'tagalog', 'haitian_creole'}
# bert-score language codes; the published run passed lang="multilingual",
# which bert-score silently resolves to multilingual BERT for every language.
# We pin that model explicitly so the comparison is like for like.
MULTILINGUAL_MODEL = 'bert-base-multilingual-cased'
ENGLISH_MODEL = 'roberta-large'


def level(l):
    return 'high' if l in HIGH else ('low' if l in LOW else 'medium')


def segments(text, n):
    """Split into n positionally aligned chunks.

    Texts in different languages have different word counts for the same
    content, so chunking by a fixed word count would misalign them. Splitting
    each text into the same NUMBER of proportional chunks keeps chunk k of the
    translation aligned with chunk k of the source.
    """
    w = (text or '').split()
    if not w or n < 1:
        return []
    return [' '.join(w[i * len(w) // n:(i + 1) * len(w) // n]) for i in range(n)]


def n_segments(english, window=150):
    return max(1, math.ceil(len((english or '').split()) / window))



def _patch_functools_for_comet():
    """COMET 2.2.7 imports private names from functools that Python 3.14 removed.

    comet/models/lru_cache.py does `from functools import _CacheInfo, _HashedSeq`.
    Both are internal CPython bookkeeping helpers for lru_cache. Recreating them
    with CPython's own definitions lets the import succeed without changing any
    COMET behaviour: they are used only for cache key hashing and cache
    statistics, neither of which affects a score.
    """
    import functools
    if not hasattr(functools, '_HashedSeq'):
        class _HashedSeq(list):
            __slots__ = 'hashvalue'

            def __init__(self, tup, hash=hash):
                self[:] = tup
                self.hashvalue = hash(tup)

            def __hash__(self):
                return self.hashvalue
        functools._HashedSeq = _HashedSeq
    if not hasattr(functools, '_CacheInfo'):
        from collections import namedtuple
        functools._CacheInfo = namedtuple(
            "CacheInfo", ["hits", "misses", "maxsize", "currsize"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--metrics', choices=['bertscore', 'comet', 'both'], default='both')
    ap.add_argument('--window', type=int, default=150)
    ap.add_argument('--out', default='output/segmented_bertscore_comet')
    a = ap.parse_args()

    if not os.path.exists('output/medlineplus_results/all_results.json'):
        sys.exit("Run me from the root of the llm-translation-study repo.")
    os.makedirs(a.out, exist_ok=True)
    ckpt = f'{a.out}/checkpoint.jsonl'

    results = json.load(open('output/medlineplus_results/all_results.json'))
    published = {(r['doc_id'], r['model'], r['language']): r
                 for r in json.load(open('output/medlineplus_metrics/all_metrics.json'))}

    do_bs = a.metrics in ('bertscore', 'both')
    do_cm = a.metrics in ('comet', 'both')

    # Resume is tracked PER METRIC. A record completed by the BERTScore pass is
    # not complete for COMET, so each metric keeps its own done-set.
    done_bs, done_cm = set(), set()
    if os.path.exists(ckpt):
        for line in open(ckpt):
            try:
                r = json.loads(line)
                k = (r['doc_id'], r['model'], r['language'])
                if r.get('bertscore_segmented') is not None:
                    done_bs.add(k)
                if r.get('comet_segmented') is not None:
                    done_cm.add(k)
            except Exception:
                pass
        print(f"resuming: {len(done_bs)} done for bertscore, {len(done_cm)} for comet")

    bs = None
    if do_bs:
        from bert_score import BERTScorer
        print("[init] loading BERTScore (multilingual + english)")
        bs = {'multi': BERTScorer(model_type=MULTILINGUAL_MODEL, num_layers=9),
              'en': BERTScorer(lang='en', model_type=ENGLISH_MODEL, num_layers=17)}

    comet = None
    if do_cm:
        _patch_functools_for_comet()
        from comet import download_model, load_from_checkpoint
        print("[init] loading COMET wmt20-comet-da (large download on first run)")
        comet = load_from_checkpoint(download_model("Unbabel/wmt20-comet-da"))

    fh = open(ckpt, 'a')

    def needs(r):
        k = (r['doc_id'], r['model'], r['language'])
        return (do_bs and k not in done_bs) or (do_cm and k not in done_cm)

    todo = [r for r in results if needs(r)]
    print(f"[run] {len(todo)} records to process")

    for i, r in enumerate(todo, 1):
        key = (r['doc_id'], r['model'], r['language'])
        en = r.get('english_original') or ''
        mt = r.get('llm_translation') or ''
        ref = r.get('professional_translation') or ''
        bt = r.get('llm_back_translation') or ''
        n = n_segments(en, a.window)
        pub = published.get(key, {})

        row = dict(doc_id=r['doc_id'], model=r['model'], language=r['language'],
                   resource_level=level(r['language']),
                   doc_category=r['doc_id'].split('/')[0], n_segments=n,
                   bertscore_published=pub.get('same_lang_bertscore'),
                   comet_published=pub.get('same_lang_comet'),
                   backtrans_bertscore_published=pub.get('backtrans_bertscore'))

        need_bs = do_bs and key not in done_bs
        need_cm = do_cm and key not in done_cm

        if need_bs and mt.strip() and ref.strip():
            try:
                h, rr = segments(mt, n), segments(ref, n)
                P, R, F = bs['multi'].score(h, rr)
                row['bertscore_segmented'] = float(F.mean())
            except Exception as e:
                row['bertscore_error'] = str(e)[:160]

        if need_bs and bt.strip() and en.strip():
            try:
                h, rr = segments(bt, n), segments(en, n)
                P, R, F = bs['en'].score(h, rr)
                row['backtrans_bertscore_segmented'] = float(F.mean())
            except Exception as e:
                row['backtrans_bertscore_error'] = str(e)[:160]

        if need_cm and mt.strip() and ref.strip() and en.strip():
            try:
                data = [{"src": s, "mt": m, "ref": f}
                        for s, m, f in zip(segments(en, n), segments(mt, n), segments(ref, n))]
                out = comet.predict(data, batch_size=8, accelerator='cpu',
                                    progress_bar=False)
                row['comet_segmented'] = float(np.mean(out.scores))
            except Exception as e:
                row['comet_error'] = str(e)[:160]

        fh.write(json.dumps(row) + "\n")
        fh.flush()
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}  {r['doc_id']:38} {r['language']:18} "
                  f"bs={row.get('bertscore_segmented')} comet={row.get('comet_segmented')}")
    fh.close()

    merged = {}
    for l in open(ckpt):
        try:
            r = json.loads(l)
        except Exception:
            continue
        k = (r['doc_id'], r['model'], r['language'])
        base = merged.setdefault(k, {})
        for kk, vv in r.items():
            if vv is not None or kk not in base:
                base[kk] = vv
    rows = list(merged.values())
    if rows:
        cols = sorted({c for r in rows for c in r})
        with open(f'{a.out}/segmented_bertscore_comet.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols, restval='')
            w.writeheader()
            w.writerows(rows)
    summarise(rows, a.out)


def summarise(rows, out):
    from scipy import stats
    lines = []

    def say(s=''):
        print(s)
        lines.append(s)

    def m(v):
        v = [x for x in v if x is not None]
        return float(np.mean(v)) if v else float('nan')

    say("=" * 78)
    say("SEGMENT-LEVEL BERTScore AND COMET")
    say("=" * 78)

    for pubf, segf, label in [('bertscore_published', 'bertscore_segmented',
                               'BERTScore vs professional'),
                              ('comet_published', 'comet_segmented',
                               'COMET vs professional'),
                              ('backtrans_bertscore_published',
                               'backtrans_bertscore_segmented',
                               'BERTScore, back-translation')]:
        have = [r for r in rows if r.get(segf) is not None]
        if not have:
            continue
        say(f"\n--- {label} ---")
        say(f"  overall   published {m([r.get(pubf) for r in have]):.4f}   "
            f"segmented {m([r[segf] for r in have]):.4f}")
        say(f"  {'level':10}{'published':>12}{'segmented':>12}")
        for lv in ['high', 'medium', 'low']:
            rs = [r for r in have if r['resource_level'] == lv]
            if rs:
                say(f"  {lv:10}{m([r.get(pubf) for r in rs]):>12.4f}"
                    f"{m([r[segf] for r in rs]):>12.4f}")
        A = [r[segf] for r in have if r['resource_level'] == 'low']
        B = [r[segf] for r in have if r['resource_level'] == 'high']
        if A and B:
            say(f"  low vs high, segmented: {np.mean(A):.4f} vs {np.mean(B):.4f}, "
                f"Mann-Whitney p={stats.mannwhitneyu(A, B).pvalue:.3g}")
            Ap = [r.get(pubf) for r in have if r['resource_level'] == 'low' and r.get(pubf) is not None]
            Bp = [r.get(pubf) for r in have if r['resource_level'] == 'high' and r.get(pubf) is not None]
            say(f"  low vs high, published: {np.mean(Ap):.4f} vs {np.mean(Bp):.4f}, "
                f"Mann-Whitney p={stats.mannwhitneyu(Ap, Bp).pvalue:.3g}")
        A = [r[segf] for r in have if r['doc_category'] == 'cancer']
        B = [r[segf] for r in have if r['doc_category'] == 'immunize']
        if A and B:
            say(f"  cancer vs vaccine, segmented: {np.mean(A):.4f} vs {np.mean(B):.4f}, "
                f"p={stats.mannwhitneyu(A, B).pvalue:.3g}")

    say("\n" + "=" * 78)
    with open(f'{out}/segmented_bertscore_comet_summary.txt', 'w') as f:
        f.write("\n".join(lines))
    print(f"\nWrote {out}/ — send me segmented_bertscore_comet_summary.txt")


if __name__ == '__main__':
    main()
