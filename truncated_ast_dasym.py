# -*- coding: utf-8 -*-
"""截断 AST 路径（在第一个"未来祖先"处截断）上的 ⟨ΔS⟩。

⟨ΔS⟩ on truncated AST paths: keep the full AST ancestor chain but cut it at the first ancestor that
starts at or after the token, so the retained chain is prefix-measurable. All tokens are kept.

两种顺序 / two orders:
  --mode trunc         AST 字段序（与 full-AST 同序，便于隔离"泄漏"本身）
  --mode trunc_sorted  按 (lineno, col_offset) 源码序（同时修正顺序问题；丢弃无位置算子）
用法 / Usage: python truncated_ast_dasym.py --mode trunc --depth 5 --nperm 1000
"""
import argparse
import ast
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402


def pos(n):
    ln = getattr(n, "lineno", None)
    co = getattr(n, "col_offset", None)
    return None if ln is None or co is None else (ln, co)


def collect(src, depth, mode):
    tree = ast.parse(src)
    out = []          # (path, sym, (lineno, col_offset))
    stack = []
    truncate = mode != "full_sorted"      # full_sorted 保留完整祖先链、只改顺序 / keep full chain, only reorder

    def walk(node):
        sym = dap.leaf_symbol(node)
        if sym is not None:
            tp = pos(node)
            if truncate:
                keep = 0
                for a in stack:
                    ap = pos(a)
                    if ap is None:
                        if isinstance(a, ast.Module):
                            keep += 1
                            continue
                        break                      # 无位置的非根祖先：保守截断
                    if tp is not None and ap < tp:
                        keep += 1
                    else:
                        break
                path = tuple(type(a).__name__ for a in stack[:keep][-depth:])
            else:
                path = tuple(type(a).__name__ for a in stack[-depth:])
            out.append((path, sym, tp))
            return
        stack.append(node)
        for ch in ast.iter_child_nodes(node):
            walk(ch)
        stack.pop()

    walk(tree)
    if mode.endswith("sorted"):
        out = [x for x in out if x[2] is not None]
        out.sort(key=lambda x: x[2])
    return [(p, s) for p, s, _ in out]


def stats(tokens):
    seq, mean = dap.eval_stat(tokens)
    fwd, bwd = dap.build_counts(tokens)
    v = len({t for _, t in tokens})
    return {"n": len(tokens), "mean": mean,
            "pos_frac": sum(1 for x in seq if x > 0) / len(seq),
            "skew": dap.skew_delta(fwd, bwd, len(tokens), v)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["trunc", "trunc_sorted", "full_sorted"], default="trunc")
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--nperm", type=int, default=1000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--filelist", default=os.path.join(HERE, "files_author_d5.txt"))
    args = ap.parse_args()
    out_path = args.out or os.path.join(HERE, "trunc_%s_d%d.json" % (args.mode, args.depth))

    files = [ln.strip() for ln in open(args.filelist, encoding="utf-8") if ln.strip()]
    all_toks, per_file, used = [], [], 0
    for fp in files:
        if not os.path.exists(fp):
            continue
        try:
            src = open(fp, encoding="utf-8-sig", errors="replace").read()
            toks = collect(src, args.depth, args.mode)
        except Exception:
            continue
        if len(toks) < 50:
            continue
        used += 1
        all_toks += toks
        st = stats(toks)
        per_file.append({"file": fp, "n": st["n"], "mean": st["mean"], "skew": st["skew"]})

    st = stats(all_toks)
    dist = []
    for k in range(args.nperm):
        r2 = random.Random(20260929 + 1000 + k)
        _, m = dap.eval_stat(dap.permute_symbols(all_toks, r2))
        dist.append(m)
    null_mean = sum(dist) / len(dist)
    p_one = (sum(1 for x in dist if x >= st["mean"]) + 1) / (len(dist) + 1)
    n_pos = sum(1 for f in per_file if f["mean"] > 0)
    print("mode=%s depth=%d | 文件=%d token=%d | <DeltaS>=%+.4f | pos_frac=%.3f | S(delta)=%+.3f"
          % (args.mode, args.depth, used, st["n"], st["mean"], st["pos_frac"], st["skew"]))
    print("置换: null_mean=%+.5f null_max=%+.4f p_one=%.4f | 逐文件 mean>0 = %d/%d"
          % (null_mean, max(dist), p_one, n_pos, len(per_file)))
    json.dump({"mode": args.mode, "depth": args.depth, "n": st["n"], "mean": st["mean"],
               "pos_frac": st["pos_frac"], "skew": st["skew"], "null_mean": null_mean,
               "null_max": max(dist), "p_one": p_one, "n_files": len(per_file),
               "n_positive": n_pos, "nperm": args.nperm, "per_file": per_file},
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written:", out_path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
