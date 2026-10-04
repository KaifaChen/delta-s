# github_scripts — 论文复现脚本包 / Reproduction Script Package

## 项目简介 / Project Introduction

本目录是论文《逻辑序列的方向性：ε-机的扩展与 Amari–Chentsov 三阶张量》(v2.4) 的复现脚本包。
代码与作者原始脚本逐行等价（仅注释改为中英双语），UTF-8 编码，中文 print 输出原样保留。

This directory is the reproduction script package for the paper
*Directionality of Logic Sequences: An Extension of ε-Machines and the Third-Order Amari–Chentsov Tensor* (v2.4).
The code is line-for-line equivalent to the author's original scripts (only the comments have been made bilingual
Chinese/English), it is UTF-8 encoded, and the Chinese print output is kept unchanged.

## 重要：⟨ΔS⟩ 与 D_asym 是两个不同的量 / Important: ⟨ΔS⟩ and D_asym are different quantities

- 逐 token 统计量 log P_f(τ_i\|p_i) − log P_b(τ_i\|p_{i+1}) 是**对数比**；其经验均值 ⟨ΔS⟩ 在总体意义上等于
  **ΔS = D_KL(P_f∥P_b) ≥ 0**（平均局部不可逆度），因此恒非负。
- 定理 3 的对象是**不对称差** D_asym = D_KL(P_f∥P_b) − D_KL(P_b∥P_f)（两个 KL 之差，可正可负，最低非零阶为三阶）。
  **用 ⟨ΔS⟩ 的符号去检验定理 3 是无效的**——这正是 v2.5 修正的地方。
- **定理 3 的正确检验**（脚本现在会自动输出）：对"正反向符号边际分布"这一对分布直接计算**精确 KL 差**（不做展开），
  再与三阶预言 −(1/6)Σδ³/P_f² 和 S(δ) 比较。该检验只依赖符号边际，**与路径深度无关**。
- 已记录结果（见本仓库 `valid_*.json`）：

| 数据集 / Dataset | ⟨ΔS⟩ | S(δ) | D_asym(边际, 精确) | 三阶预言 | 逐文件符号一致 |
| --- | --- | --- | --- | --- | --- |
| 作者数据集（74 文件；深度 3/5/7） | +0.2031 / +0.1337 / +0.1273 | −30.919 | +2.3954e−09 | +2.3386e−09 | 74/74 |
| Python 标准库（55 文件） | +0.2115 | −23.917 | +1.5246e−10 | +1.5123e−10 | 55/55 |
| C 四仓库（168 文件） | +0.2584 | −1.0575 | ≈1e−16（见下） | ≈8e−17 | 163/168（三阶预言 166/168） |

**数值精度说明**：D_asym 是三阶量，δ 越小越接近双精度下限。脚本用恒等式
D_asym = Σ_τ (P_f + P_b) log(P_f/P_b) 配合 `log1p` 计算（避免"两个 KL 相减"的大项相消）。
C 语料的池化 δ 极小，池化值 ≈1e−16 已落在双精度地板，**只有逐文件符号计数可解读**；
其 5 个不一致文件中，4 个是 68–102 token 且 S(δ) ≈ 0 的短头文件，1 个（tif_fax3sm.c）是机器生成的数值表、
差值为 ~1e−17，符号不可分辨。Python 两语料的池化值（1e−9、1e−10）远高于地板，可正常解读。

**Numerical precision note**: D_asym is a third-order quantity, so the smaller δ is, the closer it sits to the
double-precision floor. The scripts evaluate the identity D_asym = Σ_τ (P_f + P_b) log(P_f/P_b) with `log1p`
(avoiding cancellation between two KLs). For the C corpus the pooled δ is so small that the pooled value ≈1e−16
lies at the floor and **only the per-file sign counts are interpretable**; of its 5 mismatching files, 4 are
68–102-token headers with S(δ) ≈ 0 and 1 (tif_fax3sm.c) is a machine-generated numeric table whose difference
(~1e−17) has no resolvable sign. The Python pooled values (1e−9, 1e−10) are far above the floor.

平滑敏感性检查（add-0.25 / 0.5 / 1 / 2）：作者 74/74、标准库 55/55 全部稳定（见 `check_smoothing_sensitivity.py`，位于论文目录）。

The per-token statistic log P_f − log P_b is a **log-ratio**; its empirical mean ⟨ΔS⟩ equals, in expectation,
**ΔS = D_KL(P_f∥P_b) ≥ 0** (the average local irreversibility) and is therefore never negative. Theorem 3 concerns
the **asymmetric difference** D_asym = D_KL(P_f∥P_b) − D_KL(P_b∥P_f) (a difference of two KLs, signed, third order at
leading order): testing Theorem 3 with the sign of ⟨ΔS⟩ is invalid. The scripts now also compute the **correct test** —
the exact KL difference between the forward/backward symbol marginals (no expansion) versus the third-order
prediction −(1/6)Σδ³/P_f² — which depends only on the symbol marginals and is therefore depth-independent.

**关于作者语料的快照性 / On the author-corpus snapshot**：作者数据集是采集时的快照，其文件清单即
`files_author_d5.txt`（由 `perm_depth5.json` 提取）。该目录含作者在用的脚本，脚本一经编辑，同一清单重跑的
token 数会有千分之几的漂移；`perm_*.json` 与论文 §5.5 的数字对应采集时的状态，`valid_*.json` 为脚本更新后
在**同一清单**上重跑的结果（两者差异仅来自被编辑过的少数文件，结论不变）。

The author corpus is a snapshot; its file list is `files_author_d5.txt` (extracted from `perm_depth5.json`). The
directory contains scripts the author is still editing, so re-running the same list later shifts the token count by
a few tenths of a percent. The `perm_*.json` files and the paper's §5.5 numbers correspond to the collection-time
state, while `valid_*.json` records a re-run of the **same list** after the scripts were updated (the difference
comes only from the few edited files and does not change any conclusion).

## 文件清单 / File List

| 脚本 / Script | 功能 / Purpose | 依赖 / Dependencies |
| --- | --- | --- |
| `delta_expansion_check.py` | 数值验证 §4.7 差向量展开（恒等式 4.7.1、Bernoulli 例、收敛阶检查、ε-机混合例）/ Numerical check of the §4.7 difference-vector expansion (identity 4.7.1, the Bernoulli example, the convergence-order check, the ε-machine mixture example) | 仅标准库 / stdlib only |
| `sync_check.py` | 数值验证 §3.6 桥接（命题 2/3：环上的双向同步性）/ Numerical check of the §3.6 bridge (Props. 2/3: two-way synchronization on a ring) | 仅标准库 / stdlib only |
| `d_asym_permutation.py` | §5.4 置换检验实验（Python AST 结构路径协议；打乱符号 / 打乱路径两类零假设）；同时输出 **⟨ΔS⟩**（平均局部不可逆度）与 **定理 3 的检验**（边际对的精确 KL 差 D_asym 及其三阶预言）/ §5.4 permutation-test experiment (Python-AST protocol; shuffle-symbols / shuffle-paths nulls); also reports **⟨ΔS⟩** and the **test of Theorem 3** (exact KL difference between the two marginals plus its third-order prediction) | 仅标准库 / stdlib only |
| `c_asym_permutation.py` | §5.4 C 语料的同协议验证（tree-sitter C 解析），输出同上 / §5.4 same-protocol verification on a C corpus (tree-sitter C parsing), same outputs | tree-sitter 与 tree-sitter-c（`pip install tree-sitter tree-sitter-c`，两包版本需匹配，见脚本注释；在 WSL 或 Linux 下运行）/ tree-sitter plus tree-sitter-c (`pip install tree-sitter tree-sitter-c`; the two packages' versions must match, see the script comments; run under WSL or Linux) |
| `symbolic_check.py` | §4.6 六步推导的通用符号验证 / General symbolic verification of the six-step derivation in §4.6 | sympy（`pip install sympy`）/ sympy (`pip install sympy`) |
| `figs.py` | 生成论文 6 张示意图（SVG；本仓库版图内文字为英文）/ Generates the paper's 6 schematic figures (SVG; the figure text in this repository version is English) | 仅标准库 / stdlib only |
| `validate_svg.py` | 逐个检查 fig*.svg 是否为 well-formed XML / Checks each fig*.svg for well-formed XML | 仅标准库 / stdlib only |

## 用法示例 / Usage Examples

```bash
# 安装外部依赖（仅两个脚本需要）/ install external dependencies (only two scripts need them)
pip install sympy                        # symbolic_check.py
pip install tree-sitter tree-sitter-c    # c_asym_permutation.py（WSL/Linux / under WSL or Linux）

# 数值验证（仅标准库） / numerical checks (stdlib only)
python delta_expansion_check.py
python sync_check.py

# §4.6 符号验证（需 sympy） / §4.6 symbolic check (requires sympy)
python symbolic_check.py

# §5.4 置换检验（Python 语料） / §5.4 permutation test (Python corpus)
python d_asym_permutation.py --roots <dir...> --depth 5 --nperm 1000 --out perm_depth5.json

# 精确复现既有结果（用记录的文件清单，无需重扫目录）/ exact reproduction from a recorded file list
python d_asym_permutation.py --filelist files_author_d5.txt --depth 5 --nperm 0 --out valid_depth5.json

# §5.4 置换检验（C 语料；WSL/Linux + tree-sitter） / §5.4 permutation test (C corpus; WSL/Linux + tree-sitter)
python c_asym_permutation.py --roots <musl> <libuv> <libtiff> <zlib> --depth 5 --nperm 1000 --out perm_c.json

# 生成 6 张 SVG 示意图 / generate the 6 SVG figures
python figs.py

# 校验生成的 SVG / validate the generated SVGs
python validate_svg.py
```

`figs.py` 会读取同目录的 `perm_depth5.json`、`perm_stdlib.json`、`perm_c.json`，生成 6 张 SVG
（fig1_sample_space.svg、fig2_phase_ambiguity.svg、fig3_three_state.svg、fig4_third_order.svg、
fig5_perm_histogram.svg、fig6_sign_scatter.svg）。相对作者原始脚本，本仓库版有三类**已披露的移植性改动**，
其余逐行等价：（1）`figs.py` 的 `OUT` 常量改为脚本所在目录；（2）`validate_svg.py` 校验脚本所在目录的
fig*.svg（原版指向作者本地路径）；（3）全部脚本在启动时把标准输出切到 UTF-8（原版依赖终端环境）。

`figs.py` reads `perm_depth5.json`, `perm_stdlib.json` and `perm_c.json` from the same directory and generates
the 6 SVGs (fig1_sample_space.svg, fig2_phase_ambiguity.svg, fig3_three_state.svg, fig4_third_order.svg,
fig5_perm_histogram.svg, fig6_sign_scatter.svg). Relative to the author's original scripts, this repository
version contains three **disclosed portability changes** and is otherwise line-for-line equivalent:
(1) `figs.py`'s `OUT` constant points at the script's own directory; (2) `validate_svg.py` validates the
fig*.svg files in the script's own directory (the original pointed at the author's local path); (3) every script
switches stdout to UTF-8 at startup (the originals relied on the terminal environment).

## 数据依赖说明 / Data Dependencies

`figs.py`（以及结果复现）依赖以下 JSON 文件，**均已随本仓库发布**（与本 README 同目录）：

`figs.py` (and the reproduction of the results) depends on the following JSON files, **all shipped with this repository**
(in the same directory as this README):

| 文件 / File | 内容 / Contents | 生成方式 / How it is generated |
| --- | --- | --- |
| `perm_depth3.json` | 作者 Python 语料、深度 3 的置换检验结果 / permutation-test results on the author's Python corpus at depth 3 | `python d_asym_permutation.py --roots <作者语料> --depth 3 --out perm_depth3.json` / `python d_asym_permutation.py --roots <author corpus> --depth 3 --out perm_depth3.json` |
| `perm_depth5.json` | 作者 Python 语料、深度 5 的置换检验结果 / permutation-test results on the author's Python corpus at depth 5 | `python d_asym_permutation.py --roots <作者语料> --depth 5 --out perm_depth5.json` / `python d_asym_permutation.py --roots <author corpus> --depth 5 --out perm_depth5.json` |
| `perm_depth7.json` | 作者 Python 语料、深度 7 的置换检验结果 / permutation-test results on the author's Python corpus at depth 7 | `python d_asym_permutation.py --roots <作者语料> --depth 7 --out perm_depth7.json` / `python d_asym_permutation.py --roots <author corpus> --depth 7 --out perm_depth7.json` |
| `perm_stdlib.json` | Python 标准库语料的置换检验结果 / permutation-test results on the Python standard-library corpus | `python d_asym_permutation.py --roots <Python 标准库目录> --out perm_stdlib.json` / `python d_asym_permutation.py --roots <Python stdlib directory> --out perm_stdlib.json` |
| `perm_c.json` | C 四仓库（musl、libuv、libtiff、zlib）的置换检验结果 / permutation-test results on the four C repositories (musl, libuv, libtiff, zlib) | `python c_asym_permutation.py --roots <musl> <libuv> <libtiff> <zlib> --depth 5 --nperm 1000 --out perm_c.json`（在 WSL 或 Linux 下运行 / run under WSL or Linux） |
| `files_author_d5.txt`、`files_stdlib.txt` | 记录的文件清单（每行一个路径），用于精确复现 / recorded file lists (one path per line) for exact reproduction | 由 `perm_depth5.json`、`perm_stdlib.json` 的 `per_file[].file` 提取 / extracted from `per_file[].file` |
| `valid_depth3/5/7.json`、`valid_stdlib.json`、`valid_c.json` | **定理 3 的检验**结果：⟨ΔS⟩、S(δ)、边际对的精确 KL 差 D_asym、三阶预言、逐文件符号一致数 / **the test of Theorem 3**: ⟨ΔS⟩, S(δ), the exact marginal-pair D_asym, its third-order prediction, and the per-file sign-agreement counts | `python d_asym_permutation.py --filelist files_author_d5.txt --depth 5 --nperm 0 --out valid_depth5.json`（其余同理；C 语料用 `c_asym_permutation.py --roots ... --maxfiles 60 --nperm 0 --out valid_c.json`）/ likewise for the others; for the C corpus use `c_asym_permutation.py --roots ... --maxfiles 60 --nperm 0 --out valid_c.json` |

## 许可 / License

本仓库全部内容（代码与数据）采用 **CC BY-NC-ND 4.0**（署名—非商业性使用—禁止演绎 4.0 国际）许可。
商业使用需联系作者（见论文作者信息）。完整许可证文本见本仓库 `LICENSE` 文件，
或 https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode 。

All contents of this repository (code and data) are licensed under **CC BY-NC-ND 4.0**
(Attribution–NonCommercial–NoDerivatives 4.0 International). Commercial use requires contacting the author
(see the paper's author information). See the `LICENSE` file in this repository, or
https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode .
