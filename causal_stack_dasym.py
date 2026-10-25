# -*- coding: utf-8 -*-
"""前缀因果结构路径（tokenize 栈）上的 ⟨ΔS⟩ 重跑（P2）。

⟨ΔS⟩ on the prefix-causal structure path (a tokenize-based stack).

与 prefix-safe 子集不同，本口径**重构**而不是丢弃未来依赖 token：用 `tokenize` 顺序读 token，
只维护"已读前缀中已打开的结构"栈，因此路径天然是前缀的函数 p=f(K)。

Unlike the prefix-safe subset, this convention *reconstructs* rather than drops tokens: it reads the
token stream with `tokenize` and maintains only the structures already open in the prefix, so the path
is a function of the prefix by construction.

结构栈（沿用 v3 `m0_causal_path.causal_tokens` 的定义 / stack definition follows v3 m0_causal_path）:
  - compound: def/class/if/elif/else/for/while/with/try/except/finally（DEDENT 弹）
  - bracket:  ( ) [ ] { }；`(` 前是 NAME/字面量/闭括号 → Call，def 后的 `(` → parameters，否则 Tuple；
              `[` 前是 NAME → Subscript，否则 List；`{` → Dict
  - stmt:     `=` → Assign；比较/算术算符 → Compare/BinOp；return/import/… → 对应标签（NEWLINE 弹）
  - `.` 后的 NAME 临时加 Attribute
用法 / Usage: python causal_stack_dasym.py [--depth 5] [--nperm 1000] [--out causal_stack_result.json]
"""
import argparse
import io
import json
import os
import random
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402

COMPOUND = {
    "def": "FunctionDef", "class": "ClassDef",
    "if": "If", "elif": "If", "else": "If",
    "for": "For", "while": "While", "with": "With",
    "try": "Try", "except": "Try", "finally": "Try",
}
STMT = {
    "return": "Return", "yield": "Yield", "raise": "Raise",
    "assert": "Assert", "import": "Import", "from": "Import",
    "global": "Global", "nonlocal": "Nonlocal", "del": "Delete",
}
CMP = {"==", "!=", "<", ">", "<=", ">=", "is", "in", "not"}
ARITH = {"+", "-", "*", "/", "//", "%", "**", "|", "&", "^", "<<", ">>"}


def causal_tokens(src, depth):
    """返回 [(path, sym)]：path 只由已读前缀决定。
    Returns [(path, sym)] where path depends only on the prefix read so far."""
    out = []
    compound, brackets, stmt = [], [], []
    prev = None
    def_params = False
    attr_pending = 0
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception:
        return out
    for tok in toks:
        t, s = tok.type, tok.string
        if t == tokenize.NEWLINE:
            stmt.clear()
            def_params = False
            continue
        if t == tokenize.DEDENT:
            if compound:
                compound.pop()
            continue
        if t in (tokenize.INDENT, tokenize.COMMENT, tokenize.NL,
                 tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if t in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
            path = ["Module"] + compound + stmt + brackets
            if attr_pending and t == tokenize.NAME:
                path = path + ["Attribute"]
                attr_pending = 0
            out.append((tuple(path[-depth:]), s))
            if t == tokenize.NAME:
                if s in COMPOUND:
                    compound.append(COMPOUND[s])
                    if s == "def":
                        def_params = True
                elif s in STMT:
                    stmt.append(STMT[s])
            prev = (t, s)
            continue
        if t == tokenize.OP:
            if s == "(":
                if def_params:
                    brackets.append("parameters")
                    def_params = False
                elif prev is not None and (prev[0] in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
                                           or prev[1] in (")", "]", "}")):
                    brackets.append("Call")
                else:
                    brackets.append("Tuple")
            elif s == "[":
                if prev is not None and (prev[0] in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
                                         or prev[1] in (")", "]", "}")):
                    brackets.append("Subscript")
                else:
                    brackets.append("List")
            elif s == "{":
                brackets.append("Dict")
            elif s in (")", "]", "}"):
                if brackets:
                    brackets.pop()
            elif s == ".":
                attr_pending = 1
            elif s == "=":
                stmt.append("Assign")
            elif s in CMP:
                stmt.append("Compare")
            elif s in ARITH:
                stmt.append("BinOp")
            prev = (t, s)
            continue
    return out


def stats(tokens):
    seq, mean = dap.eval_stat(tokens)
    fwd, bwd = dap.build_counts(tokens)
    v = len({t for _, t in tokens})
    return {"n": len(tokens), "mean": mean,
            "pos_frac": sum(1 for x in seq if x > 0) / len(seq),
            "skew": dap.skew_delta(fwd, bwd, len(tokens), v)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--nperm", type=int, default=1000)
    ap.add_argument("--out", default=os.path.join(HERE, "causal_stack_result.json"))
    ap.add_argument("--filelist", default=os.path.join(HERE, "files_author_d5.txt"))
    args = ap.parse_args()

    files = [ln.strip() for ln in open(args.filelist, encoding="utf-8") if ln.strip()]
    all_toks, per_file = [], []
    used = 0
    for fp in files:
        if not os.path.exists(fp):
            continue
        try:
            src = open(fp, encoding="utf-8-sig", errors="replace").read()
            toks = causal_tokens(src, args.depth)
        except Exception:
            continue
        if len(toks) < 50:
            continue
        used += 1
        all_toks += toks
        st = stats(toks)
        per_file.append({"file": fp, "n": st["n"], "mean": st["mean"], "skew": st["skew"]})

    st = stats(all_toks)
    print("文件数: %d | token: %d | <DeltaS>=%+.4f | pos_frac=%.3f | S(delta)=%+.3f"
          % (used, st["n"], st["mean"], st["pos_frac"], st["skew"]))

    dist = []
    for k in range(args.nperm):
        r2 = random.Random(20260929 + 1000 + k)
        _, m = dap.eval_stat(dap.permute_symbols(all_toks, r2))
        dist.append(m)
    null_mean = sum(dist) / len(dist)
    p_one = (sum(1 for x in dist if x >= st["mean"]) + 1) / (len(dist) + 1)
    print("置换: n=%d  null_mean=%+.5f  null_max=%+.4f  p_one=%.4f"
          % (len(dist), null_mean, max(dist), p_one))

    n_pos = sum(1 for f in per_file if f["mean"] > 0)
    n_agree = sum(1 for f in per_file if f["mean"] * f["skew"] < 0)
    print("逐文件: %d 个 (n>=50)；mean>0 = %d；符号一致 = %d" % (len(per_file), n_pos, n_agree))

    out = {"depth": args.depth, "files": used, "n_tokens": st["n"],
           "real_mean": st["mean"], "positive_frac": st["pos_frac"], "skew_delta": st["skew"],
           "null_mean": null_mean, "null_max": max(dist), "p_one_sided": p_one,
           "nperm": args.nperm, "n_files": len(per_file),
           "n_files_positive": n_pos, "n_files_sign_agree": n_agree,
           "null_a_dist": dist, "per_file": per_file}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written:", args.out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
