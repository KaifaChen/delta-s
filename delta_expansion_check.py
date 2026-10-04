# -*- coding: utf-8 -*-
"""
delta_expansion_check.py — 数值验证 §4.7 差向量展开

验证：
 A. 恒等式 4.7.1：D_asym = Σ(P+Q)log(P/Q) 与两个单侧 KL 之差的精确吻合（随机分布对）；
 B. Bernoulli 参数例（θ=0.7, dθ=−0.02）：三阶 −(1/6)T dθ³ 恢复 + 四阶修正后余项为 O(δ⁵)；
 C. 收敛阶检查：δ = ε·δ0 固定方向收缩，误差 |精确 − 三阶| 应 ∝ ε⁴（每减半 ÷16）；
 D. ε-机混合例（近对称、入度 2）：P_b = p·P_A + (1−p)·P_B，δ 小，
    三阶近似与精确 D_asym 吻合，且 ΔS = D_KL(P_A∥P_b) > 0 表明方向性存在。
（纯标准库实现，无外部依赖。）

delta_expansion_check.py — numerical verification of the §4.7 difference-vector expansion.
Checks: (A) identity 4.7.1: D_asym = Σ(P+Q)log(P/Q) matches the difference of the two one-sided KL divergences exactly (random distribution pairs); (B) Bernoulli parameter example (θ=0.7, dθ=−0.02): the third-order term −(1/6)T dθ³ is recovered and the remainder after the fourth-order correction is O(δ⁵); (C) convergence-order check: with δ = ε·δ0 shrinking along a fixed direction, the error |exact − third order| should be ∝ ε⁴ (÷16 per halving); (D) ε-machine mixture example (nearly symmetric, in-degree 2): P_b = p·P_A + (1−p)·P_B with small δ; the third-order approximation matches the exact D_asym, and ΔS = D_KL(P_A∥P_b) > 0 shows that directionality exists. (Pure standard-library implementation, no external dependencies.)
"""
import math
import random

def kl(p, q):
    s = 0.0
    for a, b in zip(p, q):
        if a > 0:
            if b > 0:
                s += a * math.log(a / b)
            else:
                return math.inf
    return s

def d_asym_exact(p, q):
    s = 0.0
    for a, b in zip(p, q):
        if a > 0 and b > 0:
            s += (a + b) * math.log(a / b)
        elif a > 0:  # b == 0（此分支：b 为零）/ b == 0 (this branch: b is zero)
            return -math.inf
        elif b > 0:  # a == 0（此分支：a 为零）/ a == 0 (this branch: a is zero)
            return math.inf
    return s

def third_order(p, q):
    s = 0.0
    for a, b in zip(p, q):
        d = b - a
        s += d ** 3 / (a * a)
    return -s / 6.0

def fourth_order(p, q):
    s = 0.0
    for a, b in zip(p, q):
        d = b - a
        s += d ** 4 / (a ** 3)
    return s / 6.0

def main():
    print("== A. 恒等式检查（200 个随机三元分布对） ==")
    rng = random.Random(7)
    maxerr = 0.0
    for _ in range(200):
        p = [rng.random() + 0.05 for _ in range(3)]
        s = sum(p); p = [x / s for x in p]
        q = [rng.random() + 0.05 for _ in range(3)]
        s = sum(q); q = [x / s for x in q]
        exact = d_asym_exact(p, q)
        two_kl = kl(p, q) - kl(q, p)
        err = abs(exact - two_kl)
        maxerr = max(maxerr, err)
    print(f"  max |恒等式 − (KL差)| = {maxerr:.2e}  （应≈0）")

    print()
    print("== B. Bernoulli 参数例（theta=0.7, dtheta=-0.02） ==")
    th, dth = 0.7, -0.02
    P = [th, 1 - th]
    Q = [th + dth, 1 - th - dth]
    exact = d_asym_exact(P, Q)
    t3 = third_order(P, Q)
    t4 = fourth_order(P, Q)
    T = 1 / th ** 2 - 1 / (1 - th) ** 2
    print(f"  T_zzz = 1/theta^2 - 1/(1-theta)^2 = {T:.6f}")
    print(f"  精确 D_asym           = {exact:.6e}")
    print(f"  三阶 -(1/6)T dtheta^3 = {-(1/6) * T * dth ** 3:.6e}")
    print(f"  三阶公式(Σδ^3/P^2)    = {t3:.6e}   （两者应一致）")
    print(f"  三阶+四阶             = {t3 + t4:.6e}")
    print(f"  余项(精确−三阶)       = {exact - t3:.3e}")
    print(f"  余项(精确−三阶−四阶)  = {exact - t3 - t4:.3e}  （O(δ^5) 量级）")

    print()
    print("== C. 收敛阶（delta = eps*delta0，误差应 ∝ eps^4） ==")
    P0 = [0.6, 0.25, 0.15]
    D0 = [0.3, -0.2, -0.1]
    prev = None
    for eps in [0.05, 0.025, 0.0125, 0.00625]:
        Q = [a + eps * d for a, d in zip(P0, D0)]
        exact = d_asym_exact(P0, Q)
        err = abs(exact - third_order(P0, Q))
        ratio = (err / prev) if prev else 0.0
        print(f"  eps={eps:.5f}  误差={err:.3e}  相邻比={ratio:.4f}  （预期 1/16 = 0.0625）")
        prev = err

    print()
    print("== D. epsilon-机混合例（近对称，C 的入度为 2） ==")
    PA = [0.6, 0.4]
    PB = [0.55, 0.45]
    p = 0.9
    Pb = [p * a + (1 - p) * b for a, b in zip(PA, PB)]
    exact = d_asym_exact(PA, Pb)
    t3 = third_order(PA, Pb)
    ds = kl(PA, Pb)
    print(f"  P_b(·|C) = 0.9·P_A + 0.1·P_B = [{Pb[0]:.3f}, {Pb[1]:.3f}]")
    print(f"  delta = P_b − P_A = [{Pb[0]-PA[0]:.4f}, {Pb[1]-PA[1]:.4f}]")
    print(f"  ΔS(A→C) = D_KL(P_A ∥ P_b) = {ds:.6e}  （>0：方向性存在）")
    print(f"  D_asym 精确 = {exact:.3e}")
    print(f"  D_asym 三阶 = {t3:.3e}")
    print(f"  |精确 − 三阶| = {abs(exact - t3):.2e}  （O(δ^4) 量级）")

if __name__ == "__main__":
    main()
