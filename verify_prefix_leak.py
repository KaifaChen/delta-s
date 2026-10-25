# -*- coding: utf-8 -*-
"""复核审计文档 §1 的"最小反例"表：用 d_asym_permutation.collect_tokens 实测路径。
Verify the minimal counterexample table of the audit with the script's own collect_tokens."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d_asym_permutation as dap  # noqa: E402

SRC = '''def f():
    x = foo(a)
    return x
'''

for depth in (3, 5, 1):
    print("=== depth =", depth, "===")
    for path, sym in dap.collect_tokens(SRC, depth):
        print("   %-6s %s" % (sym, " → ".join(path) if path else "(empty)"))
    print()
