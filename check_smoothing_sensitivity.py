# -*- coding: utf-8 -*-
"""对"合法检验"做平滑敏感性检查：add-α 取 0.25/0.5/1/2 时，D_marg 的符号是否稳定。

Smoothing-sensitivity check for the valid test: is the sign of D_marg stable for add-α ∈ {0.25, 0.5, 1, 2}?

用法 / Usage:
  python d_asym_permutation.py --filelist files_author_d5.txt --depth 5 --nperm 0 --out valid_depth5.json
  python check_smoothing_sensitivity.py
"""
import json
import math
import os
import sys

GH = os.path.dirname(os.path.abspath(__file__))   # 脚本所在目录（第三方克隆后即克隆目录）
sys.path.insert(0, GH)
import d_asym_permutation as dap  # noqa: E402

DEPTH = 5


def stats(tokens, alpha):
    fwd, bwd = dap.build_counts(tokens)
    n = len(tokens)
    v = len({t for _, t in tokens})
    f, b = {}, {}
    for (p, t), c in fwd.items():
        f[t] = f.get(t, 0) + c
    for (p, t), c in bwd.items():
        b[t] = b.get(t, 0) + c
    n_b = n - 1
    syms = sorted(set(f) | set(b))
    pf = {t: (f.get(t, 0) + alpha) / (n + alpha * v) for t in syms}
    pb = {t: (b.get(t, 0) + alpha) / (n_b + alpha * v) for t in syms}
    dm = sum(pf[t] * math.log(pf[t] / pb[t]) - pb[t] * math.log(pb[t] / pf[t]) for t in syms)
    delta = {t: pb[t] - pf[t] for t in syms}
    num = sum(delta[t] ** 3 / pf[t] ** 2 for t in syms)
    den = sum(delta[t] ** 2 / pf[t] for t in syms)
    sk = num / den ** 1.5 if den > 0 else 0.0
    return dm, sk


for name, label in [("perm_depth5.json", "作者数据集"), ("perm_stdlib.json", "标准库")]:
    d = json.load(open(os.path.join(GH, name), encoding="utf-8"))
    files = [f["file"] for f in d["per_file"] if os.path.exists(f["file"])]
    if not files:
        print("== %s：文件路径不存在（该清单记录的是作者本机路径）==" % label)
        continue
    cache = []
    for fp in files:
        src = open(fp, "r", encoding="utf-8-sig", errors="replace").read()
        toks = dap.collect_tokens(src, DEPTH)
        if len(toks) >= 50:
            cache.append(toks)
    print("== %s（%d 文件）==" % (label, len(cache)))
    for alpha in (0.25, 0.5, 1.0, 2.0):
        ok = tot = 0
        for toks in cache:
            dm, sk = stats(toks, alpha)
            tot += 1
            if dm * sk < 0:
                ok += 1
        print("  add-%-4s : sign(D_marg) = −sign(S(δ)) 成立 %d/%d" % (alpha, ok, tot))
