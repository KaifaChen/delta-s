# -*- coding: utf-8 -*-
"""检查 d_asym_permutation.collect_tokens 的 token 顺序是否严格等于源码顺序。
Check whether collect_tokens emits tokens in strict source order (ast.iter_child_nodes is field order)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402

CASES = {
    "decorator": "@dec\ndef f(x):\n    return x\n",
    "default_arg": "def f(a=1, b=2):\n    return a\n",
    "kw_default": "def f(*, k=3):\n    return k\n",
}

for name, src in CASES.items():
    toks = dap.collect_tokens(src, 3)
    print("== %s ==" % name)
    print("   源码里符号出现顺序:", [w for w in src.replace("(", " ").replace(")", " ").replace(":", " ").replace("=", " ").split() if w not in ("@dec", "def", "return")][:8])
    print("   collect_tokens 输出:", [t for _, t in toks])
    print()
