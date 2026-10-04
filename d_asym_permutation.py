# -*- coding: utf-8 -*-
"""
d_asym_permutation.py — §5.4 置换检验实验（Python AST 结构路径口径）

协议（对应工作稿 §5.2，纯标准库实现，可复现）：
 1. ast 解析 Python 源码，按源码顺序提取符号叶子（Name/Constant/keyword/operator）；
    每个 token 记 (结构路径 p, 符号 τ)：p = 祖先节点类型链（深度 ≤ depth）。
 2. 正向计数 P_f(τ|p)：位置 i 的路径 p_i 预测符号 τ_i；
    反向计数 P_b(τ|p')：下一位置路径 p_{i+1} 预测当前符号 τ_i；add-1 平滑。
 3. 逐 token 不对称差 D_asym(i) = log P_f(τ_i|p_i) − log P_b(τ_i|p_{i+1})。
 4. 全局 ⟨D_asym⟩ = 均值；另报方向性偏斜 S(δ) = Σδ³/P_f² / (Σδ²/P_f)^{3/2}，
    其中 δ = 反向符号边际 − 正向符号边际（§4.7 差向量展开的归一化三阶量，
    理论预期 sign(⟨D_asym⟩) = −sign(S(δ))，见工作稿 §4.7/§4.8）。
 5. 两类零假设置换检验（模型随置换重估）：
    (a) 打乱符号序列 τ（路径顺序保留）；
    (b) 打乱路径序列 p（符号顺序保留）。
    自检：置换分布的均值应 ≈ 0。
用法：
  python d_asym_permutation.py --roots <dir...> [--depth 5] [--nperm 1000]
        [--maxfiles 0] [--seed 20260929] [--out result.json]

d_asym_permutation.py — the §5.4 permutation-test experiment (Python-AST structural-path protocol).
Protocol (per working draft §5.2; pure standard library, reproducible): (1) parse Python source with ast and extract the symbolic leaves (Name/Constant/keyword/operator) in source order; each token is recorded as (structural path p, symbol τ), where p = the chain of ancestor node types (depth ≤ depth). (2) Forward counts P_f(τ|p): the path p_i at position i predicts the symbol τ_i; backward counts P_b(τ|p'): the path p_{i+1} at the next position predicts the current symbol τ_i; add-1 smoothing. (3) Per-token asymmetry D_asym(i) = log P_f(τ_i|p_i) − log P_b(τ_i|p_{i+1}). (4) Global ⟨D_asym⟩ = mean; also report the directional skew S(δ) = Σδ³/P_f² / (Σδ²/P_f)^{3/2}, where δ = backward symbol marginal − forward symbol marginal (the normalized third-order quantity of the §4.7 difference-vector expansion; theory predicts sign(⟨D_asym⟩) = −sign(S(δ)), see working draft §4.7/§4.8). (5) Two null-hypothesis permutation tests (the model is re-estimated after each permutation): (a) shuffle the symbol sequence τ (path order preserved); (b) shuffle the path sequence p (symbol order preserved). Self-check: the means of the permutation distributions should be ≈ 0. Usage: python d_asym_permutation.py --roots <dir...> [--depth 5] [--nperm 1000] [--maxfiles 0] [--seed 20260929] [--out result.json]
"""
import ast
import os
import sys
import math
import random
import json
import time
import argparse

def leaf_symbol(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        v = node.value
        if v is None or isinstance(v, bool):
            return type(v).__name__
        if isinstance(v, (int, float, complex)):
            return "num"
        if isinstance(v, str):
            return "str"
        return "const"
    if isinstance(node, ast.keyword):
        return node.arg if node.arg else "**"
    if isinstance(node, (ast.operator, ast.unaryop, ast.cmpop, ast.boolop)):
        return type(node).__name__
    return None

def collect_tokens(src, depth):
    """按源码顺序返回 [(path_tuple, symbol), ...]
    Returns [(path_tuple, symbol), ...] in source order."""
    tree = ast.parse(src)
    tokens = []
    stack = []

    def walk(node):
        sym = leaf_symbol(node)
        if sym is not None:
            path = tuple(stack[-depth:])
            tokens.append((path, sym))
            return
        stack.append(type(node).__name__)
        for child in ast.iter_child_nodes(node):
            walk(child)
        stack.pop()

    walk(tree)
    return tokens

def build_counts(tokens):
    n = len(tokens)
    fwd = {}
    bwd = {}
    for i in range(n):
        p, t = tokens[i]
        fwd[(p, t)] = fwd.get((p, t), 0) + 1
        if i + 1 < n:
            pn, _ = tokens[i + 1]
            bwd[(pn, t)] = bwd.get((pn, t), 0) + 1
    return fwd, bwd

def eval_stat(tokens):
    """由 tokens 估计模型并返回 (seq, mean)。模型随 tokens 重估（置换后亦然）。
    Estimates the model from the tokens and returns (seq, mean); the model is re-estimated from the tokens (likewise after permutation)."""
    n = len(tokens)
    if n < 2:
        return [], 0.0
    fwd, bwd = build_counts(tokens)
    fwd_marg = {}
    for (p, t), c in fwd.items():
        fwd_marg[p] = fwd_marg.get(p, 0) + c
    bwd_marg = {}
    for (p, t), c in bwd.items():
        bwd_marg[p] = bwd_marg.get(p, 0) + c
    v = len({t for _, t in tokens})
    seq = []
    for i in range(n - 1):
        p, t = tokens[i]
        pn, _ = tokens[i + 1]
        lp_f = math.log((fwd.get((p, t), 0) + 1) / (fwd_marg.get(p, 0) + v))
        lp_b = math.log((bwd.get((pn, t), 0) + 1) / (bwd_marg.get(pn, 0) + v))
        seq.append(lp_f - lp_b)
    return seq, sum(seq) / len(seq)

def skew_delta(fwd, bwd, n, v):
    """S(δ) = Σδ³/f² / (Σδ²/f)^{3/2}，δ = 反向符号边际 − 正向符号边际（+1 平滑）
    S(δ) = Σδ³/f² / (Σδ²/f)^{3/2}, where δ = backward symbol marginal − forward symbol marginal (+1 smoothing)."""
    f = {}
    for (p, t), c in fwd.items():
        f[t] = f.get(t, 0) + c
    b = {}
    for (p, t), c in bwd.items():
        b[t] = b.get(t, 0) + c
    n_b = n - 1
    num = 0.0
    den = 0.0
    for t in sorted(set(f) | set(b)):
        pf = (f.get(t, 0) + 1) / (n + v)
        pb = (b.get(t, 0) + 1) / (n_b + v)
        d = pb - pf
        num += d ** 3 / (pf * pf)
        den += d * d / pf
    return num / (den ** 1.5) if den > 0 else 0.0

def permute_symbols(tokens, rng):
    ts = [t for _, t in tokens]
    rng.shuffle(ts)
    return [(p, t) for (p, _), t in zip(tokens, ts)]

def permute_paths(tokens, rng):
    ps = [p for p, _ in tokens]
    rng.shuffle(ps)
    return [(p, t) for p, (_, t) in zip(ps, tokens)]

def iter_files(roots, maxfiles=0):
    skip_dirs = {"repos", "data", ".venvs", ".pypkgs", "node_modules",
                 "build", "vx_images", "Zenodo_v3.0_主线总论文", ".git",
                 "__pycache__", "vx_notebook", "vx_recycle_bin", "tests",
                 "site-packages", "test", "testsuite"}
    count = 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fn in sorted(filenames):
                if fn.endswith(".py"):
                    fp = os.path.join(dirpath, fn)
                    try:
                        if os.path.getsize(fp) > 400_000:
                            continue
                    except OSError:
                        continue
                    yield fp
                    count += 1
                    if maxfiles and count >= maxfiles:
                        return

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--nperm", type=int, default=1000)
    ap.add_argument("--maxfiles", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    t0 = time.time()
    rng = random.Random(args.seed)

    per_file = []
    all_tokens = []
    n_parse_fail = 0
    n_files = 0
    for fp in iter_files(args.roots, args.maxfiles):
        n_files += 1
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
            toks = collect_tokens(src, args.depth)
        except (SyntaxError, ValueError, UnicodeError):
            n_parse_fail += 1
            continue
        if len(toks) < 50:
            continue
        seq, mean = eval_stat(toks)
        fwd, bwd = build_counts(toks)
        v = len({t for _, t in toks})
        sk = skew_delta(fwd, bwd, len(toks), v)
        per_file.append((fp, len(toks), mean, sk,
                         sum(1 for x in seq if x > 0) / len(seq)))
        all_tokens.extend(toks)

    N = len(all_tokens)
    seq_real, real_mean = eval_stat(all_tokens)
    pos_frac = sum(1 for x in seq_real if x > 0) / len(seq_real)
    fwd_all, bwd_all = build_counts(all_tokens)
    V = len({t for _, t in all_tokens})
    skew_real = skew_delta(fwd_all, bwd_all, N, V)
    print(f"[corpus] depth={args.depth} files={n_files} parsed={n_files-n_parse_fail} "
          f"skipped_fail={n_parse_fail}")
    print(f"[corpus] tokens={N}  <D_asym>={real_mean:.6f}  S(delta)={skew_real:.6f}  "
          f"positive_frac={pos_frac:.4f}")
    print(f"[sign-check] sign(<D_asym>)={1 if real_mean > 0 else -1}, "
          f"sign(S(delta))={1 if skew_real > 0 else -1}, "
          f"预期相反: {'OK' if real_mean * skew_real < 0 else 'FAIL'}")

    # 置换检验 / Permutation tests
    dist_a = []
    dist_b = []
    for k in range(args.nperm):
        rng2 = random.Random(args.seed + 1000 + k)
        _, m_a = eval_stat(permute_symbols(all_tokens, rng2))
        dist_a.append(m_a)
        _, m_b = eval_stat(permute_paths(all_tokens, rng2))
        dist_b.append(m_b)
        if (k + 1) % 200 == 0:
            print(f"  perm {k+1}/{args.nperm}  t={time.time()-t0:.0f}s", flush=True)

    def pval(dist, val, two_sided=True):
        n = len(dist)
        ge = sum(1 for x in dist if x >= val)
        le = sum(1 for x in dist if x <= val)
        p1 = (ge + 1) / (n + 1)
        p2 = (le + 1) / (n + 1)
        if not two_sided:
            return p1
        return min(1.0, 2.0 * min(p1, p2))

    mean_a = sum(dist_a) / len(dist_a)
    mean_b = sum(dist_b) / len(dist_b)
    print(f"[null-a 打乱符号]  null mean={mean_a:.6f}  p(单侧)={pval(dist_a, real_mean, two_sided=False):.4f}  p(双侧)={pval(dist_a, real_mean):.4f}")
    print(f"[null-b 打乱路径]  null mean={mean_b:.6f}  p(单侧)={pval(dist_b, real_mean, two_sided=False):.4f}  p(双侧)={pval(dist_b, real_mean):.4f}")
    print(f"[self-check] null-a mean={abs(mean_a):.2e};  null-b mean={abs(mean_b):.2e}  (应≈0)")

    pos_files = sum(1 for _, _, m, _, _ in per_file if m > 0)
    sign_agree = sum(1 for _, _, m, sk, _ in per_file if m * sk < 0)
    print(f"[per-file] 文件数={len(per_file)}  ⟨D_asym⟩>0 文件数={pos_files}  "
          f"符号一致性(⟨D_asym⟩与−S(δ)同号)={sign_agree}/{len(per_file)}")

    out = {
        "depth": args.depth,
        "real_mean": real_mean,
        "skew_delta": skew_real,
        "sign_check_ok": real_mean * skew_real < 0,
        "positive_frac": pos_frac,
        "n_tokens": N,
        "n_files": n_files,
        "n_parse_fail": n_parse_fail,
        "null_a_mean": mean_a,
        "null_b_mean": mean_b,
        "p_two_sided_a": pval(dist_a, real_mean),
        "p_two_sided_b": pval(dist_b, real_mean),
        "p_one_sided_a": pval(dist_a, real_mean, two_sided=False),
        "p_one_sided_b": pval(dist_b, real_mean, two_sided=False),
        "null_a_dist": dist_a,
        "null_b_dist": dist_b,
        "nperm": args.nperm,
        "seed": args.seed,
        "per_file": [{"file": fp, "tokens": n, "mean": m, "skew": sk, "pos_frac": pf}
                     for fp, n, m, sk, pf in per_file],
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"[out] {args.out}")
    print(f"[done] total time {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
