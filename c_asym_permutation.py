# -*- coding: utf-8 -*-
"""
c_asym_permutation.py — §5.4 C 语料的同协议验证（tree-sitter C 口径）

与 Python 版 d_asym_permutation.py 完全同一协议：
 1. tree-sitter 解析 C 源码，按源码顺序提取符号叶子；
    token = (结构路径 p, 符号 τ)：p = 最近 depth 个 named 祖先节点类型；
    τ = 抽象符号（identifier/field_identifier→id；type_identifier/primitive_type/
    sized_type_specifier→type；number_literal→num；string_literal→str；
    char_literal→char；关键字（return/if/…）→关键字名；算符（+、==、…）→算符；
    跳过 ( ) , ; { } 与注释）。
 2. 正向计数 (p_i→τ_i)、反向计数 (p_{i+1}→τ_i)，add-1 平滑。
 3. D_asym(i) = log P_f(τ_i|p_i) − log P_b(τ_i|p_{i+1})。
 4. ⟨D_asym⟩ 与 S(δ)（δ = 反向符号边际 − 正向符号边际）。
 5. 两类零假设置换检验（打乱符号 / 打乱路径），模型随置换重估。

运行环境要求：tree-sitter（0.25/0.26）与 tree-sitter-c（0.25/0.26，胶囊 ABI 须匹配）；
即论文 v1/v2 管线所用的环境。用法：
  python c_asym_permutation.py --roots <musl> <libuv> <libtiff> <zlib> \
      --depth 5 --nperm 1000 --maxfiles 0 --out perm_c.json

c_asym_permutation.py — same-protocol verification on a C corpus in §5.4 (tree-sitter C protocol).
Exactly the same protocol as the Python version d_asym_permutation.py: (1) tree-sitter parses C source and extracts the symbolic leaves in source order; token = (structural path p, symbol τ), where p = the chain of the nearest depth named ancestor node types and τ = an abstract symbol (identifier/field_identifier→id; type_identifier/primitive_type/sized_type_specifier→type; number_literal→num; string_literal→str; char_literal→char; keywords (return/if/…)→keyword name; operators (+, ==, …)→operator; ( ) , ; { } and comments are skipped). (2) Forward counts (p_i→τ_i) and backward counts (p_{i+1}→τ_i), add-1 smoothing. (3) D_asym(i) = log P_f(τ_i|p_i) − log P_b(τ_i|p_{i+1}). (4) ⟨D_asym⟩ and S(δ) (δ = backward symbol marginal − forward symbol marginal). (5) Two null-hypothesis permutation tests (shuffle symbols / shuffle paths), with the model re-estimated after each permutation. Runtime requirements: tree-sitter (0.25/0.26) and tree-sitter-c (0.25/0.26, the capsule ABI must match), i.e. the environment used by the paper's v1/v2 pipeline. Usage: python c_asym_permutation.py --roots <musl> <libuv> <libtiff> <zlib> --depth 5 --nperm 1000 --maxfiles 0 --out perm_c.json
"""
import argparse
import json
import math
import os
import random
import time
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from tree_sitter import Language, Parser
import tree_sitter_c

DEPTH = 5
KEYWORDS = {
    "return", "if", "else", "for", "while", "do", "switch", "case", "default",
    "break", "continue", "goto", "sizeof", "struct", "union", "enum", "typedef",
    "static", "extern", "const", "volatile", "register", "inline", "void",
    "char", "short", "int", "long", "float", "double", "signed", "unsigned",
}
SKIP_ANON = {"(", ")", "[", "]", "{", "}", ",", ";", ".", "->", "comment"}

def build_parser():
    lang = Language(tree_sitter_c.language())
    return Parser(lang)

def collect_tokens(parser, src, depth):
    tree = parser.parse(src)  # tree-sitter 0.26：parse 接受 bytes（勿再 .encode） / tree-sitter 0.26: parse accepts bytes (do not call .encode again)
    tokens = []
    root = tree.root_node

    def walk(node, named_ancestors):
        if node.child_count == 0:
            if node.is_named:
                sym = abstract_named(node.type, node)
                if sym is not None:
                    tokens.append((tuple(named_ancestors[-depth:]), sym))
            else:
                if node.type not in SKIP_ANON:
                    tokens.append((tuple(named_ancestors[-depth:]), node.type))
            return
        if node.is_named:
            named_ancestors = named_ancestors + [node.type]
        for child in node.children:
            walk(child, named_ancestors)

    walk(root, [])
    return tokens

def abstract_named(t, node):
    if t in ("identifier", "field_identifier"):
        return "id"
    if t in ("type_identifier", "primitive_type", "sized_type_specifier"):
        return "type"
    if t == "number_literal":
        return "num"
    if t == "string_literal":
        return "str"
    if t == "char_literal":
        return "char"
    if t in ("true", "false", "null"):
        return t
    return None

# —— 以下与 d_asym_permutation.py 同构 —— / Below this point the code is isomorphic to d_asym_permutation.py

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
    n = len(tokens)
    if n < 2:
        return [], 0.0
    fwd, bwd = build_counts(tokens)
    fwd_marg, bwd_marg = {}, {}
    for (p, t), c in fwd.items():
        fwd_marg[p] = fwd_marg.get(p, 0) + c
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
    f, b = {}, {}
    for (p, t), c in fwd.items():
        f[t] = f.get(t, 0) + c
    for (p, t), c in bwd.items():
        b[t] = b.get(t, 0) + c
    n_b = n - 1
    num = den = 0.0
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
    """maxfiles 为每个仓库的文件数上限（0=不限），保证多仓库均衡采样。
    maxfiles caps the number of files per repository (0 = unlimited), ensuring balanced sampling across repositories."""
    for root in roots:
        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", "tests", "test"}]
            for fn in sorted(filenames):
                if fn.endswith((".c", ".h")):
                    fp = os.path.join(dirpath, fn)
                    try:
                        if os.path.getsize(fp) > 200_000:
                            continue
                    except OSError:
                        continue
                    yield fp
                    count += 1
                    if maxfiles and count >= maxfiles:
                        break
            if maxfiles and count >= maxfiles:
                break

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--nperm", type=int, default=1000)
    ap.add_argument("--maxfiles", type=int, default=0,
                    help="每个仓库的文件数上限（0=不限）")
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    t0 = time.time()
    parser = build_parser()
    import tree_sitter as _ts
    print(f"[env] tree_sitter={getattr(_ts, '__version__', '?')} "
          f"tree_sitter_c={getattr(tree_sitter_c, '__version__', '?')}", flush=True)
    per_file = []
    all_tokens = []
    n_parse_fail = n_files = 0
    parse_errors = []
    for fp in iter_files(args.roots, args.maxfiles):
        n_files += 1
        try:
            with open(fp, "rb") as f:
                src = f.read()          # bytes 直接传给 parse / bytes are passed directly to parse
            toks = collect_tokens(parser, src, args.depth)
        except Exception as e:
            n_parse_fail += 1
            if len(parse_errors) < 3:
                parse_errors.append(f"{os.path.basename(fp)}: {type(e).__name__}: {e}")
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
    for pe in parse_errors:
        print(f"[parse-error] {pe}", flush=True)

    N = len(all_tokens)
    print(f"[corpus] depth={args.depth} files={n_files} parsed={n_files - n_parse_fail} "
          f"skipped_fail={n_parse_fail} tokens={N}", flush=True)
    if N < 2:
        print("[error] 语料为空或 token 不足（<2）。请检查 --roots 路径是否存在、"
              "目录内是否有 .c/.h 文件（注意：每个文件需 ≥50 个 token 才计入统计）。",
              flush=True)
        sys.exit(1)
    seq_real, real_mean = eval_stat(all_tokens)
    pos_frac = sum(1 for x in seq_real if x > 0) / len(seq_real)
    fwd_all, bwd_all = build_counts(all_tokens)
    V = len({t for _, t in all_tokens})
    skew_real = skew_delta(fwd_all, bwd_all, N, V)
    print(f"[corpus] <D_asym>={real_mean:.6f}  S(delta)={skew_real:.6f}  "
          f"positive_frac={pos_frac:.4f}")
    print(f"[sign-check] sign(<D_asym>)={1 if real_mean > 0 else -1}, "
          f"sign(S(delta))={1 if skew_real > 0 else -1}, "
          f"预期相反: {'OK' if real_mean * skew_real < 0 else 'FAIL'}")

    dist_a, dist_b = [], []
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
        return min(1.0, 2.0 * min(p1, p2)) if two_sided else p1

    mean_a = sum(dist_a) / len(dist_a)
    mean_b = sum(dist_b) / len(dist_b)
    print(f"[null-a 打乱符号]  null mean={mean_a:.6f}  p(单侧)={pval(dist_a, real_mean, two_sided=False):.4f}")
    print(f"[null-b 打乱路径]  null mean={mean_b:.6f}  p(单侧)={pval(dist_b, real_mean, two_sided=False):.4f}")
    pos_files = sum(1 for _, _, m, _, _ in per_file if m > 0)
    sign_agree = sum(1 for _, _, m, sk, _ in per_file if m * sk < 0)
    print(f"[per-file] 文件数={len(per_file)}  ⟨D_asym⟩>0={pos_files}  符号一致性={sign_agree}/{len(per_file)}")

    out = {
        "depth": args.depth, "real_mean": real_mean, "skew_delta": skew_real,
        "sign_check_ok": real_mean * skew_real < 0, "positive_frac": pos_frac,
        "n_tokens": N, "n_files": n_files, "n_parse_fail": n_parse_fail,
        "null_a_mean": mean_a, "null_b_mean": mean_b,
        "p_one_sided_a": pval(dist_a, real_mean, two_sided=False),
        "p_one_sided_b": pval(dist_b, real_mean, two_sided=False),
        "null_a_dist": dist_a, "null_b_dist": dist_b,
        "nperm": args.nperm, "seed": args.seed,
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
