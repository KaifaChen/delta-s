# -*- coding: utf-8 -*-
"""演示：逐 token 对数比均值估计的是 ΔS = D_KL(P_f∥P_b)，而不是 D_asym = D_KL(P_f∥P_b) − D_KL(P_b∥P_f)。"""
import math

def kl(p, q):
    return sum(pi * math.log(pi / qi) for pi, qi in zip(p, q))

def dasym(p, q):
    return kl(p, q) - kl(q, p)

def mean_logratio_under_pf(pf, pb):
    """E_{τ~P_f}[log P_f(τ) − log P_b(τ)]，即脚本统计量的总体值。"""
    return sum(p * math.log(p / q) for p, q in zip(pf, pb))

print("P_f            P_b            统计量(均值对数比)  ΔS=D_KL(f||b)  D_asym=KL差   定理3预言 −(1/6)Σδ³/P²")
for pf, pb in [((0.7, 0.3), (0.68, 0.32)),
               ((0.7, 0.3), (0.72, 0.28)),
               ((0.5, 0.5), (0.5, 0.5)),
               ((0.9, 0.1), (0.8, 0.2))]:
    delta = [b - a for a, b in zip(pf, pb)]
    third = -sum(d ** 3 / p ** 2 for d, p in zip(delta, pf)) / 6.0
    print("%-14s %-14s %+.6f          %+.6f      %+.6f     %+.6f" % (
        pf, pb, mean_logratio_under_pf(pf, pb), kl(pf, pb), dasym(pf, pb), third))

print()
print("结论：统计量 = D_KL(P_f∥P_b) = ΔS ≥ 0（恒非负），与 D_asym 的符号无关；")
print("      第二例中 ΔS>0 而 D_asym<0 —— 用该统计量的符号去验证定理 3 关于 D_asym 的符号预言是无效的。")
