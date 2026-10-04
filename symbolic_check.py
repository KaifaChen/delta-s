# -*- coding: utf-8 -*-
"""
symbolic_check.py — §4.6 六步推导的通用符号验证（sympy）

在 2 参数 3 符号族 P = (θ1, θ2, 1−θ1−θ2) 上验证：
 1. 三阶 Bartlett 恒等式：S_ijk = T_ijk + B_ijk + B_jik + B_kij；
 2. 约束恒等式：B_kij = S_ijk − ∂_k g_ij（由 ∂_k E[∂i∂j l] = −∂_k g_ij）；
 3. 六步结论（工作稿恒等式 (5)）：S_ijk = ½(∂_i g_jk + ∂_j g_ik + ∂_k g_ij − T_ijk)。
（需要 sympy；运行环境 PYTHONPATH 含 E:\\LOGIC AI\\.pypkgs）

symbolic_check.py — general symbolic verification of the six-step derivation in §4.6 (sympy).
Verifies, on the 2-parameter 3-symbol family P = (θ1, θ2, 1−θ1−θ2): (1) the third-order Bartlett identity S_ijk = T_ijk + B_ijk + B_jik + B_kij; (2) the constraint identity B_kij = S_ijk − ∂_k g_ij (from ∂_k E[∂i∂j l] = −∂_k g_ij); (3) the six-step conclusion (working-draft identity (5)): S_ijk = ½(∂_i g_jk + ∂_j g_ik + ∂_k g_ij − T_ijk). (Requires sympy; the runtime PYTHONPATH includes E:\\LOGIC AI\\.pypkgs)
"""
import sys
import sympy as sp

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

t1, t2 = sp.symbols("t1 t2", positive=True)
P = [t1, t2, 1 - t1 - t2]
l = [sp.log(P[0]), sp.log(P[1]), sp.log(P[2])]
pars = [t1, t2]

def g(a, b):
    return sum(sp.diff(P[i], pars[a]) * sp.diff(P[i], pars[b]) / P[i] for i in range(3))

def T(a, b, c):
    return sum(P[i] * sp.diff(l[i], pars[a]) * sp.diff(l[i], pars[b]) * sp.diff(l[i], pars[c])
               for i in range(3))

def S(a, b, c):
    return -sum(P[i] * sp.diff(sp.diff(sp.diff(l[i], pars[a]), pars[b]), pars[c])
               for i in range(3))

def B(k, i, j):  # B_kij = E[∂i∂j l · ∂k l]，第一下标为单导数指标 / B_kij = E[∂i∂j l · ∂k l]; the first subscript is the single-derivative index
    return sum(P[ii] * sp.diff(sp.diff(l[ii], pars[i]), pars[j]) * sp.diff(l[ii], pars[k])
               for ii in range(3))

ok = True

def check(name, lhs, rhs):
    global ok
    d = sp.simplify(lhs - rhs)
    good = (d == 0)
    if not good:
        ok = False
    print(f"  {name}: {'OK' if good else 'FAIL'}   ({d})")

print("== 1. Bartlett 恒等式 S_ijk = T_ijk + B_ijk + B_jik + B_kij（8 个指标组合） ==")
for a in range(2):
    for b in range(2):
        for c in range(2):
            check(f"S({a}{b}{c})", S(a, b, c), T(a, b, c) + B(a, b, c) + B(b, a, c) + B(c, a, b))

print("== 2. 约束恒等式 B_kij = S_ijk − ∂_k g_ij（8 个指标组合） ==")
for k in range(2):
    for i in range(2):
        for j in range(2):
            check(f"B_kij k={k},i={i},j={j}", B(k, i, j), S(i, j, k) - sp.diff(g(i, j), pars[k]))

print("== 3. 六步结论 S_ijk = ½(∂_i g_jk + ∂_j g_ik + ∂_k g_ij − T_ijk)（8 个指标组合） ==")
for i in range(2):
    for j in range(2):
        for k in range(2):
            rhs = sp.Rational(1, 2) * (sp.diff(g(j, k), pars[i]) + sp.diff(g(i, k), pars[j])
                                      + sp.diff(g(i, j), pars[k]) - T(i, j, k))
            check(f"S({i}{j}{k})", S(i, j, k), rhs)

print("== 4. Bernoulli 特殊值核对（θ=0.7） ==")
th = sp.Rational(7, 10)
Tval = 1 / th ** 2 - 1 / (1 - th) ** 2
print(f"  T = {Tval}  数值 {float(Tval):.6f}  （应与 delta_expansion_check 的 −9.070295 一致）")

print()
print("全部通过" if ok else "存在 FAIL")
