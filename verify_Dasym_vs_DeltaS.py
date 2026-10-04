# -*- coding: utf-8 -*-
"""演示：逐 token 对数比均值估计的是 ΔS = D_KL(P_f∥P_b)，而不是 D_asym = D_KL(P_f∥P_b) − D_KL(P_b∥P_f)。

Demonstration: the mean per-token log-ratio estimates ΔS = D_KL(P_f∥P_b), not the asymmetric
difference D_asym = D_KL(P_f∥P_b) − D_KL(P_b∥P_f).

对若干分布对打印四个量 / For several distribution pairs the script prints four quantities:
  统计量 = 均值对数比 = 总体意义上的 ΔS（恒非负）/ statistic = mean log-ratio = ΔS in expectation (never negative);
  ΔS = D_KL(P_f∥P_b)；D_asym = 两个单侧 KL 之差（可正可负）；定理 3 的三阶预言 −(1/6)Σδ³/P_f²。
结论：统计量与 D_asym 不是同一个量，用前者的符号去检验定理 3 的符号预言是无效的。
Conclusion: the statistic and D_asym are different quantities; testing the sign prediction of
Theorem 3 with the sign of the former is invalid.

用法 / Usage: python verify_Dasym_vs_DeltaS.py
"""
import math


def kl(p, q):
    """D_KL(P∥Q)。/ D_KL(P∥Q)."""
    return sum(pi * math.log(pi / qi) for pi, qi in zip(p, q))


def dasym(p, q):
    """D_asym = D_KL(P∥Q) − D_KL(Q∥P)。/ D_asym = D_KL(P∥Q) − D_KL(Q∥P)."""
    return kl(p, q) - kl(q, p)


def mean_logratio_under_pf(pf, pb):
    """E_{τ~P_f}[log P_f(τ) − log P_b(τ)]，即脚本统计量的总体值。/ Population value of the script's statistic."""
    return sum(p * math.log(p / q) for p, q in zip(pf, pb))


print("P_f            P_b            统计量(均值对数比)  ΔS=D_KL(f||b)  D_asym=KL差   定理3预言 −(1/6)Σδ³/P²")
print("P_f            P_b            statistic (mean log-ratio)  DeltaS=D_KL(f||b)  D_asym  Thm-3 prediction")
for pf, pb in [((0.7, 0.3), (0.68, 0.32)),
               ((0.7, 0.3), (0.72, 0.28)),
               ((0.5, 0.5), (0.5, 0.5)),
               ((0.9, 0.1), (0.8, 0.2))]:
    delta = [b - a for a, b in zip(pf, pb)]          # δ = P_b − P_f / δ = P_b − P_f
    third = -sum(d ** 3 / p ** 2 for d, p in zip(delta, pf)) / 6.0   # 定理 3 三阶项 / third-order term
    print("%-14s %-14s %+.6f          %+.6f      %+.6f     %+.6f" % (
        pf, pb, mean_logratio_under_pf(pf, pb), kl(pf, pb), dasym(pf, pb), third))

print()
print("结论：统计量 = D_KL(P_f∥P_b) = ΔS ≥ 0（恒非负），与 D_asym 的符号无关；")
print("      第二例中 ΔS>0 而 D_asym<0 —— 用该统计量的符号去验证定理 3 关于 D_asym 的符号预言是无效的。")
print("Conclusion: the statistic equals D_KL(P_f∥P_b) = ΔS ≥ 0 and is independent of the sign of D_asym;")
print("            in the second example DeltaS > 0 while D_asym < 0, so testing the sign prediction of")
print("            Theorem 3 with the sign of this statistic is invalid.")
