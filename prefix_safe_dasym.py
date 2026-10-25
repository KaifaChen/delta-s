# -*- coding: utf-8 -*-
"""前缀安全子集上的 ⟨ΔS⟩ 重跑（P1）。

Prefix-safe subset rerun of ⟨ΔS⟩.
安全定义 / safety: token 的所有 **有位置** 祖先前缀起点严格早于 token 起点。
无位置 token（算子等）不计入安全子集（保守）。
对照 / control: 同一批文件的 full-AST 全部 token。
"""
import ast
import json
import math
import os
import random
import sys

GH = r"E:\LOGIC AI\logic papers\DELTA S\github_scripts"
sys.path.insert(0, GH)
import d_asym_permutation as dap  # noqa: E402

LIST = os.path.join(GH, "files_author_d5.txt")
DEPTH = 5
NPERM = 1000


def node_pos(n):
    ln = getattr(n, "lineno", None)
    co = getattr(n, "col_offset", None)
    return None if ln is None or co is None else (ln, co)


def collect_with_flags(src, depth):
    """返回 [(path, symbol, safe, has_pos), ...] / returns path, symbol, safety flag."""
    tree = ast.parse(src)
    out = []
    stack = []

    def walk(node):
        sym = dap.leaf_symbol(node)
        if sym is not None:
            path = tuple(type(a).__name__ for a in stack[-depth:])
            tp = node_pos(node)
            if tp is None:
                out.append((path, sym, False, False))
            else:
                safe = all(node_pos(a) is None or node_pos(a) < tp for a in stack)
                out.append((path, sym, safe, True))
            return
        stack.append(node)
        for ch in ast.iter_child_nodes(node):
            walk(ch)
        stack.pop()

    walk(tree)
    return out


def stats(tokens):
    """⟨ΔS⟩、正号比例、S(δ)、逐 token 序列。"""
    seq, mean = dap.eval_stat(tokens)
    fwd, bwd = dap.build_counts(tokens)
    v = len({t for _, t in tokens})
    return {
        "n": len(tokens),
        "mean": mean,
        "pos_frac": sum(1 for x in seq if x > 0) / len(seq),
        "skew": dap.skew_delta(fwd, bwd, len(tokens), v),
        "seq": seq,
    }


def main():
    files = [ln.strip() for ln in open(LIST, encoding="utf-8") if ln.strip()]
    all_toks, safe_toks = [], []
    per_file = []
    n_safe = n_all = n_nopos = 0
    used = 0
    for fp in files:
        if not os.path.exists(fp):
            continue
        try:
            src = open(fp, encoding="utf-8-sig", errors="replace").read()
            toks = collect_with_flags(src, DEPTH)
        except (SyntaxError, ValueError, UnicodeError):
            continue
        used += 1
        a = [(p, s) for p, s, _, _ in toks]
        sf = [(p, s) for p, s, safe, _ in toks if safe]
        n_all += len(a)
        n_safe += len(sf)
        n_nopos += sum(1 for _, _, _, hp in toks if not hp)
        all_toks += a
        safe_toks += sf
        if len(sf) >= 50:
            sa = stats(sf)
            per_file.append((os.path.basename(fp), sa["mean"], sa["skew"]))

    print("文件数: %d | 全部 token: %d | 前缀安全: %d (%.1f%%) | 无位置: %d"
          % (used, n_all, n_safe, 100.0 * n_safe / max(n_all, 1), n_nopos))
    print()

    res = {}
    for name, toks in (("full-AST", all_toks), ("prefix-safe", safe_toks)):
        st = stats(toks)
        rng = random.Random(20260929)
        nulls = []
        for k in range(NPERM):
            r2 = random.Random(20260929 + 1000 + k)
            _, m = dap.eval_stat(dap.permute_symbols(toks, r2))
            nulls.append(m)
        null_mean = sum(nulls) / len(nulls)
        p1 = (sum(1 for x in nulls if x >= st["mean"]) + 1) / (len(nulls) + 1)
        res[name] = dict(n=st["n"], mean=st["mean"], pos_frac=st["pos_frac"],
                         skew=st["skew"], null_mean=null_mean, p_one=p1,
                         null_max=max(nulls))
        print("%-12s n=%6d  <DeltaS>=%+.4f  pos_frac=%.3f  S(delta)=%+.3f  "
              "null_mean=%+.5f  null_max=%+.4f  p_one=%.4f"
              % (name, st["n"], st["mean"], st["pos_frac"], st["skew"],
                 null_mean, max(nulls), p1))

    print()
    print("逐文件（前缀安全，n≥50）：%d 个文件，mean>0 = %d，符号一致 = %d"
          % (len(per_file),
             sum(1 for _, m, _ in per_file if m > 0),
             sum(1 for _, m, sk in per_file if m * sk < 0)))

    out = {"files": used, "tokens_all": n_all, "tokens_safe": n_safe,
           "nopos": n_nopos, "results": res,
           "per_file_safe": [{"file": f, "mean": m, "skew": s} for f, m, s in per_file]}
    with open(os.path.join(GH, "prefix_safe_result.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written prefix_safe_result.json")


if __name__ == "__main__":
    main()
