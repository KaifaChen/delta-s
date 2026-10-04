# github_scripts — 论文复现脚本包 / Reproduction Script Package

## 项目简介 / Project Introduction

本目录是论文《逻辑序列的方向性：ε-机的扩展与 Amari–Chentsov 三阶张量》(v2.4) 的复现脚本包。
代码与作者原始脚本逐行等价（仅注释改为中英双语），UTF-8 编码，中文 print 输出原样保留。

This directory is the reproduction script package for the paper
*Directionality of Logic Sequences: An Extension of ε-Machines and the Third-Order Amari–Chentsov Tensor* (v2.4).
The code is line-for-line equivalent to the author's original scripts (only the comments have been made bilingual
Chinese/English), it is UTF-8 encoded, and the Chinese print output is kept unchanged.

## 文件清单 / File List

| 脚本 / Script | 功能 / Purpose | 依赖 / Dependencies |
| --- | --- | --- |
| `delta_expansion_check.py` | 数值验证 §4.7 差向量展开（恒等式 4.7.1、Bernoulli 例、收敛阶检查、ε-机混合例）/ Numerical check of the §4.7 difference-vector expansion (identity 4.7.1, the Bernoulli example, the convergence-order check, the ε-machine mixture example) | 仅标准库 / stdlib only |
| `sync_check.py` | 数值验证 §3.6 桥接（命题 2/3：环上的双向同步性）/ Numerical check of the §3.6 bridge (Props. 2/3: two-way synchronization on a ring) | 仅标准库 / stdlib only |
| `d_asym_permutation.py` | §5.4 置换检验实验（Python AST 结构路径口径；打乱符号 / 打乱路径两类零假设）/ §5.4 permutation-test experiment (Python-AST structural-path protocol; shuffle-symbols / shuffle-paths null hypotheses) | 仅标准库 / stdlib only |
| `c_asym_permutation.py` | §5.4 C 语料的同协议验证（tree-sitter C 口径）/ §5.4 same-protocol verification on a C corpus (tree-sitter C protocol) | tree-sitter 与 tree-sitter-c（`pip install tree-sitter tree-sitter-c`，两包版本需匹配，见脚本注释；在 WSL 或 Linux 下运行）/ tree-sitter plus tree-sitter-c (`pip install tree-sitter tree-sitter-c`; the two packages' versions must match, see the script comments; run under WSL or Linux) |
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

## 许可 / License

本仓库全部内容（代码与数据）采用 **CC BY-NC-ND 4.0**（署名—非商业性使用—禁止演绎 4.0 国际）许可。
商业使用需联系作者（见论文作者信息）。完整许可证文本见本仓库 `LICENSE` 文件，
或 https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode 。

All contents of this repository (code and data) are licensed under **CC BY-NC-ND 4.0**
(Attribution–NonCommercial–NoDerivatives 4.0 International). Commercial use requires contacting the author
(see the paper's author information). See the `LICENSE` file in this repository, or
https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode .
