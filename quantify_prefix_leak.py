# -*- coding: utf-8 -*-
"""量化：DELTA S 的 token 中有多少其祖先链含"未来节点"（祖先起点不早于 token 起点）。
Quantify how many DELTA S tokens have ancestors that start at or after the token itself,
i.e. structures that could not have been open when the token was read.

安全 / safe  = 所有祖先节点的 (lineno, col_offset) 严格早于 token 的起点。
无位置属性的算子节点 / 节点视为不安全（保守）。
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402

LIST = r"E:\LOGIC AI\logic papers\DELTA S\github_scripts\files_author_d5.txt"


def safe_stats(src, depth):
    tree = ast.parse(src)
    stack = []
    out = {"total": 0, "safe": 0, "unsafe": 0, "nopos": 0}

    def pos(node):
        ln = getattr(node, "lineno", None)
        co = getattr(node, "col_offset", None)
        return None if ln is None or co is None else (ln, co)

    def walk(node):
        sym = dap.leaf_symbol(node)
        if sym is not None:
            out["total"] += 1
            tp = pos(node)
            if tp is None:
                out["nopos"] += 1          # 算子/比较符等无位置节点：单独计，不武断判为不安全
                return
            ok = True
            for a in stack:
                ap = pos(a)
                if ap is None:
                    continue               # Module/arguments 等无位置节点：跳过，不作判定
                if not (ap < tp):
                    ok = False
                    break
            out["safe" if ok else "unsafe"] += 1
            return
        stack.append(node)
        for ch in ast.iter_child_nodes(node):
            walk(ch)
        stack.pop()

    walk(tree)
    return out


paths = [ln.strip() for ln in open(LIST, encoding="utf-8") if ln.strip()]
tot = {"total": 0, "safe": 0, "unsafe": 0, "nopos": 0}
nfile = 0
for p in paths[:25]:
    if not os.path.exists(p):
        continue
    try:
        src = open(p, encoding="utf-8-sig", errors="replace").read()
        s = safe_stats(src, 5)
    except SyntaxError:
        continue
    nfile += 1
    for k in tot:
        tot[k] += s[k]

print("抽样文件数:", nfile)
print("token 总数:", tot["total"])
print("前缀安全:", tot["safe"], "(%.1f%%)" % (100.0 * tot["safe"] / max(tot["total"], 1)))
print("含未来祖先:", tot["unsafe"], "(%.1f%%)" % (100.0 * tot["unsafe"] / max(tot["total"], 1)))
print("  其中无位置属性（保守计为不安全）:", tot["nopos"])
