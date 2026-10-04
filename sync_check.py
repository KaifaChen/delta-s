# -*- coding: utf-8 -*-
"""
sync_check.py — 数值验证 §3.6 桥接（命题 2/3：环上的双向同步性）

验证三点：
 A. 漂移公式：真相位 φ0 对移位相位 ψ 的过去对数似然比，
    每周期期望 = (1/k) Σ_i D(P_i || P_{i+(ψ-φ0)}) > 0（P_i 两两不同时）。
 B. 分布两两不同（最小性） ⟹ 相位可由无限过去 / 无限未来渐近确定（后验 → 1）。
 C. 分布相同 ⟹ 漂移为 0、相位不可辨认（后验停在先验）——最小性为何要把它们合并。
 D. 不相交支撑（三状态反例式）⟹ 一个符号即锁定相位。

sync_check.py — numerical verification of the §3.6 bridge (Props. 2/3: two-way synchronization on a ring).
Checks: (A) drift formula: for the true phase φ0 versus the shifted phase ψ, the past log-likelihood ratio has per-cycle expectation = (1/k) Σ_i D(P_i || P_{i+(ψ-φ0)}) > 0 (when the P_i are pairwise distinct); (B) pairwise distinct distributions (minimality) ⟹ the phase is asymptotically determined by the infinite past / infinite future (posterior → 1); (C) identical distributions ⟹ zero drift and an unidentifiable phase (the posterior stays at the prior) — the reason minimality merges them; (D) disjoint supports (the three-state counterexample style) ⟹ a single symbol locks the phase.
"""
import math
import random

def kl(p, q):
    """KL 散度（支持 p 的坐标上求和；q 元素为 0 且 p 元素 > 0 时视为 +inf）
    KL divergence (summed over the coordinates in p's support; treated as +inf when p > 0 and q = 0)."""
    s = 0.0
    for a, b in zip(p, q):
        if a > 0:
            if b > 0:
                s += a * math.log(a / b)
            else:
                return math.inf
    return s

def drift_per_cycle(distrs, true, hyp):
    """E[LLR(φtrue vs φhyp)] / 周期（解析公式）
    E[LLR(φtrue vs φhyp)] per cycle (analytic formula)."""
    k = len(distrs)
    if hyp == true:
        return 0.0
    return sum(kl(distrs[i], distrs[(i + hyp - true) % k]) for i in range(k)) / k

def sample_symbol(distrs, phase, t, rng):
    """真相位 phase 下时刻 t 的符号（状态 = (phase + t) mod k）
    The symbol at time t under the true phase (state = (phase + t) mod k)."""
    d = distrs[(phase + t) % len(distrs)]
    u = rng.random()
    c = 0.0
    for i, pr in enumerate(d):
        c += pr
        if u < c:
            return i
    return len(d) - 1

def posterior(distrs, xs, t0, step):
    """由窗口符号序列（对应时刻 t0, t0+step, ...）计算各相位后验
    Computes the posterior over phases from the windowed symbol sequence (at times t0, t0+step, ...)."""
    k = len(distrs)
    loglik = []
    for ph in range(k):
        L = 0.0
        t = t0
        for x in xs:
            pr = distrs[(ph + t) % k][x]
            if pr > 0:
                L += math.log(pr)
            else:
                L = -math.inf
                break
            t += step
        loglik.append(L)
    m = max(loglik)
    w = [math.exp(L - m) if L != -math.inf else 0.0 for L in loglik]
    s = sum(w)
    return [v / s for v in w]

def run_case(name, distrs, true_phase, N, future, seed):
    rng = random.Random(seed)
    k = len(distrs)
    step = 1 if future else -1
    t0 = 1 if future else -1
    xs = [sample_symbol(distrs, true_phase, t0 + n * step, rng) for n in range(N)]
    post = posterior(distrs, xs, t0, step)
    print(f"[{name}] k={k} 真相位={true_phase} 方向={'未来' if future else '过去'} N={N}")
    print(f"  后验 = {[round(v, 4) for v in post]}")
    print(f"  真相位后验 = {post[true_phase]:.6f}")
    return post[true_phase]

def main():
    print("== A. 漂移公式（解析；分布两两不同、支撑重叠的情形） ==")
    P = [(0.7, 0.3), (0.3, 0.7), (0.5, 0.5)]
    k = len(P)
    for true in range(k):
        for hyp in range(k):
            if hyp != true:
                d = drift_per_cycle(P, true, hyp)
                print(f"  E[LLR(ph{true} vs ph{hyp})]/cycle = {d:.6f}  (expect >0 {'OK' if d > 0 else 'FAIL'})")
    print()

    print("== B. 分布两两不同 ⟹ 双向同步（后验应收敛到 1） ==")
    run_case("B-过去", P, 0, 20000, False, 42)
    run_case("B-未来", P, 0, 20000, True, 43)
    print()

    print("== C. 分布相同 ⟹ 漂移 0、相位不可辨认（后验应停在先验） ==")
    Q = [(0.5, 0.5), (0.5, 0.5)]
    print(f"  E[LLR(ph0 vs ph1)]/cycle = {drift_per_cycle(Q, 0, 1):.6f}  (expect =0)")
    run_case("C-过去", Q, 0, 20000, False, 44)
    print()

    print("== D. 不相交支撑（三状态反例式）⟹ 一步锁定 ==")
    R = [(1.0, 0.0), (0.0, 1.0)]
    run_case("D-过去", R, 0, 100, False, 45)

if __name__ == "__main__":
    main()
