# -*- coding: utf-8 -*-
"""Repair the abstract: pair every italic English term with its Chinese gloss."""
import re, os

p = r"D:\ZZY\1LearningMore\AY4\project1.2\reliable_sde_derivations_cn.tex"
txt = open(p, encoding="utf-8").read()

NEW_ABSTRACT = r"""\begin{abstract}
\noindent
本文档按原 PDF 的章节顺序，逐步讲解其中的全部数学推导。从布朗增量的量级
\textit{Brownian increment scaling}（布朗增量缩放）与伊藤公式
\textit{It\^o's formula}（伊藤公式）出发，推出几何布朗运动
\textit{GBM, geometric Brownian motion}（几何布朗运动）的精确解、期望与方差；
再推导欧拉--丸山格式 \textit{Euler--Maruyama, EM}（欧拉--丸山格式）与
米尔斯坦格式 \textit{Milstein scheme}（米尔斯坦格式），给出强收敛
\textit{strong convergence}（强收敛）与弱收敛 \textit{weak convergence}（弱收敛）
的定义与估计量；随后分析 EM 的一步正性失败概率
\textit{one-step positivity failure probability}（一步正性失败概率）与 Milstein
二次乘子的最小值；然后给出非仿射随机波动率模型
\textit{non-affine stochastic volatility model}（非仿射随机波动率模型）的 EM 格式、
相关布朗增量 \textit{correlated Brownian increments}（相关布朗增量）的构造、
嵌套网格耦合 \textit{nested-grid coupling}（嵌套网格耦合）、置信区间
\textit{confidence interval}（置信区间），以及对数--对数回归斜率
\textit{log--log regression slope}（对数--对数回归斜率）的数学表达。

\medskip
\noindent\textbf{阅读约定}：关键术语后以括号给出英文原名；标有
\textbf{【为什么这样做】}的方框解释推导动机，标有
\textbf{【关键结论】}的方框给出必须记住的结果。
\end{abstract}"""

pat = re.compile(r"\\begin\{abstract\}.*?\\end\{abstract\}", re.S)
assert pat.search(txt), "abstract not found"
txt = pat.sub(lambda m: NEW_ABSTRACT, txt, count=1)
open(p, "w", encoding="utf-8", newline="\n").write(txt)

# ---------------- full re-verification ----------------
body = re.sub(r"(?<!\\)%.*", "", txt)
print("bytes:", os.path.getsize(p))

ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S).group(1)
print("\n--- abstract parens ---")
print("  （ :", ab.count("（"), "  ） :", ab.count("）"),
      "->", "OK" if ab.count("（") == ab.count("）") else "MISMATCH")
print("  \\en remaining:", len(re.findall(r"\\en\{", ab)))

print("\n--- global 全角括号 balance (whole document) ---")
print("  （ :", body.count("（"), "  ） :", body.count("）"))
print("  【 :", body.count("【"), "  】 :", body.count("】"))

print("\n--- env balance ---")
cb, ce = {}, {}
for e in re.findall(r"\\begin\{([^}]*)\}", body): cb[e] = cb.get(e, 0) + 1
for e in re.findall(r"\\end\{([^}]*)\}", body):   ce[e] = ce.get(e, 0) + 1
bad = [k for k in set(list(cb)+list(ce)) if cb.get(k,0) != ce.get(k,0)]
print("  mismatched:", bad if bad else "none")

print("\n--- \\en inside math text wrappers ---")
print("  count:", len(re.findall(r"\\(?:text|textrm|textnormal|mathrm|mbox)\{[^{}]*\\en\{", body)))

print("\n--- brace balance of whole file ---")
depth, ok = 0, True
for ch in body:
    if ch == "{": depth += 1
    elif ch == "}":
        depth -= 1
        if depth < 0: ok = False; break
print("  final depth:", depth, "| never negative:", ok)

print("\n--- single-$ parity ---")
print("  count:", len(re.findall(r"(?<!\$)\$(?!\$)", body)))

labels = set(re.findall(r"\\label\{([^}]*)\}", body))
refs = set(re.findall(r"\\(?:eqref|ref)\{([^}]*)\}", body))
print("\n  dangling refs:", sorted(refs - labels) if refs - labels else "none")
print("\nVERDICT:", "PASS" if not bad and depth == 0 and ok else "REVIEW")
