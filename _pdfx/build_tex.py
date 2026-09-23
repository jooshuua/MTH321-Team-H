# -*- coding: utf-8 -*-
"""Build the Chinese derivation document (UTF-8, no BOM) and self-verify it."""
import os, re, sys

BASE = r"D:\ZZY\1LearningMore\AY4\project1.2"
OUT = os.path.join(BASE, "reliable_sde_derivations_cn.tex")

DOC = r"""% ============================================================
%  Reliable Numerical Simulation of Financial SDEs
%  数学推导全过程详解（中文讲义版）
%  来源：Reliable_Numerical_Simulation_of_Financial_SDEs.pdf
%
%  编译方式（任选其一，Overleaf 均可直接编译）：
%    (A) XeLaTeX  —— 推荐，中文最稳
%    (B) pdfLaTeX —— 亦可（ctexart 会自动切换到 CJK 方案）
%  若 Overleaf 报错，把 Menu -> Compiler 设为 XeLaTeX 即可。
% ============================================================
\documentclass[UTF8,a4paper,11pt]{ctexart}

% ---------- 数学与排版宏包 ----------
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=2.4cm]{geometry}
\usepackage{bm}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage[dvipsnames]{xcolor}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=NavyBlue,citecolor=NavyBlue,urlcolor=NavyBlue}

% ---------- 定理类环境 ----------
\newtheorem{theorem}{定理}[section]
\newtheorem{proposition}[theorem]{命题}
\newtheorem{lemma}[theorem]{引理}
\newtheorem{corollary}[theorem]{推论}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{定义}
\newtheorem{example}[theorem]{例}
\theoremstyle{remark}
\newtheorem{remark}[theorem]{注}

% ---------- 自定义排版命令（不依赖额外宏包，保证可编译）----------
% \why{...}  : 「为什么这样做」讲解块
% \key{...}  : 关键结论块
% \en{...}   : 英文术语标注
\newcommand{\why}[1]{%
  \par\medskip\noindent
  \colorbox{Orange!12}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
  \textbf{【为什么这样做】}\ #1}}\par\medskip}
\newcommand{\key}[1]{%
  \par\medskip\noindent
  \colorbox{NavyBlue!8}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
  \textbf{【关键结论】}\ #1}}\par\medskip}
\newcommand{\en}[1]{\textnormal{（\textit{#1}）}}

% ---------- 常用数学宏 ----------
\newcommand{\dd}{\mathrm{d}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Var}{\operatorname{Var}}
\newcommand{\Cov}{\operatorname{Cov}}
\newcommand{\Corr}{\operatorname{Corr}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\F}{\mathcal{F}}
\newcommand{\dW}{\Delta W}
\newcommand{\Sref}{\mathrm{ref}}
\newcommand{\EM}{\mathrm{EM}}
\newcommand{\Mil}{\mathrm{Mil}}
\newcommand{\exact}{\mathrm{exact}}
\newcommand{\Nref}{N_{\mathrm{ref}}}

\title{\textbf{Reliable Numerical Simulation of Financial SDEs}\\[2mm]
       \large 数学推导全过程详解（中文讲义版）}
\author{基于同名 PDF 报告整理}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
\noindent
本文档按原 PDF 的章节顺序，逐步讲解其中的全部数学推导。从布朗增量的量级
\en{Brownian increment scaling}与伊藤公式\en{It\^o's formula}出发，推出几何布朗运动
\en{GBM, geometric Brownian motion}的精确解、期望与方差；再推导欧拉--丸山格式
\en{Euler--Maruyama, EM}与米尔斯坦格式\en{Milstein scheme}，给出强收敛
\en{strong convergence}与弱收敛\en{weak convergence}的定义与估计量；随后分析
EM 的一步正性失败概率\en{one-step positivity failure probability}与 Milstein
二次乘子的最小值；然后给出非仿射随机波动率模型\en{non-affine stochastic volatility model}
的 EM 格式、相关布朗增量\en{correlated Brownian increments}的构造、嵌套网格耦合
\en{nested-grid coupling}、置信区间\en{confidence interval}，以及
对数--对数回归斜率\en{log--log regression slope}的数学表达。

\medskip
\noindent\textbf{阅读约定}：关键术语后以括号给出英文；标有
\textbf{【为什么这样做】}的方框解释推导动机，标有
\textbf{【关键结论】}的方框给出必须记住的结果。
\end{abstract}

\tableofcontents
\newpage

% ============================================================
\section{地基：布朗运动、SDE 与伊藤公式}
\label{sec:foundation}
% ============================================================

\subsection{为什么需要随机微积分}

普通微积分处理 $\dd x=f'(t)\dd t$ 这类式子，路径是光滑的。股价路径不是光滑的：
它处处连续但处处不可微，因此 $\dd S_t/\dd t$ 不存在。我们只能写
\begin{equation}
\dd S_t=\underbrace{\mu S_t\,\dd t}_{\text{确定趋势}}
+\underbrace{\sigma S_t\,\dd W_t}_{\text{随机扰动}},
\end{equation}
其中 $\dd W_t$ 是布朗运动的增量\en{Brownian increment}。首要问题是：$\dd W_t$ 的
量级\en{order of magnitude}是多大？

\subsection{布朗增量的量级：整套理论的起点}

\why{后面所有推导（伊藤公式、迭代随机积分、鞅性质、耦合降方差）都依赖下面这个量级分析。
它是整个随机微积分与数值方法的基石。}

设 $W$ 为标准布朗运动\en{standard Brownian motion}，则
$\dW=W_{t+h}-W_t\sim N(0,h)$，于是
\begin{equation}
\E\bigl[(\dW)^2\bigr]=h,\qquad
\Var\bigl((\dW)^2\bigr)=2h^2 .
\label{eq:incr-scale}
\end{equation}
第一式的意思是 $(\dW)^2$ 的平均值恰好是 $h$；第二式说明它围绕 $h$ 的涨落是
$O(h)$ 阶，因此
\begin{equation}
\E\Bigl[\bigl((\dW)^2-h\bigr)^{2}\Bigr]=2h^{2}\longrightarrow 0 .
\label{eq:incr-ms}
\end{equation}
这就是非形式地写 $(\dd W_t)^2=\dd t$ 的严格来源：它不是约定，而是被
「平方的均值收敛到 $h$、方差是 $h^2$ 阶」这件事逼出来的。由此得到伊藤乘法表
\en{It\^o multiplication table}
\begin{equation}
(\dd W_t)^2=\dd t,\qquad \dd t\cdot\dd W_t=0,\qquad (\dd t)^2=0 .
\label{eq:ito-table}
\end{equation}

\why{为什么 $\dd t\,\dd W_t=0$？因为
$|\Delta t\,\dW|\le h\cdot O(\sqrt h)=O(h^{3/2})$，求和后为 $O(\sqrt h)\to0$，
比 $O(h)$ 更高阶，故可丢弃。}

\key{$(dW)^2=dt$ 是全部的来源。只要记住这一条，伊藤公式中多出的
$\tfrac12f''$ 就不神秘了。}

\subsection{SDE 的严格含义：积分方程}

$\dd S_t=\mu S_t\dd t+\sigma S_t\dd W_t$ 本身没有独立含义，它只是积分方程
\en{integral equation}的缩写：
\begin{equation}
S_t=S_0+\int_0^t\mu S_u\,\dd u+\int_0^t\sigma S_u\,\dd W_u .
\label{eq:sde-integral}
\end{equation}
右端第二项是\textbf{伊藤积分}\en{It\^o integral}，定义为非预期（左端点）黎曼和的
均方极限\en{mean-square limit}：
\begin{equation}
\int_0^T H_u\,\dd W_u
=\lim_{\|\Pi\|\to0}\sum_k H_{t_k}\bigl(W_{t_{k+1}}-W_{t_k}\bigr).
\label{eq:ito-def}
\end{equation}

\why{必须取左端点 $H_{t_k}$，即被积函数与增量不重叠（非预期性
\en{non-anticipativity}）。若改用中点，得到的是斯特拉托诺维奇积分
\en{Stratonovich integral}，链式法则回到普通微积分形式，但会\emph{失去鞅性质}。}

伊藤积分满足两条基本性质：
\begin{equation}
\E\Bigl[\int_0^T H_u\,\dd W_u\Bigr]=0,\qquad
\E\Bigl[\Bigl(\int_0^T H_u\,\dd W_u\Bigr)^{2}\Bigr]
=\E\int_0^T H_u^{2}\,\dd u\quad\text{（伊藤等距 \en{It\^o isometry}）}.
\label{eq:ito-isometry}
\end{equation}
这两条是后面计算 $\E[S_T]$、$\E[S_T^2]$，以及解释「耦合为何能降低方差」的全部基础。

\subsection{伊藤公式：多出来的 $\tfrac12f''$}

\why{这是全文最核心的一步。普通泰勒展开中 $(\Delta x)^2=O(h^2)$ 是高阶小量；
但在随机世界里 $\Delta x$ 含 $O(\sqrt h)$ 的布朗部分，于是 $(\Delta x)^2$ 中含
$O(h)$ 项，与一阶项\emph{同阶}，不能丢弃。}

设 $\dd X_t=a\,\dd t+b\,\dd W_t$。把 $(\dd X_t)^2$ 展开并用乘法表
式~\eqref{eq:ito-table}：
\begin{equation}
(\dd X_t)^2=\bigl(a\,\dd t+b\,\dd W_t\bigr)^2
=\underbrace{b^2\,\dd t}_{\text{保留}}
+\underbrace{2ab\,\dd t\,\dd W_t}_{=0}
+\underbrace{a^2(\dd t)^2}_{=0}=b^{2}\,\dd t .
\label{eq:dx-squared}
\end{equation}
而 $(\dd X)^3$ 含 $(\dd W)^3$，量级为 $h^{3/2}$，求和后 $O(\sqrt h)\to0$，可丢。
于是得到伊藤公式\en{It\^o's formula}：
\begin{equation}
\dd f(t,X_t)=\Bigl(f_t+a f_x+\tfrac12 b^{2}f_{xx}\Bigr)\dd t+b f_x\,\dd W_t .
\label{eq:ito-lemma}
\end{equation}

\subsection{附带结论：$\int_0^t W_s\,\dd W_s=\tfrac12W_t^2-\tfrac12t$}

\why{\S\ref{sec:discretisation} 推导 Milstein 时要用迭代随机积分
\en{iterated stochastic integral}，其最简版本就是这一条。先在这里把它算清楚。}

取 $f(x)=\tfrac12x^2$（故 $f'=x$，$f''=1$）代入式~\eqref{eq:ito-lemma}：
\begin{equation}
\dd\Bigl(\tfrac12W_t^{2}\Bigr)=W_t\,\dd W_t+\tfrac12\,\dd t
\quad\Longrightarrow\quad
\int_0^t W_s\,\dd W_s=\tfrac12W_t^{2}-\tfrac12t .
\label{eq:intWdW}
\end{equation}
与普通微积分 $\int x\,\dd x=\tfrac12x^2$ 相比多出的 $-\tfrac12t$，
\textbf{完全来自 $\tfrac12f''$ 项}。写成增量形式即
\begin{equation}
\int_{t_n}^{t_{n+1}}\!\!\int_{t_n}^{s}\dd W_r\,\dd W_s
=\tfrac12\Bigl[(\dW_n)^{2}-h\Bigr].
\label{eq:iterated-intro}
\end{equation}

% ============================================================
\section{GBM 全套：定义、伊藤公式、精确解与矩}
\label{sec:gbm}
% ============================================================

\subsection{SDE 定义（式(1)）}

在物理测度\en{physical measure}下，几何布朗运动\en{GBM}为
\begin{equation}
\dd S_t=\mu S_t\,\dd t+\sigma S_t\,\dd W_t,\qquad S_0>0 ,
\label{eq:gbm}
\end{equation}
其中 $\mu$ 为漂移率\en{drift rate}，$\sigma>0$ 为波动率\en{volatility}。

\why{「几何」的含义是：系数 $\mu S_t$、$\sigma S_t$ 与当前价格成正比，于是价格按
「比例」（收益率 \en{return}）演化。这正对应金融经验事实——收益率与价格水平无关。
代价是真解恒为正（$S_t>0$），这为后面的正性分析埋下伏笔。}

\subsection{伊藤公式推 $\dd\log S_t$（式(2)）}

\why{$\dd S_t$ 中 $S_t$ 以乘性出现，方程不好处理；取对数把它变成加性方程，
漂移与扩散都成为常数，立即可积。这是解 GBM 的标准思路。}

取 $f(s)=\log s$，则
\begin{equation}
f'(s)=\frac{1}{s},\qquad f''(s)=-\frac{1}{s^{2}} .
\end{equation}
代入式~\eqref{eq:ito-lemma}（此处 $a=\mu S_t$，$b=\sigma S_t$），先算两项：
\begin{align}
f'(S_t)\,\dd S_t
&=\frac{1}{S_t}\bigl(\mu S_t\,\dd t+\sigma S_t\,\dd W_t\bigr)
=\mu\,\dd t+\sigma\,\dd W_t ,
\label{eq:log-term1}\\
\tfrac12f''(S_t)(\dd S_t)^2
&=-\frac{1}{2S_t^{2}}\cdot\sigma^{2}S_t^{2}\,\dd t
=-\tfrac12\sigma^{2}\,\dd t .
\label{eq:log-term2}
\end{align}
式~\eqref{eq:log-term2} 中用了式~\eqref{eq:dx-squared} 的
$(\dd S_t)^2=\sigma^2S_t^2\dd t$。两式相加得到
\begin{equation}
\dd\log S_t=\Bigl(\mu-\tfrac12\sigma^{2}\Bigr)\dd t+\sigma\,\dd W_t .
\label{eq:log-gbm}
\end{equation}

\key{真实的对数收益率不是 $\mu\,\dd t$，而是 $(\mu-\tfrac12\sigma^2)\dd t$。
多出的 $-\tfrac12\sigma^2$ 称为\textbf{波动拖累}\en{volatility drag}，
与式~\eqref{eq:intWdW} 中的 $-\tfrac12t$ 同源。它说明 $\sigma$ 越大，
几何平均增长越慢，即使算术平均 $\mu$ 不变。}

\subsection{精确解（式(3)）}

\why{式~\eqref{eq:log-gbm} 右端系数全为常数，因此对时间的积分就是普通黎曼积分，
不需要再处理伊藤项。这就是「取对数」的好处。}

从 $0$ 积到 $t$：
\begin{equation}
\log S_t-\log S_0=\Bigl(\mu-\tfrac12\sigma^{2}\Bigr)t+\sigma W_t .
\end{equation}
两边取指数（$e^{x}$ 是确定性光滑函数，不再产生新的伊藤项）：
\begin{equation}
S_t=S_0\exp\Bigl[\Bigl(\mu-\tfrac12\sigma^{2}\Bigr)t+\sigma W_t\Bigr].
\label{eq:gbm-exact}
\end{equation}
因为 $W_t\sim N(0,t)$，所以
\begin{equation}
\log S_t\sim N\Bigl(\log S_0+\bigl(\mu-\tfrac12\sigma^{2}\bigr)t,\ \sigma^{2}t\Bigr),
\label{eq:log-normal}
\end{equation}
即 $S_t$ 服从\textbf{对数正态分布}\en{lognormal distribution}。

\subsection{期望与方差（式(4)）}

\why{这是全文唯一的闭式基准（oracle）。有了它，数值格式的\emph{弱}误差
（均值偏差）可以精确算出，无需用参考解近似。}

回忆对数正态矩公式\en{lognormal moment formula}：若 $X\sim N(m,s^2)$，则
$\E[e^{X}]=e^{m+\frac12s^2}$。于是
\begin{equation}
\E[S_T]=S_0\,e^{(\mu-\frac12\sigma^2)T}\cdot e^{\frac12\sigma^{2}T}
=S_0e^{\mu T}.
\label{eq:gbm-mean}
\end{equation}
\textbf{注意 $\tfrac12\sigma^2$ 恰好抵消}——这不是巧合，它说明 $\mu$ 就是期望收益率。

同理 $S_T^2=S_0^2e^{(2\mu-\sigma^2)T}e^{2\sigma W_T}$，再用一次矩公式
（$m=(2\mu-\sigma^2)T$，$s=2\sigma\sqrt T$）：
\begin{equation}
\E[S_T^{2}]=S_0^{2}e^{(2\mu-\sigma^2)T}\cdot e^{\frac12(2\sigma)^2T}
=S_0^{2}e^{2\mu T}e^{\sigma^{2}T},
\end{equation}
故
\begin{equation}
\Var(S_T)=\E[S_T^{2}]-\bigl(\E[S_T]\bigr)^{2}
=S_0^{2}e^{2\mu T}\Bigl(e^{\sigma^{2}T}-1\Bigr).
\label{eq:gbm-moments}
\end{equation}

\subsection{基准参数与数值（式(5)(31)）}

\begin{equation}
S_0=100,\qquad \mu=0.05,\qquad \sigma=0.40,\qquad T=1 .
\label{eq:gbm-params}
\end{equation}
代入得
\begin{equation}
\E[S_T]=100e^{0.05}=105.127110,\qquad
\Var(S_T)=100^{2}e^{0.1}\bigl(e^{0.16}-1\bigr)=1917.591686 .
\label{eq:gbm-moments-num}
\end{equation}

\why{方差很大（标准差 $\approx43.8$，相对波动 $\approx41.7\%$）。当
$M=3\times10^{5}$ 条路径时，均值的蒙特卡洛标准误约为
$43.8/\sqrt{3\times10^{5}}\approx0.080$。这说明\textbf{抽样噪声
\en{sampling noise}与离散偏差\en{discretisation bias}必须分开处理}——
这正是原报告反复强调「耦合」的原因。}

% ============================================================
\section{离散化：欧拉--丸山与米尔斯坦格式的推导}
\label{sec:discretisation}
% ============================================================

\subsection{欧拉--丸山格式（式(10)）}

\why{SDE 的积分形式里两个积分都算不出来（需要知道整条路径）。最朴素的办法是：
在一个步长内把系数「冻结」在左端点。这与伊藤积分本身取左端点天然一致。}

对单步 $[t_n,t_{n+1}]$ 写积分形式，并把被积的 $S_u$ 近似为
$S_{t_n}\equiv S_n$（常数），于是两个积分都变得平凡：
\begin{equation}
\int_{t_n}^{t_{n+1}}\!\!\mu S_n\,\dd u=\mu S_nh,\qquad
\int_{t_n}^{t_{n+1}}\!\!\sigma S_n\,\dd W_u=\sigma S_n\,\dW_n .
\end{equation}
得到\textbf{欧拉--丸山格式}\en{Euler--Maruyama scheme}：
\begin{equation}
S^{\EM}_{n+1}=S^{\EM}_{n}+\mu S^{\EM}_{n}h+\sigma S^{\EM}_{n}\dW_n
=S^{\EM}_{n}\bigl(1+\mu h+\sigma\dW_n\bigr),
\qquad \dW_n=\sqrt h\,Z_n .
\label{eq:em}
\end{equation}
其中 $Z_n\sim N(0,1)$ 独立，这是 $\dW_n\sim N(0,h)$ 的可实现形式。

\key{这里留下两笔「欠账」：一是冻结系数带来的误差；二是——更关键地——对扩散系数
$\sigma S_u$ 的冻结比对漂移 $\mu S_u$ 的冻结\emph{严重得多}。后者正是 Milstein
的动机。}

\subsection{迭代随机积分（式(11)）}

\why{Milstein 的全部内容，就是把 EM 丢掉的下一项伊藤--泰勒
\en{It\^o--Taylor}项加回来；而那一项就是这个二重随机积分。它必须被显式算出，
才能得到可实现的格式。}

在 $[t_n,s]$ 上用式~\eqref{eq:intWdW} 得 $\int_{t_n}^{s}\dd W_r=W_s-W_{t_n}$；
再对 $s$ 从 $t_n$ 积分到 $t_{n+1}$：
\begin{equation}
\int_{t_n}^{t_{n+1}}\!\!\int_{t_n}^{s}\dd W_r\,\dd W_s
=\int_{t_n}^{t_{n+1}}\bigl(W_s-W_{t_n}\bigr)\dd W_s .
\end{equation}
对 $f(x)=\tfrac12x^2$ 作用于 $W_s-W_{t_n}$（漂移为 0、扩散为 1）：
\begin{equation}
\dd\Bigl[\tfrac12\bigl(W_s-W_{t_n}\bigr)^{2}\Bigr]
=\bigl(W_s-W_{t_n}\bigr)\dd W_s+\tfrac12\,\dd s .
\end{equation}
两端从 $t_n$ 积到 $t_{n+1}$，得
\begin{equation}
\int_{t_n}^{t_{n+1}}\!\!\int_{t_n}^{s}\dd W_r\,\dd W_s
=\tfrac12\bigl(W_{t_{n+1}}-W_{t_n}\bigr)^{2}-\tfrac12h
=\tfrac12\Bigl[(\dW_n)^{2}-h\Bigr].
\label{eq:iterated}
\end{equation}

\key{一个漂亮的检验：$\dW_n=\sqrt h\,Z$ 且 $\E[Z^2]=1$，故
\begin{equation}
\E\Bigl[\tfrac12\bigl(hZ^{2}-h\bigr)\Bigr]=0,\qquad
\Var\Bigl[\tfrac12\bigl(hZ^{2}-h\bigr)\Bigr]
=\frac{h^{2}}{4}\Var(Z^{2})=\frac{h^{2}}{2}=O(h^{2}).
\label{eq:iterated-var}
\end{equation}
即该积分项均值 $0$、标准差 $h/\sqrt2$——\textbf{典型大小是 $O(h)$ 阶，与漂移项同阶}。
所以 EM 丢掉它不是丢高阶小量，而是丢了一个真正的 $O(h)$ 项，这直接解释了
EM 强阶为何只有 $1/2$。}

\subsection{米尔斯坦格式（式(12)）}

\why{EM 把扩散系数 $b(s)=\sigma s$ 冻结成 $b(S_n)$，但 $b$ 在一步内其实在变化。
把 $b$ 也在 $S_n$ 处作一阶展开，并保留伊藤--泰勒的二重积分项，
即可消掉领先的 $O(h)$ 误差。}

按 $b(S_u)\approx b(S_n)+b'(S_n)(S_u-S_n)$ 展开，并注意一步内
$S_u-S_n\approx b(S_n)(W_u-W_{t_n})$（漂移贡献为更高阶）：
\begin{equation}
\int_{t_n}^{t_{n+1}}\!\! b(S_u)\,\dd W_u
\approx b(S_n)\,\dW_n
+b(S_n)b'(S_n)\int_{t_n}^{t_{n+1}}\!\!\int_{t_n}^{s}\dd W_r\,\dd W_s .
\label{eq:milstein-motivation}
\end{equation}
对 GBM，$b(s)=\sigma s$，故 $b'(s)=\sigma$，
$b(S_n)b'(S_n)=\sigma^{2}S_n$。代入式~\eqref{eq:iterated} 得到
\textbf{米尔斯坦格式}\en{Milstein scheme}：
\begin{equation}
S^{\Mil}_{n+1}=S^{\Mil}_{n}+\mu S^{\Mil}_{n}h+\sigma S^{\Mil}_{n}\dW_n
+\tfrac12\sigma^{2}S^{\Mil}_{n}\Bigl[(\dW_n)^{2}-h\Bigr].
\label{eq:milstein}
\end{equation}

\key{把它写成乘子形式，并与精确解的一步乘子比较：
\begin{align}
S^{\Mil}_{n+1}
&=S^{\Mil}_{n}\Bigl[1+\mu h+\sigma\dW_n+\tfrac12\sigma^{2}
\bigl((\dW_n)^{2}-h\bigr)\Bigr],
\label{eq:milstein-mult}\\
e^{(\mu-\frac12\sigma^{2})h+\sigma\dW_n}
&=1+\sigma\dW_n+\bigl(\mu-\tfrac12\sigma^{2}\bigr)h
+\tfrac12\sigma^{2}(\dW_n)^{2}+O(h^{3/2}).
\label{eq:exact-mult}
\end{align}
二者到 $O(h)$ \textbf{完全一致}：Milstein 乘子正是精确乘子的二阶泰勒截断。
这解释了它为何能把标量强阶由 $1/2$ 提升到 $1$，而弱阶仍为 $1$。}

\subsection{精确转移与路径耦合（式(13)）}

\why{要测量「离散误差」，必须让三个解面对\emph{完全相同的随机性}，
否则量到的是抽样噪声。}

对同一个 $\dW_n$，由式~\eqref{eq:gbm-exact} 在 $[t_n,t_{n+1}]$ 上取比例，
得\textbf{精确转移}\en{exact transition}：
\begin{equation}
S^{\exact}_{n+1}=S^{\exact}_{n}
\exp\Bigl[\bigl(\mu-\tfrac12\sigma^{2}\bigr)h+\sigma\dW_n\Bigr].
\label{eq:exact-step}
\end{equation}
于是精确解、EM、Milstein 三条路径\textbf{共用同一个增量序列} $\{\dW_n\}$。
这种做法称为\textbf{路径耦合}\en{pathwise coupling}，也常称为共用随机数
\en{common random numbers}。

\why{定量理由：若精确路径与数值路径相互\emph{独立}，则差值方差包含两条路径各自的方差
（约为 $2\Var(S_T)$），蒙特卡洛标准误为 $O(M^{-1/2})$。当 $M=3\times10^{5}$ 时
该标准误约为 $0.11$，而 $h=1/256$ 处真实误差仅约 $0.59$——同一量级，
斜率会被噪声完全淹没。耦合后差值方差大幅缩小，收敛阶才可辨。}

% ============================================================
\section{强收敛、弱收敛与误差估计量}
\label{sec:convergence}
% ============================================================

\subsection{强收敛（式(14)）}

\begin{definition}[强收敛 \en{strong convergence}]
若对任意足够细的步长 $h$ 有
\begin{equation}
\Bigl(\E\bigl|S^{(h)}_N-S_T\bigr|^{2}\Bigr)^{1/2}\le C h^{p},
\qquad h\longrightarrow 0,
\end{equation}
则称该格式的\textbf{强收敛阶}\en{strong order of convergence}为 $p$。
\end{definition}

强收敛是\textbf{逐路径精度}\en{pathwise accuracy}，关心单条路径的准确性，
适用于对冲\en{hedging}、路径依赖期权\en{path-dependent option}与耦合构造。
其估计量（终端强误差）为
\begin{equation}
\hat e_s(h)=\frac{1}{M}\sum_{m=1}^{M}
\Bigl|S^{(h)}_{N,m}-S^{\exact}_{T,m}\Bigr| .
\label{eq:strong}
\end{equation}

\why{为什么用平均绝对误差（MAE, \en{mean absolute error}）而不是均方根误差？
两者满足相同的收敛阶，但绝对值对少数极端路径不敏感，蒙特卡洛方差更小，
拟合出的斜率更稳定。}

\why{斜率怎么估？取若干步长 $h_j$，令 $y_j=\log\hat e_s(h_j)$、
$x_j=\log h_j$。若 $\hat e_s(h)\approx Ch^p$，则 $y_j\approx\log C+p\,x_j$
是一条直线，用最小二乘拟合斜率即得 $p$（详见 \S\ref{sec:uq}）。}

\subsection{弱收敛（式(15)）}

\begin{definition}[弱收敛 \en{weak convergence}]
若对属于某类光滑检验函数\en{test function}的 $\phi$ 有
\begin{equation}
\bigl|\E\,\phi\bigl(S^{(h)}_N\bigr)-\E\,\phi(S_T)\bigr|\le C h^{q},
\end{equation}
则称该格式的\textbf{弱收敛阶}\en{weak order of convergence}为 $q$。
\end{definition}

弱收敛是\textbf{分布级精度}\en{law-level accuracy}，关心期望（价格）而非路径，
用于欧式期权定价\en{European option pricing}。弱误差记为
\begin{equation}
e_w(h)=\Bigl|\E\,\phi\bigl(S^{(h)}_N\bigr)-\E\,\phi(S_T)\Bigr| .
\label{eq:weak}
\end{equation}

\subsection{解析偏差基准（式(16)）}

\why{弱误差需要 $\E\phi(S_T)$，一般要蒙特卡洛，噪声很大。但对线性检验函数
$\phi(s)=s$，GBM 给出闭式答案，可以\textbf{完全无噪声}地测出弱阶。}

记两个格式的一步乘子（multiplier）为
\begin{equation}
M_{\EM}=1+\mu h+\sigma\dW_n,\qquad
M_{\Mil}=1+\mu h+\sigma\dW_n+\tfrac12\sigma^{2}\bigl[(\dW_n)^{2}-h\bigr].
\end{equation}
\textbf{关键观察}：两个乘子的条件期望都等于 $1+\mu h$。这里 $\F_n$ 表示到时刻
$t_n$ 的 $\sigma$-代数\en{filtration}（已有信息）：
\begin{align}
\E\bigl[M_{\EM}\mid\F_n\bigr]
&=1+\mu h+\sigma\underbrace{\E[\dW_n]}_{=0}=1+\mu h,
\label{eq:mult-em}\\
\E\bigl[M_{\Mil}\mid\F_n\bigr]
&=1+\mu h+\tfrac12\sigma^{2}
\Bigl(\underbrace{\E\bigl[(\dW_n)^{2}\bigr]}_{=h}-h\Bigr)=1+\mu h .
\label{eq:mult-mil}
\end{align}
式~\eqref{eq:mult-mil} 用了
$\E[(\dW_n)^2]=\Var(\dW_n)+\bigl(\E\dW_n\bigr)^2=h$，
即式~\eqref{eq:incr-scale}。

于是用\textbf{迭代期望}（塔性质 \en{tower property}）逐步回推：
\begin{equation}
\E[S_{n+1}]=\E\bigl[\E[S_nM_n\mid\F_n]\bigr]=\E[S_n]\cdot(1+\mu h).
\end{equation}
递推 $N$ 次（从 $S_0$ 出发）得
\begin{equation}
\E\bigl[S^{\EM}_N\bigr]=\E\bigl[S^{\Mil}_N\bigr]=S_0(1+\mu h)^{N}.
\label{eq:em-mil-mean}
\end{equation}

\key{两个含义：(i) EM 与 Milstein 的期望价格\textbf{完全相同}，
故式~\eqref{eq:em-mil-mean} 对两者通用——这正是原报告表 2 中
「exact weak-bias 列由两者共用」的原因；(ii) 该式对任意 $N$
\emph{精确成立}（不是渐近近似），因此是一个零噪声的基准 oracle。}

\subsection{偏差的一阶渐近（式(17)(18)）}

\why{$(1+\mu h)^N$ 是精确值却看不出「阶」。把它展开成 $h$ 的幂，
就能读出主项与阶，从而预测回归斜率应当等于 $1$。}

用 $N=T/h$ 与标准的泰勒展开
$\log(1+\mu h)=\mu h-\tfrac12\mu^{2}h^{2}+O(h^{3})$：
\begin{align}
(1+\mu h)^{T/h}
&=\exp\Bigl[\frac{T}{h}\log(1+\mu h)\Bigr]
=\exp\Bigl[\frac{T}{h}\Bigl(\mu h-\tfrac12\mu^{2}h^{2}+O(h^{3})\Bigr)\Bigr]
\notag\\
&=\exp\Bigl[\mu T-\tfrac12\mu^{2}Th+O(h^{2})\Bigr]
=S_0^{-1}S_0e^{\mu T}\Bigl[1-\tfrac12\mu^{2}Th+O(h^{2})\Bigr],
\label{eq:bias-expand}
\end{align}
其中最后一步用了 $e^{x}=1+x+O(x^{2})$。与精确期望 $S_0e^{\mu T}$ 相减并取绝对值：
\begin{equation}
e_w(h)=\bigl|S_0(1+\mu h)^{T/h}-S_0e^{\mu T}\bigr|
=\tfrac12S_0e^{\mu T}\mu^{2}Th+O(h^{2}).
\label{eq:bias-first-order}
\end{equation}

\key{主项与 $h$ \textbf{成正比}，故弱阶 $q=1$，\textbf{对 EM 与 Milstein 都成立}
（因为式~\eqref{eq:em-mil-mean} 相同）。}

\begin{example}[数值感受]
渐近系数为
$\tfrac12\times105.127\times0.05^{2}\times1=0.13141$，
即 $e_w(h)\approx0.13141\,h$。原报告在 $h=0.25$ 处报告偏差 $0.032576$，
即 $0.1303\,h$，与渐近系数已很接近；拟合斜率为 $0.9982$，与 $q=1$ 精确吻合。
\end{example}

% ============================================================
\section{正性分析}
\label{sec:positivity}
% ============================================================

\subsection{EM 的一步正性条件与失败概率（式(19)(20)）}

\why{真解 $S_t>0$ 恒成立（因为式~\eqref{eq:gbm-exact} 是指数形式），
但 EM 是\textbf{线性}更新，乘子可能为负，导致价格变负、失去金融意义。
我们需要把这个结构性缺陷量化为一个概率。}

EM 一步为 $S_{n+1}=S_n\bigl(1+\mu h+\sigma\dW_n\bigr)$。
写 $\dW_n=\sqrt h\,Z_n$，$Z_n\sim N(0,1)$。只要 $S_n>0$，
$S_{n+1}$ 的符号就\textbf{完全由乘子决定}：
\begin{equation}
1+\mu h+\sigma\sqrt h\,Z_n>0
\quad\Longleftrightarrow\quad
Z_n>-\frac{1+\mu h}{\sigma\sqrt h}.
\label{eq:pos-condition}
\end{equation}
失败（即 $S_{n+1}\le0$）当且仅当上式反向，于是\textbf{一步失败概率}
\en{one-step failure probability}为
\begin{equation}
p_{\mathrm{neg,EM}}(h)
=\Prob\Bigl(Z<-\frac{1+\mu h}{\sigma\sqrt h}\Bigr)
=\Phi\Bigl(-\frac{1+\mu h}{\sigma\sqrt h}\Bigr)>0 .
\label{eq:pneg}
\end{equation}
其中 $\Phi$ 是标准正态分布函数\en{standard normal CDF}。

\key{该概率恒为正（高斯尾部再小也不为零），故 EM 在价格空间
\textbf{永远不保正}\en{not positivity preserving}。这是格式的结构性缺陷，
不是参数选择问题。}

\begin{example}[与观测对照：用式~\eqref{eq:gbm-params} 的参数]
\begin{itemize}[leftmargin=1.6em]
\item $h=1$：阈值为 $-1.05/0.4=-2.625$，
      $\Phi(-2.625)=0.00433$，即 $0.433\%$。此时 $N=1$，单步即全程，
      与观测 $0.435\%$ 相符。
\item $h=1/2$：阈值为 $-1.025/(0.4\times0.7071)=-3.624$，
      $\Phi(-3.624)=1.45\times10^{-4}$；全程 $N=2$ 步约为
      $2.9\times10^{-4}$，即 $0.029\%$，与观测 $0.034\%$ 相符。
\item $h\le1/4$：阈值 $\le-5.13$，$\Phi\approx1.4\times10^{-7}$，
      $N=4$ 步约为 $5.8\times10^{-7}$；乘以 $3\times10^{5}$ 条路径，
      期望出现不到一条，故观测为零。
\end{itemize}
因此「细网格观测为 $0$」的含义是\textbf{样本中未抽到}，
而不是数学保证。尾部衰减极快：阈值每增大 $1$，$\Phi$ 缩小约一个半数量级。
\end{example}

\subsection{Milstein 的二次乘子与最小值（式(21)(22)）}

\why{Milstein 的乘子是 $Z$ 的\textbf{二次函数}，而二次函数有下界；
下界是否大于零，就决定了它能否保正。}

把 $\dW_n=\sqrt h\,Z_n$ 代入 Milstein 乘子：
\begin{equation}
q(z)=1+\mu h+\sigma\sqrt h\,z+\tfrac12\sigma^{2}\bigl(hz^{2}-h\bigr)
=\tfrac12\sigma^{2}h\,z^{2}+\sigma\sqrt h\,z+1+\mu h-\tfrac12\sigma^{2}h .
\label{eq:milstein-quadratic}
\end{equation}
\textbf{配方}（把一次项吸收进完全平方）：
\begin{align}
q(z)&=\tfrac12\sigma^{2}h\Bigl(z+\frac{1}{\sigma\sqrt h}\Bigr)^{2}
-\frac12+1+\mu h-\tfrac12\sigma^{2}h \notag\\
&=\underbrace{\tfrac12+\mu h-\tfrac12\sigma^{2}h}_{=:\,q_{\min}}
+\tfrac12\sigma^{2}h\Bigl(z+\frac{1}{\sigma\sqrt h}\Bigr)^{2}
\;\ge\;q_{\min},
\label{eq:milstein-qmin}
\end{align}
因为最后一项 $\ge0$，最小值在 $z^{*}=-1/(\sigma\sqrt h)$ 处取得：
\begin{equation}
q_{\min}=\tfrac12+\mu h-\tfrac12\sigma^{2}h .
\end{equation}

\begin{example}[本参数下为何 Milstein 从不违反正性]
$\mu=0.05$，$\sigma=0.40$，故 $\tfrac12\sigma^{2}h=0.08h$，于是
\begin{equation}
q_{\min}(h)=\tfrac12+0.05h-0.08h=\tfrac12-0.03h\ge0.47>0
\qquad(0<h\le1).
\end{equation}
这解释了原报告为何在 Milstein 下从未观测到正性违反。但 $q_{\min}$ 依赖
$\mu,\sigma,h$：若 $\sigma$ 很大或 $\mu$ 负得较多，$q_{\min}$ 可以变负——
因此 Milstein \textbf{不是无条件保正}\en{unconditional positivity preservation}。
\end{example}

% ============================================================
\section{非仿射随机波动率模型}
\label{sec:nonaffine}
% ============================================================

\subsection{模型定义（式(6)(7)(8)）}

记 $X_t=\log S_t$。所给模型为
\begin{align}
\dd X_t&=\Bigl(\mu-\tfrac12g(Y_t)^{2}\Bigr)\dd t+g(Y_t)\,\dd W^{(1)}_t,
\label{eq:na-x}\\
\dd Y_t&=\kappa(\theta-Y_t)\,\dd t+\xi\sqrt{1+Y_t^{2}}\,\dd W^{(2)}_t,
\label{eq:na-y}\\
g(y)&=\sigma_{\min}+\frac{\sigma_{\max}-\sigma_{\min}}{1+e^{-y}},
\qquad \dd\langle W^{(1)},W^{(2)}\rangle_t=\rho\,\dd t .
\label{eq:na-g}
\end{align}
其中 $\kappa$ 为均值回复速度\en{mean-reversion speed}，$\theta$ 为长期均值
\en{long-run mean}，$\xi$ 为波动率的波动率\en{vol-of-vol}，
$\rho$ 为相关系数\en{correlation}（此处 $\rho=-0.7$ 体现杠杆效应
\en{leverage effect}：股价下跌 $\Rightarrow$ 波动率上升）。
基准参数为
\begin{equation}
\begin{gathered}
S_0=100,\quad Y_0=0,\quad \mu=0.05,\quad \kappa=2,\quad \theta=-0.2,\quad \xi=0.6,\\
\rho=-0.7,\quad \sigma_{\min}=0.10,\quad \sigma_{\max}=0.50,\quad T=1 .
\end{gathered}
\label{eq:na-params}
\end{equation}

\why{为什么叫「非仿射」\en{non-affine}？因为波动率 $g(Y_t)$ 对 $Y$ 不是线性函数，
也不是 $S$ 的常数倍（对比 Heston 模型的仿射结构）。因此该模型\textbf{没有闭式解}，
只能数值求解——这正是「没有精确转移时怎么办」这一研究问题的由来。}

\subsection{模型正则性与可用理论}

\why{标准 EM 收敛定理要求系数满足全局 Lipschitz 条件\en{global Lipschitz condition}
与线性增长条件\en{linear growth condition}。必须逐条核对本模型是否满足，
否则「EM 强阶 $1/2$」的说法就没有依据。}

\begin{itemize}[leftmargin=1.6em]
\item $g$ 的值域为 $(\sigma_{\min},\sigma_{\max})=(0.10,0.50)$，故 $g$
      \textbf{有界}\en{bounded}；且
      $g'(y)=(\sigma_{\max}-\sigma_{\min})\dfrac{e^{-y}}{(1+e^{-y})^{2}}$
      亦有界。
\item $\dfrac{\dd}{\dd y}\sqrt{1+y^{2}}=\dfrac{y}{\sqrt{1+y^{2}}}$，
      其绝对值 $\le1$，故 $y\mapsto\sqrt{1+y^{2}}$ 是全局 Lipschitz 且线性增长的
      （注意：$\sqrt{1+y^2}$ 本身不是线性函数，但由 $|y|/\sqrt{1+y^2}\le1$
      可推出 $|\sqrt{1+y_1^2}-\sqrt{1+y_2^2}|\le|y_1-y_2|$）。
\item 漂移 $\kappa(\theta-y)$ 显然全局 Lipschitz。
\end{itemize}

因此「全局 Lipschitz 且线性增长 $\Rightarrow$ EM 强阶 $1/2$、弱阶 $1$」
的标准结论适用，为后面的实测强阶 $0.5111$ 提供了理论预期。
但需注意：下方使用的有限参考解\en{numerical reference}仍然是数值基准，
并非闭式 oracle。

\subsection{相关布朗增量的构造（式(23)(24)）}

\why{模型含两个相关系数为 $\rho$ 的布朗运动。要用两个\emph{独立}标准正态随机数
作线性变换（Cholesky 分解 \en{Cholesky factorisation}）来\textbf{精确}实现
该相关结构，而不是近似。}

取 $Z_{1,n},Z_{2,n}\stackrel{iid}{\sim}N(0,1)$，令
\begin{equation}
\dW^{(1)}_n=\sqrt h\,Z_{1,n},\qquad
\dW^{(2)}_n=\sqrt h\Bigl(\rho Z_{1,n}+\sqrt{1-\rho^{2}}\,Z_{2,n}\Bigr).
\label{eq:corr-increments}
\end{equation}
\textbf{验证}（利用 $Z_1\perp Z_2$）：
\begin{align}
\Var\bigl(\dW^{(1)}_n\bigr)&=h,\qquad
\Var\bigl(\dW^{(2)}_n\bigr)=h\bigl(\rho^{2}+(1-\rho^{2})\bigr)=h,
\label{eq:corr-var}\\
\Cov\bigl(\dW^{(1)}_n,\dW^{(2)}_n\bigr)
&=h\,\E\bigl[Z_1\bigl(\rho Z_1+\sqrt{1-\rho^{2}}Z_2\bigr)\bigr]
=h\bigl(\rho\cdot1+\sqrt{1-\rho^{2}}\cdot0\bigr)=\rho h,
\label{eq:corr-cov}
\end{align}
于是相关系数\en{correlation coefficient}恰为
\begin{equation}
\Corr=\frac{\rho h}{\sqrt h\cdot\sqrt h}=\rho .
\label{eq:corr-check}
\end{equation}

\key{$\sqrt{1-\rho^{2}}$ 的作用是保证 $\dW^{(2)}$ 的方差恰好为 $h$。
若漏掉它，它就不是标准布朗增量，模型被改变。这也解释了自动检验为何同时检查
方差 $(1,1)$ 与相关系数 $-0.7$：它们分别锁定式~\eqref{eq:corr-var}
与式~\eqref{eq:corr-check}。}

\subsection{非仿射模型的 EM 格式（式(25)(26)(27)）}

\why{推导逻辑与 \S\ref{sec:discretisation} 完全相同：把每个系数冻结在左端点。
唯一的细节是漂移里的 $g$ 也必须用 $Y_n$（左端点已知值），
因为 $g(Y_u)$ 在步内是未知的。}

\begin{align}
X_{n+1}&=X_n+\Bigl(\mu-\tfrac12g(Y_n)^{2}\Bigr)h+g(Y_n)\,\dW^{(1)}_n,
\label{eq:na-em-x}\\
Y_{n+1}&=Y_n+\kappa(\theta-Y_n)h+\xi\sqrt{1+Y_n^{2}}\,\dW^{(2)}_n,
\label{eq:na-em-y}\\
S_{n+1}&=e^{X_{n+1}}>0 .
\label{eq:na-positivity}
\end{align}

\key{式~\eqref{eq:na-positivity} 的保正是\textbf{结构性}的\en{structural}：
指数函数的值域为 $(0,\infty)$，无论 $X_n$ 多么极端（甚至 $X_n\to-\infty$），
都有 $e^{X_n}>0$。它不是从有限样本推断出的经验性质，而是由变量替换
$X=\log S$ 保证的。原报告图 5 的措辞「enforced by the model representation
rather than inferred from a finite sample」正指此点。}

\subsection{为什么不对该模型使用标量 Milstein}

\why{按两个独立布朗驱动写出扩散向量场后：$g$ 依赖 $Y$，
$\sqrt{1+Y^{2}}$ 依赖 $Y$，而 $X$ 的扩散也依赖 $Y$，因此\textbf{交叉导数非零}。
标量 Milstein 公式只处理 $\partial b/\partial x\cdot b$ 这一项；
多维 Milstein 还需要交叉项 $\partial b^i/\partial x^j\,b^j$ 以及模拟迭代随机积分
（含 L\'evy 面积 \en{L\'evy area}）。略去这些却声称强阶 $1$，
在数学上是不成立的。}

这是一个很好的严谨性示范：原报告明确\textbf{拒绝}在不实现这些交叉项的情况下
宣称非仿射模型具有强阶 $1$。

% ============================================================
\section{嵌套网格耦合与数值参考解}
\label{sec:nested}
% ============================================================

\subsection{嵌套网格耦合（式(28)）}

\why{粗网格解要与「参考解」比较，但参考解本身也是数值的。若两者使用独立随机数，
比较结果会混入抽样噪声。解决办法：先生成细网格增量，粗增量由细增量\textbf{求和}
得到。}

设细步长 $h_{\Sref}=T/\Nref$，粗步长 $h=K h_{\Sref}$（即粗一步等于细 $K$ 步）。
对每个粗步 $n$，取细步 $Kn,\dots,Kn+K-1$：
\begin{equation}
\dW^{(i)}_{n,\mathrm{coarse}}
=\sum_{j=0}^{K-1}\dW^{(i)}_{Kn+j,\Sref},\qquad i=1,2 .
\label{eq:nested}
\end{equation}

\key{为什么正确：布朗运动具有独立增量，且
\begin{equation}
W_{t_{n+1}}-W_{t_n}
=\sum_{j=0}^{K-1}\Bigl(W_{t_n+(j+1)h_{\Sref}}-W_{t_n+jh_{\Sref}}\Bigr),
\end{equation}
即\textbf{增量的可加性}\en{additivity of increments}。分布上，
\begin{equation}
\sum_{j=0}^{K-1}\dW^{(i)}_{Kn+j,\Sref}\sim N(0,Kh_{\Sref})=N(0,h),
\label{eq:nested-law}
\end{equation}
与直接生成 $\sqrt h\,Z$ \textbf{同分布}。但耦合版本更强：它们是同一个 $\omega$
（同一样本点）上的\textbf{同一条布朗路径}。因此粗解与参考解之差反映的是
纯离散误差，而非抽样噪声。}

这正是原报告算法 1 的结构：先生成细网格增量 $\rightarrow$ 在参考网格上积分
$\rightarrow$ 对每个 $N$ 按式~\eqref{eq:nested} 聚合增量 $\rightarrow$
在粗网格上积分 $\rightarrow$ 存\textbf{成对}的终端差 \en{paired differences}。

\subsection{参考解并非精确解（式(33)）}

\why{必须检验「参考解够不够细」，否则误差趋势可能被参考解的自身偏差污染。}

原报告取 $\Nref=2048$，并在 $4000$ 条新的耦合路径上与 $4096$ 步比较，
得终端价的平均绝对变化
\begin{equation}
\overline{\bigl|\Delta S_T\bigr|}=0.057626,
\qquad 95\%\ \text{置信区间}\ [0.056114,\ 0.059139].
\label{eq:ref-check}
\end{equation}
该量远小于最粗网格的强误差 $0.886$，故参考解足以支撑所观测到的趋势；
但它约为 $N=256$ 处误差（$0.210677$）的 $27\%$，
因此\textbf{不能}据此报告更多终端位数或分辨弱偏差。

\key{「数值参考解 $\ne$ 精确 oracle」是本节的核心信息。原报告因此只用它论证
\emph{强}收敛趋势，而不声称弱阶。}

% ============================================================
\section{置信区间与回归斜率}
\label{sec:uq}
% ============================================================

\subsection{置信区间（式(29)）}

\why{任何蒙特卡洛均值都带抽样误差，必须给出区间，否则无法判断「差异是否真实」。
这是原报告反复强调「不制造弱阶结论」的技术手段。}

设路径级观测\en{path-level observation} $D_1,\dots,D_M$ 独立同分布
（例如 $D_m=S^{(h)}_{N,m}-S^{\exact}_{T,m}$，或成对的看涨期权收益差
\en{paired call-payoff difference}）。令
\begin{equation}
\bar D=\frac{1}{M}\sum_{m=1}^{M}D_m,\qquad
s_D^{2}=\frac{1}{M-1}\sum_{m=1}^{M}\bigl(D_m-\bar D\bigr)^{2},
\label{eq:ci-def}
\end{equation}
则 $95\%$ 置信区间\en{confidence interval}为
\begin{equation}
\bar D\pm1.96\,\frac{s_D}{\sqrt M}.
\label{eq:ci}
\end{equation}

\why{为什么是 $1.96$？由中心极限定理\en{central limit theorem}，$\bar D$ 近似
正态、标准差为 $s_D/\sqrt M$；标准正态的 $97.5\%$ 分位数
$\Phi^{-1}(0.975)=1.95996$，对应双侧 $95\%$。为什么除以 $\sqrt M$？
独立同分布均值的方差为 $\Var(D)/M$，故标准差为 $s_D/\sqrt M$——这就是
蒙特卡洛误差 $O(M^{-1/2})$ 的来源。为什么分母用 $M-1$？
用 $\bar D$ 代替未知真均值损失一个自由度，除以 $M-1$ 才使
$\E[s_D^{2}]=\Var(D)$ 无偏（贝塞尔修正 \en{Bessel's correction}）。}

\begin{remark}
原报告表 4 的看涨期权收益偏差的 $95\%$ 置信区间\textbf{全部包含 $0$}
（例如 $N=32$ 时为 $[-0.006056,\ 0.014005]$）。正确的结论是
「抽样不确定度已与弱偏差相当，数据不支持报告弱阶」，
而\textbf{不是}「弱偏差为零」。这是统计推断纪律的示范。
\end{remark}

\subsection{对数--对数回归斜率及其标准误}

\why{理论上误差为 $Ch^{p}$，但 $C$ 与 $p$ 都未知，我们只有有限网格上的误差观测。
取对数把\textbf{幂律变成直线}，于是可以用标准最小二乘
\en{ordinary least squares} 估出 $p$。}

取 $J$ 个网格 $h_1,\dots,h_J$，令 $y_j=\log\hat e_s(h_j)$、$x_j=\log h_j$。
若 $\hat e_s(h)\approx Ch^{p}$，则
\begin{equation}
y_j=\log C+p\,x_j+\varepsilon_j ,
\label{eq:loglog-model}
\end{equation}
最小二乘估计为
\begin{equation}
\hat p=\frac{\sum_{j=1}^{J}(x_j-\bar x)(y_j-\bar y)}
{\sum_{j=1}^{J}(x_j-\bar x)^{2}},
\qquad
\hat a=\bar y-\hat p\,\bar x\ \ \bigl(\text{即}\ \log\hat C\bigr),
\label{eq:slope}
\end{equation}
斜率的标准误\en{standard error of the slope}为
\begin{equation}
\operatorname{se}(\hat p)
=\sqrt{\frac{\hat\sigma^{2}}{\sum_{j=1}^{J}(x_j-\bar x)^{2}}},
\qquad
\hat\sigma^{2}=\frac{1}{J-2}\sum_{j=1}^{J}
\bigl(y_j-\hat a-\hat p\,x_j\bigr)^{2}.
\label{eq:slope-se}
\end{equation}

\begin{remark}
$\operatorname{se}(\hat p)$ 只刻画\textbf{给定网格范围内直线拟合本身}的不确定性，
它\textbf{不是}重复蒙特卡洛实验的不确定度，也不包含网格范围选择等模型不确定性。
因此「EM 斜率 $0.4899\pm0.0026$」中的 $\pm$ 是回归诊断
\en{regression diagnostic}，而不是蒙特卡洛置信区间。这一点原报告特别声明过。
\end{remark}

% ============================================================
\section{匹配精度下的成本比}
\label{sec:cost}
% ============================================================

\why{绝对误差不能直接比较方法优劣——必须在\textbf{同一精度目标}下比成本，
否则「Milstein 更准」并不能推出「Milstein 更划算」。}

预先声明目标 $\E|S_N-S_T|\le0.85$。查 GBM 收敛表：
\begin{itemize}[leftmargin=1.6em]
\item EM：$N=64$ 时 $1.18565>0.85$ 不达标；$N=128$ 时 $0.838329\le0.85$
      达标，故 $N_{\EM}=128$。
\item Milstein：$N=2$（即 $h=0.5$）时 $0.75433\le0.85$ 达标，
      故 $N_{\Mil}=2$。
\end{itemize}
在「每步一次系数求值」的步数成本度量\en{declared cost measure}下：
\begin{equation}
\frac{C_{\EM}}{C_{\Mil}}=\frac{128}{2}=64 .
\label{eq:cost-ratio}
\end{equation}

\begin{remark}[重要限定]
这是\textbf{算法步数比}，不是墙钟加速比\en{wall-clock speedup}。理由：
(i) Milstein 每步多算一个修正项 $(\dW_n)^2-h$，浮点运算更多；
(ii) 未计入随机数生成、内存分配、编译与 I/O 开销。
此外该比较还隐含一个「负面结论」：在极宽松的精度要求下，EM 更廉价的代数
可能反而有利，而本目标区间并未覆盖该区域。
\end{remark}

% ============================================================
\section{诊断量与结果汇总}
\label{sec:summary}
% ============================================================

\subsection{增量与参考解诊断（式(32)(33)）}

\why{嵌套耦合与相关增量的正确性必须被\textbf{独立检验}，
否则强收敛结果可能源于错误的随机数缩放或错误的相关系数。}

增量诊断（检验式~\eqref{eq:corr-check}）：
\begin{equation}
\frac{\widehat{\Var}\bigl(\dW^{(1)}\bigr)}{h}=1.00526,\qquad
\frac{\widehat{\Var}\bigl(\dW^{(2)}\bigr)}{h}=1.00346,\qquad
\widehat{\Corr}=-0.70185 ,
\label{eq:diag}
\end{equation}
对照目标 $(1,\,1,\,-0.7)$。另外 $20000$ 条参考路径全部有限且为正。

\why{为什么方差估计要除以 $h$？因为标准布朗增量满足 $\Var(\dW)=h$，
所以「方差估计 $\div\,h$」应接近 $1$。这样定义的检验量无量纲、
与步长无关，从而成为一个干净的检验。}

\subsection{理论阶与实测阶对照}

\begin{table}[htbp]
\centering
\caption{理论收敛阶与实测阶对照}
\label{tab:orders}
\begin{tabular}{lccc}
\toprule
对象 & 理论阶 & 实测阶 & 结论\\
\midrule
EM 强阶 & $1/2$ & $0.4899\pm0.0026$ & 一致\\
Milstein 强阶 & $1$ & $0.9099\pm0.0167$ & 接近 $1$（前渐近效应）\\
均值弱偏差阶 & $1$ & $0.9982\pm0.0004$ & 一致\\
非仿射 EM 强阶 & $1/2$ & $0.5111\pm0.0047$ & 一致\\
非仿射弱阶 & $1$ & 未报告 & 置信区间含 $0$，数据不足\\
\bottomrule
\end{tabular}
\end{table}

\subsection{GBM 耦合收敛数值表}

\begin{table}[htbp]
\centering
\caption{GBM 耦合收敛（$M=300{,}000$ 条路径）}
\label{tab:gbm-conv}
\begin{tabular}{rcccc}
\toprule
$N$ & $h$ & EM 强误差 MAE & Milstein 强误差 MAE & 精确均值偏差\\
\midrule
4   & 0.250000   & 4.52887  & 0.460308  & 0.0325759\\
8   & 0.125000   & 3.28870  & 0.268833  & 0.0163567\\
16  & 0.062500   & 2.34715  & 0.149881  & 0.00819567\\
32  & 0.031250   & 1.67424  & 0.0800666 & 0.00410218\\
64  & 0.015625   & 1.18565  & 0.0414826 & 0.00205218\\
128 & 0.0078125  & 0.838329 & 0.0211342 & 0.00102636\\
256 & 0.00390625 & 0.594648 & 0.0106906 & 0.000513248\\
\bottomrule
\end{tabular}
\end{table}

\noindent\textbf{快速核对}：EM 的 MAE 在 $h$ 减半时大致乘以
$1/\sqrt2\approx0.707$（$4.52887\to3.28870$，比值 $0.726$）；
Milstein 大致乘以 $1/2$（$0.460308\to0.268833$，比值 $0.584$）；
偏差列精确减半（$0.0325759\to0.0163567$，比值 $0.502$）。

\subsection{全文推导链条一览}

\begin{table}[htbp]
\centering
\caption{推导链条与「为什么」的对应关系}
\label{tab:chain}
\begin{tabular}{p{0.30\linewidth}p{0.62\linewidth}}
\toprule
结果 & 为什么必须这样做\\
\midrule
$(dW)^2=dt$ & 平方的期望是 $h$、方差是 $h^2$ 阶，故 $dW^2$ 与 $dt$ 同阶，
不能丢\\
伊藤公式 $\tfrac12f''$ & 随机情形下 $(\Delta x)^2$ 含 $O(h)$ 项，
与一阶项同阶\\
取对数解 GBM & 把乘性方程变成常系数加性方程，立即可积\\
EM 冻结系数 & 伊藤积分取左端点，与格式天然一致\\
Milstein 加迭代积分 & EM 丢掉的是 $O(h)$ 项（标准差 $h/\sqrt2$），
必须补回\\
路径耦合 & 差值方差从 $\approx2\Var(S_T)$ 降到很小，
否则 $O(M^{-1/2})$ 噪声淹没 $O(h^p)$ 信号\\
$(1+\mu h)^N$ & 两格式乘子条件期望相同，故一阶矩精确可算，
弱阶无噪声可测\\
$p_{\mathrm{neg,EM}}=\Phi(\cdot)$ & 乘子为高斯，负值即线性更新保正失败\\
$q_{\min}$ 配方 & 二次函数有下界，下界符号决定是否保正\\
$X=\log S$ 积分 & 指数值域为 $(0,\infty)$，结构性保正\\
嵌套网格求和 & 布朗增量可加，粗细网格共享同一路径\\
$\bar D\pm1.96\,s_D/\sqrt M$ & CLT + 双侧 $95\%$ + 无偏方差修正\\
$\log$--$\log$ 回归 & 幂律变直线，最小二乘估斜率 $p$\\
\bottomrule
\end{tabular}
\end{table}

% ============================================================
\appendix
\section{符号表}
% ============================================================

\begin{table}[htbp]
\centering
\begin{tabular}{lll}
\toprule
符号 & 含义 & 英文术语\\
\midrule
$W_t$ & 标准布朗运动 & standard Brownian motion\\
$\dW_n$ & 一个步长的布朗增量，$\sim N(0,h)$ & Brownian increment\\
$S_t,S_n$ & 资产价格（连续 / 离散） & asset price\\
$\mu$ & 漂移率 & drift rate\\
$\sigma$ & 波动率 & volatility\\
$h=T/N$ & 时间步长 & time step\\
$Z_n$ & 标准正态随机数 & standard normal variate\\
$\Phi$ & 标准正态分布函数 & standard normal CDF\\
$\F_n$ & 到 $t_n$ 的信息（$\sigma$-代数） & filtration\\
$\rho$ & 两个布朗运动的相关系数 & correlation coefficient\\
$g(\cdot)$ & logistic 波动率函数 & logistic volatility map\\
$\Nref$ & 参考解（细网格）步数 & reference step count\\
$\hat e_s(h)$ & 强误差估计量（终端 MAE） & strong error estimator\\
$e_w(h)$ & 弱误差 & weak error\\
$p_{\mathrm{neg,EM}}$ & EM 一步失败概率 & one-step failure probability\\
$q_{\min}$ & Milstein 二次乘子最小值 & minimum of quadratic multiplier\\
\bottomrule
\end{tabular}
\end{table}

\section{与原 PDF 的对应关系}

\begin{table}[htbp]
\centering
\begin{tabular}{ll}
\toprule
原 PDF 位置 & 本文档位置\\
\midrule
\S2.1 式(1)--(4) & \S\ref{sec:gbm}\\
\S2.2 式(6)--(8) & \S\ref{sec:nonaffine}\\
\S3.1 式(10) & \S\ref{sec:discretisation}\\
\S3.2 式(11)--(12) & \S\ref{sec:discretisation}\\
\S3.3 式(13)--(14) & \S\ref{sec:discretisation}, \S\ref{sec:convergence}\\
\S3.4 式(15)--(18) & \S\ref{sec:convergence}\\
\S3.5 式(19)--(22) & \S\ref{sec:positivity}\\
\S3.6 式(23)--(27) & \S\ref{sec:nonaffine}\\
\S3.7 式(28) & \S\ref{sec:nested}\\
\S3.8 式(29) & \S\ref{sec:uq}\\
\S\S5.2 式(30) & \S\ref{sec:cost}\\
\S5.6 式(32)--(33) & \S\ref{sec:summary}\\
\bottomrule
\end{tabular}
\end{table}

\section{一处排版笔误说明}

原 PDF 式(31) 处印为 \verb|qquad|（缺少反斜杠），正确写法应为
\verb|\qquad|。本文档式~\eqref{eq:gbm-moments-num} 已按正确写法给出。

\end{document}
"""

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(DOC)

print("WROTE:", OUT, os.path.getsize(OUT), "bytes")
raw = open(OUT, "rb").read()
print("BOM:", raw[:3] == b"\xef\xbb\xbf")
txt = raw.decode("utf-8")
print("chars:", len(txt))
print("chinese ok:", "伊藤公式" in txt, "| sample:", txt[txt.index("伊藤公式")-12:txt.index("伊藤公式")+12])

# ---------------- static self-verification ----------------
body = re.sub(r"(?<!\\)%.*", "", txt)   # strip comments

begins = re.findall(r"\\begin\{([^}]*)\}", body)
ends = re.findall(r"\\end\{([^}]*)\}", body)
cb, ce = {}, {}
for e in begins: cb[e] = cb.get(e, 0) + 1
for e in ends:   ce[e] = ce.get(e, 0) + 1
print("\n--- environment balance ---")
bad = False
for k in sorted(set(list(cb) + list(ce))):
    a, b = cb.get(k, 0), ce.get(k, 0)
    flag = "OK" if a == b else "MISMATCH"
    if a != b: bad = True
    print("%-14s begin=%d end=%d  %s" % (k, a, b, flag))
# nesting order check
stack, err = [], []
for m in re.finditer(r"\\(begin|end)\{([^}]*)\}", body):
    if m.group(1) == "begin":
        stack.append(m.group(2))
    else:
        if not stack or stack[-1] != m.group(2):
            err.append((m.group(2), stack[-1] if stack else None))
        else:
            stack.pop()
print("nesting errors:", err if err else "none", "| unclosed:", stack if stack else "none")

labels = set(re.findall(r"\\label\{([^}]*)\}", body))
refs = set(re.findall(r"\\eqref\{([^}]*)\}", body)) | set(re.findall(r"\\ref\{([^}]*)\}", body))
print("\n--- refs ---")
print("labels:", len(labels), "refs:", len(refs))
print("dangling refs:", sorted(refs - labels) if refs - labels else "none")
print("unused labels:", sorted(labels - refs) if labels - refs else "none")

print("\n--- math delimiter balance ---")
print("$$ :", body.count("$$"), "| \\[ ", body.count("\\["), "| \\] ", body.count("\\]"))
inline = re.findall(r"(?<!\$)\$(?!\$)", body)
print("single-$ count:", len(inline), "(must be even)")

print("\n--- suspicious typo scan ---")
for pat in [r"(?<!\\)qquad", r"(?<!\\)Var\b", r"(?<!\\)frac\{", r"qhmath"]:
    hits = re.findall(pat, body)
    print("  %-16s -> %d" % (pat, len(hits)))

print("\n--- macro usage sanity ---")
for mac, expected in [("\\Var", None), ("\\Corr", None)]:
    ctx = re.findall(re.escape(mac) + r"(?![A-Za-z])", body)
    print("  %s used %d times" % (mac, len(ctx)))

print("\n--- \\why / \\key argument balance ---")
for mac in ["\\why", "\\key", "\\en"]:
    cnt = len(re.findall(re.escape(mac) + r"\{", body))
    print("  %s{...} occurrences: %d" % (mac, cnt))

print("\nVERDICT: file written;", "ALL CHECKS NEED REVIEW" if bad or err or stack else "structural checks PASS")
