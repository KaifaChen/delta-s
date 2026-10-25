# -*- coding: utf-8 -*-
"""2×2×2 对照（修正版）：路径(完整/截断) × 顺序(AST/源码) × 算子(保留/丢弃)。

Clean 2x2x2 control, corrected:
 - 算子节点本身没有位置；源码序时用"前一个有位置兄弟的结束位置"作为它的排序键，
   从而把它放在正确的源码位置（左操作数之后、右操作数之前）。
 - --ops drop 才是真的丢弃（用布尔量判断）。
"""
import argparse
import ast
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402


def start(n):
    ln = getattr(n, "lineno", None)
    co = getattr(n, "col_offset", None)
    return None if ln is None or co is None else (ln, co)


def end(n):
    ln = getattr(n, "end_lineno", None)
    co = getattr(n, "end_col_offset", None)
    return None if ln is None or co is None else (ln, co)


def collect(src, depth, path_mode, order, keep_ops):
    tree = ast.parse(src)
    out = []
    stack = []

    def walk(node, key_hint):
        sym = dap.leaf_symbol(node)
        if sym is not None:
            is_op = isinstance(node, (ast.operator, ast.unaryop, ast.cmpop, ast.boolop))
            if is_op and not keep_ops:
                return
            sp = start(node)
            if path_mode == "trunc":
                keep = 0
                for a in stack:
                    ap = start(a)
                    if ap is None:
                        if isinstance(a, ast.Module):
                            keep += 1
                            continue
                        break
                    if sp is not None and ap < sp:
                        keep += 1
                    else:
                        break
                path = tuple(type(a).__name__ for a in stack[:keep][-depth:])
            else:
                path = tuple(type(a).__name__ for a in stack[-depth:])
            key = sp if sp is not None else key_hint
            out.append((path, sym, key))
            return
        stack.append(node)
        prev_end = start(node) or (0, 0)
        for ch in ast.iter_child_nodes(node):
            walk(ch, prev_end)
            e = end(ch)
            if e is not None:
                prev_end = e
        stack.pop()

    walk(tree, (0, 0))
    if order == "sorted":
        out = [t for t in out if t[2] is not None]
        out.sort(key=lambda t: t[2])
    return [(p, s) for p, s, _ in out]


def stats(tokens):
    seq, mean = dap.eval_stat(tokens)
    fwd, bwd = dap.build_counts(tokens)
    v = len({t for _, t in tokens})
    return len(tokens), mean, sum(1 for x in seq if x > 0) / len(seq), dap.skew_delta(fwd, bwd, len(tokens), v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", choices=["full", "trunc"], required=True)
    ap.add_argument("--order", choices=["ast", "sorted"], required=True)
    ap.add_argument("--ops", choices=["keep", "drop"], required=True)
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--nperm", type=int, default=300)
    ap.add_argument("--filelist", default=os.path.join(HERE, "files_author_d5.txt"))
    args = ap.parse_args()
    keep_ops = (args.ops == "keep")

    files = [ln.strip() for ln in open(args.filelist, encoding="utf-8") if ln.strip()]
    toks_all = []
    for fp in files:
        if not os.path.exists(fp):
            continue
        try:
            src = open(fp, encoding="utf-8-sig", errors="replace").read()
            t = collect(src, args.depth, args.path, args.order, keep_ops)
        except Exception:
            continue
        if len(t) >= 50:
            toks_all += t

    n, mean, posf, sk = stats(toks_all)
    dist = []
    for k in range(args.nperm):
        r2 = random.Random(20260929 + 1000 + k)
        _, m = dap.eval_stat(dap.permute_symbols(toks_all, r2))
        dist.append(m)
    p1 = (sum(1 for x in dist if x >= mean) + 1) / (len(dist) + 1)
    print("%-5s %-6s %-4s d=%d | n=%6d | <DeltaS>=%+.4f | pos=%.3f | p_one=%.3f | S(delta)=%+.2f"
          % (args.path, args.order, args.ops, args.depth, n, mean, posf, p1, sk))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
