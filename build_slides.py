from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "Team_H_Code" / "generated"
OUT = ROOT / "output" / "pdf" / "reliable_financial_sdes_slides.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 13.333 * inch, 7.5 * inch
M = 0.62 * inch

pdfmetrics.registerFont(TTFont("Deck", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"))
pdfmetrics.registerFont(TTFont("DeckBold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("DeckItalic", "/System/Library/Fonts/Supplemental/Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("DeckMono", "/System/Library/Fonts/Menlo.ttc"))

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#2A6F97")
TEAL = colors.HexColor("#2A9D8F")
ORANGE = colors.HexColor("#E07A5F")
INK = colors.HexColor("#1D2730")
MUTED = colors.HexColor("#5E6B73")
LINE = colors.HexColor("#D8DEE4")
PALE = colors.HexColor("#F7F8FA")

BODY = ParagraphStyle("body", fontName="Deck", fontSize=18, leading=23, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=15, leading=19)
TINY = ParagraphStyle("tiny", parent=BODY, fontSize=10.5, leading=13, textColor=MUTED)
CENTER = ParagraphStyle("center", parent=BODY, alignment=TA_CENTER)
FORMULA = ParagraphStyle("formula", parent=BODY, fontName="Deck", fontSize=18, leading=23, alignment=TA_CENTER)


def para(c, text, x, y_top, width, height, style=BODY):
    p = Paragraph(text, style)
    _, ph = p.wrap(width, height)
    p.drawOn(c, x, y_top - ph)
    return ph


def footer(c, section, page):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, 0.34 * inch, W - M, 0.34 * inch)
    c.setFont("Deck", 9)
    c.setFillColor(MUTED)
    c.drawString(M, 0.17 * inch, f"Team H   •   {section}")
    c.drawRightString(W - M, 0.17 * inch, f"{page}/27")


def frame(c, title, section, page, footer_note=None):
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFont("DeckBold", 25)
    c.setFillColor(NAVY)
    c.drawString(M, H - 0.55 * inch, title)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(M, H - 0.70 * inch, W - M, H - 0.70 * inch)
    if footer_note:
        para(c, footer_note, M, 0.63 * inch, W - 2 * M, 0.28 * inch, TINY)
    footer(c, section, page)


def bullets(c, items, x, y_top, width, font=18, leading=23, gap=10):
    style = ParagraphStyle("bul", parent=BODY, fontSize=font, leading=leading, leftIndent=18, firstLineIndent=-15)
    y = y_top
    for item in items:
        h = para(c, "<font color='#2A6F97'>•</font> " + item, x, y, width, 2 * inch, style)
        y -= h + gap
    return y


def formula(c, text, x, y_top, width, size=18):
    style = ParagraphStyle("f", parent=FORMULA, fontSize=size, leading=size * 1.35)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    h = para(c, text, x + 8, y_top - 7, width - 16, 1.2 * inch, style)
    c.line(x, y_top - h - 14, x + width, y_top - h - 14)
    return h + 22


def takeaway(c, text, x=M, y=0.78 * inch, width=W - 2 * M):
    c.setStrokeColor(TEAL)
    c.setLineWidth(2.2)
    c.line(x, y + 0.10 * inch, x + 0.55 * inch, y + 0.10 * inch)
    style = ParagraphStyle("take", parent=SMALL, fontName="DeckBold", textColor=INK)
    para(c, text, x + 0.68 * inch, y + 0.25 * inch, width - 0.68 * inch, 0.45 * inch, style)


def image_contain(c, path, x, y, w, h):
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, preserveAspectRatio=True, mask="auto")


def table(c, rows, x, y_top, widths, row_heights=None, font=14):
    data = []
    cell_style = ParagraphStyle("cell", parent=SMALL, fontSize=font, leading=font * 1.25)
    head_style = ParagraphStyle("head", parent=cell_style, fontName="DeckBold", textColor=colors.white)
    for i, row in enumerate(rows):
        data.append([Paragraph(str(v), head_style if i == 0 else cell_style) for v in row])
    t = Table(data, colWidths=widths, rowHeights=row_heights)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    _, th = t.wrap(sum(widths), 5 * inch)
    t.drawOn(c, x, y_top - th)
    return th


def end_page(c):
    c.showPage()


c = Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
c.setTitle("Reliable Numerical Simulation of Financial SDEs")
c.setAuthor("Team H")

# 1 — cover
c.setFillColor(colors.white); c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(NAVY); c.setFont("DeckBold", 34)
c.drawString(M, H - 0.85 * inch, "Reliable Numerical Simulation of Financial SDEs")
c.setFont("Deck", 21); c.drawString(M, H - 1.28 * inch, "GBM Benchmarks and a Non-Affine Volatility Model")
c.setStrokeColor(BLUE); c.setLineWidth(2); c.line(M, H - 1.52 * inch, W - M, H - 1.52 * inch)
table(c, [
    ["Team H", "Role"],
    ["Jinyang Wang, 2364059", "Project Manager"],
    ["Yangxiaoxiang Zheng, 1929725", "Mathematical Theory"],
    ["Jinsen Chen, 2363993", "Algorithm Implementation"],
    ["Zheyuan Zheng, 2362114", "Visualization & Report"],
    ["Dongdong Hao, 2364312", "Testing & Validation"],
], M, H - 1.9 * inch, [3.55 * inch, 3.25 * inch], font=14)
para(c, "Department of Applied Mathematics<br/>18 September 2026", 8.4 * inch, H - 2.15 * inch, 3.8 * inch, 1 * inch, BODY)
footer(c, "Project overview", 1); end_page(c)

# 2
frame(c, "Motivation and central question", "Project overview", 2)
bullets(c, [
    "Numerical SDE solvers introduce <b>time-discretisation error</b>.",
    "Monte Carlo simulation introduces <b>sampling uncertainty</b>.",
    "Mixing the two can invalidate a claimed convergence order.",
], M, H - 1.25 * inch, W - 2 * M, font=21, leading=27, gap=20)
para(c, "<b>How can coupled simulations separate discretisation error from Monte Carlo noise?</b>", M, H - 3.9 * inch, W - 2 * M, 0.9 * inch, ParagraphStyle("q", parent=CENTER, fontName="DeckBold", fontSize=28, leading=34, textColor=NAVY))
takeaway(c, "Use exact GBM oracles first, then transfer the same coupling logic to a non-affine model.")
end_page(c)

# 3
frame(c, "Research questions", "Project overview", 3, "Reproduced from Section 1.2 of the team report.")
bullets(c, [
    "Do coupled simulations recover the predicted GBM strong orders 1/2 (EM) and 1 (Milstein), and weak order 1 for the mean?",
    "At a matched strong-error target, which method uses fewer time-step coefficient evaluations?",
    "When can price-space updates lose positivity, and does the simulated terminal law agree with the exact lognormal distribution?",
    "For the non-affine model, do nested-grid EM solutions converge, pass Brownian-increment checks, remain finite and positive, and use a sufficiently resolved numerical reference?",
], M, H - 1.18 * inch, W - 2 * M, font=17, leading=22, gap=13)
end_page(c)

# 4
frame(c, "GBM dynamics and exact path", "Mathematical theory", 4)
y = H - 1.08 * inch
for txt in [
    "(1)  dS<sub>t</sub> = μS<sub>t</sub>dt + σS<sub>t</sub>dW<sub>t</sub>,   S<sub>0</sub> &gt; 0",
    "(2)  d log S<sub>t</sub> = (μ − ½σ²)dt + σdW<sub>t</sub>",
    "(3)  S<sub>t</sub> = S<sub>0</sub> exp[(μ − ½σ²)t + σW<sub>t</sub>]",
    "(4)  E[S<sub>T</sub>] = S<sub>0</sub>e<super>μT</super>,   Var(S<sub>T</sub>) = S<sub>0</sub>²e<super>2μT</super>(e<super>σ²T</super> − 1)",
]:
    y -= formula(c, txt, 1.25 * inch, y, W - 2.5 * inch, 19) + 4
takeaway(c, "The exact transition gives a pathwise oracle, not merely a moment benchmark.")
end_page(c)

# 5
frame(c, "Benchmark parameters and non-affine state equations", "Mathematical theory", 5)
y = H - 1.08 * inch
for txt in [
    "(5)  S<sub>0</sub>=100,   μ=0.05,   σ=0.40,   T=1",
    "(6)  dX<sub>t</sub> = (μ − ½g(Y<sub>t</sub>)²)dt + g(Y<sub>t</sub>)dW<sub>t</sub><super>(1)</super>",
    "(7)  dY<sub>t</sub> = κ(θ − Y<sub>t</sub>)dt + ξ√(1+Y<sub>t</sub>²)dW<sub>t</sub><super>(2)</super>",
    "(8)  g(y)=σ<sub>min</sub>+(σ<sub>max</sub>−σ<sub>min</sub>)/(1+e<super>−y</super>),   d⟨W<super>(1)</super>,W<super>(2)</super>⟩<sub>t</sub>=ρdt",
]:
    y -= formula(c, txt, 1.0 * inch, y, W - 2.0 * inch, 17) + 3
takeaway(c, "X = log S enforces positive reconstructed prices, while g keeps volatility bounded.")
end_page(c)

# 6
frame(c, "Parameters and global Lipschitz conditions", "Mathematical theory", 6)
formula(c, "(9)  S₀=100, Y₀=0, μ=0.05, κ=2, θ=−0.2, ξ=0.6, ρ=−0.7, σmin=0.10, σmax=0.50, T=1", M, H - 1.10 * inch, W - 2 * M, 16)
para(c, "<b>GBM coefficients</b>", M, H - 2.15 * inch, 5.4 * inch, 0.4 * inch, BODY)
formula(c, "|μs−μr| ≤ |μ||s−r|,     |σs−σr| ≤ |σ||s−r|", M, H - 2.55 * inch, 5.4 * inch, 17)
para(c, "Both drift and diffusion are globally Lipschitz.", M, H - 3.45 * inch, 5.4 * inch, 0.7 * inch, SMALL)
para(c, "<b>Non-affine coefficients</b>", 7.0 * inch, H - 2.15 * inch, 5.2 * inch, 0.4 * inch, BODY)
formula(c, "|g′(y)| ≤ (σmax−σmin)/4,     |d√(1+y²)/dy| ≤ 1", 7.0 * inch, H - 2.55 * inch, 5.2 * inch, 16)
para(c, "Bounded derivatives give global Lipschitz bounds and linear growth.", 7.0 * inch, H - 3.45 * inch, 5.2 * inch, 0.7 * inch, SMALL)
takeaway(c, "These regularity bounds support standard EM strong-convergence arguments.")
end_page(c)

# 7
frame(c, "Euler–Maruyama and Milstein updates", "Mathematical theory", 7)
y = H - 1.08 * inch
for txt in [
    "(10)  S<super>EM</super><sub>n+1</sub> = S<super>EM</super><sub>n</sub>(1 + μh + σΔW<sub>n</sub>)",
    "(11)  ∫∫ dW<sub>r</sub>dW<sub>s</sub> = ½[(ΔW<sub>n</sub>)² − h]",
    "(12)  S<super>Mil</super><sub>n+1</sub> = S<super>Mil</super><sub>n</sub>[1 + μh + σΔW<sub>n</sub> + ½σ²((ΔW<sub>n</sub>)²−h)]",
]:
    y -= formula(c, txt, 1.05 * inch, y, W - 2.1 * inch, 18) + 10
takeaway(c, "Milstein keeps the leading stochastic Taylor correction, giving strong order 1 instead of EM's 1/2. Both retain weak order 1.")
end_page(c)

# 8
frame(c, "Exact coupling and error definitions", "Mathematical theory", 8)
y = H - 1.08 * inch
for txt in [
    "(13)  S<super>exact</super><sub>n+1</sub> = S<super>exact</super><sub>n</sub> exp[(μ−½σ²)h + σΔW<sub>n</sub>]",
    "(14)  ê<sub>s</sub>(h) = M<super>−1</super> Σ |S<sub>N,m</sub>(h) − S<super>exact</super><sub>T,m</sub>|",
    "(15)  e<sub>w</sub>(h) = |E φ(S<sub>N</sub>(h)) − E φ(S<sub>T</sub>)|",
]:
    y -= formula(c, txt, 1.15 * inch, y, W - 2.3 * inch, 18) + 10
takeaway(c, "All methods use the same ΔWn; otherwise strong error would include differences between random paths.")
end_page(c)

# 9
frame(c, "Analytic weak bias for the mean", "Mathematical theory", 9)
y = H - 1.08 * inch
for txt in [
    "(16)  E[S<super>EM</super><sub>N</sub>] = E[S<super>Mil</super><sub>N</sub>] = S<sub>0</sub>(1+μh)<super>N</super>",
    "(17)  S<sub>0</sub>(1+μh)<super>T/h</super> = S<sub>0</sub> exp[μT − ½μ²Th + O(h²)]",
    "(18)  e<sub>w</sub>(h) = ½S<sub>0</sub>e<super>μT</super>μ²Th + O(h²)",
]:
    y -= formula(c, txt, 1.15 * inch, y, W - 2.3 * inch, 18) + 10
takeaway(c, "The deterministic bias oracle proves first-order weak behaviour for the mean and cannot be hidden by Monte Carlo noise.")
end_page(c)

# 10
frame(c, "Positivity is conditional in price space", "Mathematical theory", 10)
y = H - 1.08 * inch
for txt in [
    "(19)  1 + μh + σ√h Z<sub>n</sub> &gt; 0   is required for EM positivity",
    "(20)  p<sub>neg,EM</sub>(h) = Φ[−(1+μh)/(σ√h)] &gt; 0",
    "(21)  q(z) = ½σ²hz² + σ√h z + 1 + μh − ½σ²h",
    "(22)  q<sub>min</sub> = ½ + μh − ½σ²h",
]:
    y -= formula(c, txt, 1.20 * inch, y, W - 2.4 * inch, 16.5) + 2
takeaway(c, "EM can be negative for any finite h. Milstein is positive here, but can fail for other parameters when qmin ≤ 0. Log-price simulation stays positive.")
end_page(c)

# 11
frame(c, "Correlated non-affine EM", "Mathematical theory", 11)
y = H - 1.05 * inch
for txt in [
    "(23)  ΔW<sub>n</sub><super>(1)</super> = √h Z<sub>1,n</sub>       (24)  ΔW<sub>n</sub><super>(2)</super> = √h(ρZ<sub>1,n</sub> + √(1−ρ²)Z<sub>2,n</sub>)",
    "(25)  X<sub>n+1</sub> = X<sub>n</sub> + (μ−½g(Y<sub>n</sub>)²)h + g(Y<sub>n</sub>)ΔW<sub>n</sub><super>(1)</super>",
    "(26)  Y<sub>n+1</sub> = Y<sub>n</sub> + κ(θ−Y<sub>n</sub>)h + ξ√(1+Y<sub>n</sub>²)ΔW<sub>n</sub><super>(2)</super>",
    "(27)  S<sub>n+1</sub> = e<super>Xn+1</super> &gt; 0",
]:
    y -= formula(c, txt, 0.95 * inch, y, W - 1.9 * inch, 16) + 2
takeaway(c, "The construction gives variance h in both increments and correlation ρ. A scalar Milstein formula would omit required cross terms.")
end_page(c)

# 12
frame(c, "Nested reference and Monte Carlo uncertainty", "Mathematical theory", 12)
formula(c, "(28)  ΔW<sub>n,coarse</sub><super>(i)</super> = Σ<sub>j=0</sub><super>K−1</super> ΔW<sub>Kn+j,ref</sub><super>(i)</super>,   i=1,2", 1.1 * inch, H - 1.15 * inch, W - 2.2 * inch, 19)
formula(c, "(29)  D̄ ± 1.96 s<sub>D</sub>/√M,     s<sub>D</sub>² = (M−1)<super>−1</super>Σ(D<sub>m</sub>−D̄)²", 1.1 * inch, H - 2.25 * inch, W - 2.2 * inch, 19)
bullets(c, [
    "Equation (28) couples every grid to the same Brownian path.",
    "Equation (29) measures uncertainty in a Monte Carlo mean.",
    "Regression fit bands measure uncertainty around a fitted log–log line.",
], 1.3 * inch, H - 3.45 * inch, W - 2.6 * inch, font=18, leading=23, gap=9)
takeaway(c, "The 2048-step path is a numerical reference, not an exact solution.")
end_page(c)

# 13
frame(c, "Coupled algorithms for GBM", "Algorithm implementation", 13)
formula(c, "Z ~ N(0,1),     ΔW = √h Z", M, H - 1.20 * inch, 6.1 * inch, 22)
bullets(c, [
    "Generate one increment per path and time step.",
    "Send the same array to exact, EM, and Milstein updates.",
    "Store paired terminal differences.",
    "Fit log e(h) = log C + p log h.",
], M, H - 2.1 * inch, 6.1 * inch, font=17, leading=22, gap=8)
para(c, "<b>One random stream</b><br/><font color='#5E6B73'>↓</font><br/>Exact, EM, Milstein<br/><font color='#5E6B73'>↓</font><br/><b>Coupled terminal errors</b>", 8.0 * inch, H - 1.55 * inch, 3.8 * inch, 2.5 * inch, ParagraphStyle("flow", parent=CENTER, fontSize=22, leading=29, textColor=NAVY))
para(c, "<font color='#E07A5F'><b>Separate random draws would not estimate pathwise strong error.</b></font>", 7.6 * inch, H - 4.75 * inch, 4.5 * inch, 0.8 * inch, SMALL)
end_page(c)

# 14
frame(c, "Non-affine nested-grid algorithm", "Algorithm implementation", 14)
bullets(c, [
    "Generate finest-grid Z1, Z2 and construct correlated increments.",
    "Evaluate logistic volatility with stable positive/negative branches.",
    "Integrate X = log S and Y on the reference grid.",
    "Sum fine increments into every coarse grid.",
    "Compare coupled terminal values in memory-safe batches.",
], M, H - 1.25 * inch, 7.2 * inch, font=16, leading=21, gap=7)
formula(c, "8192  →  4096  →  2048  →  {16, 32, 64, 128, 256}", M, H - 4.55 * inch, 7.2 * inch, 17)
para(c, "<b>Reliability choices</b><br/><br/>Fixed seeds<br/>Shared Brownian paths<br/>Stable logistic evaluation<br/>Positive S = exp(X)<br/>Reference refinement", 8.4 * inch, H - 1.35 * inch, 3.7 * inch, 3.2 * inch, BODY)
takeaway(c, "Formula to code means preserving the probability structure, not only translating algebra.")
end_page(c)

# 15
frame(c, "B1. Fit bands and Monte Carlo intervals", "Visualization and report", 15)
image_contain(c, FIG / "fig01_gbm_convergence.png", M, 1.00 * inch, 7.25 * inch, 4.75 * inch)
para(c, "<b>Two uncertainty objects</b>", 8.25 * inch, H - 1.25 * inch, 4.1 * inch, 0.4 * inch, BODY)
bullets(c, [
    "Monte Carlo interval: uncertainty in a sample mean at one grid.",
    "Fit band: uncertainty around the regression line across grids.",
], 8.25 * inch, H - 1.78 * inch, 4.1 * inch, font=15, leading=20, gap=8)
formula(c, "log e(h) = α + p log h", 8.25 * inch, H - 3.25 * inch, 4.1 * inch, 17)
para(c, "Reference lines show theoretical scaling; they are not fitted data.<br/><br/><b>Observation floor:</b> when signal and sampling noise are comparable, a weak slope becomes unreliable.", 8.25 * inch, H - 4.25 * inch, 4.1 * inch, 1.5 * inch, SMALL)
end_page(c)

# 16
frame(c, "B2. Positivity algebra and the observation limit", "Visualization and report", 16)
image_contain(c, FIG / "fig03_gbm_positivity.png", M, 1.05 * inch, 7.1 * inch, 4.65 * inch)
para(c, "EM fails when<br/><b>1 + μh + σ√h Z ≤ 0</b>", 8.1 * inch, H - 1.35 * inch, 4.2 * inch, 0.8 * inch, BODY)
formula(c, "p̂ = 0 in M trials   ⇏   p = 0", 8.1 * inch, H - 2.35 * inch, 4.2 * inch, 18)
para(c, "At h=1, the observed EM failure rate is <b>0.435%</b>; at h=1/2, it is <b>0.034%</b>.<br/><br/><font color='#E07A5F'><b>“Not observed” means below the experiment's resolution, not impossible.</b></font>", 8.1 * inch, H - 3.45 * inch, 4.2 * inch, 1.6 * inch, SMALL)
end_page(c)

# 17
frame(c, "B3. Nested grids preserve the Brownian path", "Visualization and report", 17)
image_contain(c, FIG / "fig06_reference_sensitivity.png", M, 1.00 * inch, 7.35 * inch, 4.8 * inch)
para(c, "Fine increments are generated once and summed into coarse increments.", 8.25 * inch, H - 1.35 * inch, 4.0 * inch, 0.8 * inch, SMALL)
formula(c, "ΔWc = Σ ΔWf,j", 8.25 * inch, H - 2.30 * inch, 4.0 * inch, 19)
para(c, "Adjacent-reference MAE decreases:<br/><br/><b>0.0575  →  0.0407</b><br/><br/>The empirical half-order trend persists across 2048, 4096, and 8192-step references.", 8.25 * inch, H - 3.35 * inch, 4.0 * inch, 1.8 * inch, SMALL)
end_page(c)

# 18
frame(c, "B4. Matched accuracy needs a declared cost", "Visualization and report", 18)
image_contain(c, FIG / "fig07_gbm_cost_accuracy.png", M, 0.95 * inch, 7.15 * inch, 4.85 * inch)
para(c, "Target terminal MAE: <b>0.85 price units</b>", 8.05 * inch, H - 1.35 * inch, 4.2 * inch, 0.6 * inch, BODY)
bullets(c, ["EM first passes at N=128.", "Milstein first passes at N=2.", "Step-count ratio: 64:1."], 8.05 * inch, H - 2.05 * inch, 4.2 * inch, font=16, leading=21, gap=7)
para(c, "<font color='#E07A5F'><b>This is not a 64-fold wall-clock speedup.</b></font><br/><br/>Excluded: setup, plotting, file I/O, allocation, hardware effects, and extra Milstein arithmetic.", 8.05 * inch, H - 4.25 * inch, 4.2 * inch, 1.5 * inch, SMALL)
end_page(c)

# 19
frame(c, "B5. Convergence evidence at a glance", "Visualization and report", 19)
table(c, [
    ["Quantity", "Predicted", "Measured", "Interpretation"],
    ["EM strong order", "1/2", "0.4899 ± 0.0026", "consistent"],
    ["Milstein strong order", "1", "0.9099 ± 0.0167", "approaches one"],
    ["GBM mean weak order", "1", "0.9982 ± 0.0004", "analytic bias oracle"],
    ["Non-affine strong trend", "1/2", "0.5111 ± 0.0047", "numerical reference"],
], M, H - 1.18 * inch, [3.15 * inch, 1.6 * inch, 2.7 * inch, 3.5 * inch], font=13)
para(c, "<b>Log–log reference lines</b><br/>A line of slope 1/2 or 1 shows predicted scaling and helps identify the asymptotic range.", M, H - 4.45 * inch, 5.6 * inch, 1.2 * inch, SMALL)
para(c, "<b>Observation lower limit</b><br/>Call-payoff bias intervals include zero, so the project reports no non-affine weak slope.", 7.0 * inch, H - 4.45 * inch, 5.2 * inch, 1.2 * inch, SMALL)
end_page(c)

# 20
frame(c, "B6. Reproducible visual design and viva cues", "Visualization and report", 20)
para(c, "<b>Figure reproducibility</b>", M, H - 1.25 * inch, 5.8 * inch, 0.4 * inch, BODY)
bullets(c, [
    "Fixed seed and fixed output names.", "Units on every axis.", "One script regenerates all figures.",
    "Colorblind-safe blue, orange, teal, and grey palette.", "Captions state evidence and limitation.",
], M, H - 1.75 * inch, 5.8 * inch, font=16, leading=21, gap=6)
para(c, "<b>Preset questions</b>", 7.05 * inch, H - 1.25 * inch, 5.25 * inch, 0.4 * inch, BODY)
bullets(c, [
    "Why do fit bands differ from Monte Carlo intervals?", "Why use log scales and reference lines?",
    "Why does zero observed failures not imply zero probability?", "Can the 64:1 ratio be called a speedup?",
    "Why is 2048 steps not exact?",
], 7.05 * inch, H - 1.75 * inch, 5.25 * inch, font=16, leading=21, gap=6)
end_page(c)

VERSION_NOTE = "Archived environment: Python 3.9.6 on macOS 26.6 arm64. README versions NumPy 2.0.2 and Matplotlib 3.9.4 were not re-tested during slide preparation."

# 21
frame(c, "Testing and validation", "Testing and validation", 21, VERSION_NOTE)
for x, title, body in [
    (M, "Exact GBM benchmark", "Pathwise transition, moments, and terminal law provide independent oracles."),
    (4.55 * inch, "Numerical reference", "The non-affine model uses coupled fine-grid EM and refinement checks."),
    (8.55 * inch, "Fixed seed", "Every reported number and figure can be regenerated."),
]:
    para(c, f"<font color='#2A6F97'><b>{title}</b></font>", x, H - 1.65 * inch, 3.45 * inch, 0.9 * inch, ParagraphStyle("k", parent=BODY, fontSize=22, leading=27))
    para(c, body, x, H - 2.75 * inch, 3.45 * inch, 1.4 * inch, SMALL)
takeaway(c, "Checks cover convergence behaviour, Brownian increments, terminal validity, and reproducibility.", y=1.00 * inch)
end_page(c)

# 22
frame(c, "GBM convergence checks", "Testing and validation", 22, VERSION_NOTE)
image_contain(c, FIG / "fig01_gbm_convergence.png", M, 1.00 * inch, 7.2 * inch, 4.75 * inch)
para(c, "<b>Strong order</b><br/>EM: 0.4899 ± 0.0026<br/>Milstein: 0.9099 ± 0.0167<br/><br/><b>Weak bias</b><br/>GBM mean: 0.9982 ± 0.0004", 8.1 * inch, H - 1.35 * inch, 4.2 * inch, 2.5 * inch, ParagraphStyle("big", parent=BODY, fontSize=20, leading=27))
para(c, "All three lie inside the code's predeclared acceptance bands. The measured Milstein slope approaches, but does not equal, one.", 8.1 * inch, H - 4.35 * inch, 4.2 * inch, 1.3 * inch, SMALL)
end_page(c)

# 23
frame(c, "Non-affine model checks", "Testing and validation", 23, VERSION_NOTE)
image_contain(c, FIG / "fig04_nonaffine_convergence.png", M, 1.00 * inch, 7.2 * inch, 4.75 * inch)
para(c, "<b>Strong slope</b><br/>0.5111 ± 0.0047<br/><br/><b>Increment correlation</b><br/>observed −0.70185, target −0.7<br/><br/><b>Terminal validity</b><br/>all states finite<br/>all prices positive", 8.1 * inch, H - 1.2 * inch, 4.2 * inch, 3.4 * inch, ParagraphStyle("metric", parent=SMALL, fontSize=17, leading=23))
para(c, "The reference remains numerical; the experiment makes no non-affine weak-order claim.", 8.1 * inch, H - 4.95 * inch, 4.2 * inch, 0.8 * inch, SMALL)
end_page(c)

# 24
frame(c, "Numerical reproducibility", "Testing and validation", 24, VERSION_NOTE)
image_contain(c, FIG / "fig06_reference_sensitivity.png", M, 1.00 * inch, 7.2 * inch, 4.75 * inch)
para(c, "<font color='#2A9D8F'><b>10/10 checks passed</b></font><br/>OVERALL: PASS", 8.1 * inch, H - 1.2 * inch, 4.2 * inch, 1.0 * inch, ParagraphStyle("pass", parent=BODY, fontSize=23, leading=29))
para(c, "Adjacent-reference difference:<br/><b>0.0575 → 0.0407</b><br/><br/>Maximum slope change: <b>0.0117</b><br/><br/>Fixed seed: <b>20260918</b><br/>Fixed commit: <b>ef18807</b>", 8.1 * inch, H - 2.45 * inch, 4.2 * inch, 2.5 * inch, SMALL)
end_page(c)

# 25
frame(c, "Main results", "Conclusion", 25)
table(c, [
    ["Result", "Theory / target", "Evidence"],
    ["EM strong order", "1/2", "0.4899 ± 0.0026"],
    ["Milstein strong order", "1", "0.9099 ± 0.0167"],
    ["GBM mean weak order", "1", "0.9982 ± 0.0004"],
    ["Non-affine strong trend", "1/2", "0.5111 ± 0.0047"],
    ["Matched MAE ≤ 0.85", "fewer steps", "EM 128, Milstein 2"],
    ["Validation suite", "all pass", "10/10 PASS"],
], 1.15 * inch, H - 1.25 * inch, [4.15 * inch, 2.5 * inch, 3.65 * inch], font=14)
takeaway(c, "Reliable conclusions came from coupled paths, independent oracles, explicit uncertainty, and stated limits.")
end_page(c)

# 26
frame(c, "Limitations", "Conclusion", 26)
bullets(c, [
    "<b>Numerical reference.</b> The 2048-step non-affine solution is not exact; refinement checks quantify but do not remove reference bias.",
    "<b>Weak convergence.</b> Every call-payoff bias interval contains zero, so the non-affine weak rate remains unresolved.",
    "<b>Cost definition.</b> The 64:1 ratio counts time steps, not wall-clock time or arithmetic cost.",
    "<b>Regression evidence.</b> Fit standard errors do not include every mesh-selection or model-selection uncertainty.",
    "<b>Model and extreme-path risk.</b> Numerical convergence does not validate market realism, and exp(X) may overflow under longer horizons or extreme parameters.",
], M, H - 1.18 * inch, W - 2 * M, font=16, leading=21, gap=8)
end_page(c)

# 27
c.setFillColor(colors.white); c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(NAVY); c.setFont("DeckBold", 44); c.drawCentredString(W / 2, H * 0.60, "Thank you")
c.setFont("Deck", 27); c.drawCentredString(W / 2, H * 0.47, "Questions?")
c.setStrokeColor(BLUE); c.setLineWidth(2); c.line(W * 0.34, H * 0.39, W * 0.66, H * 0.39)
c.setFillColor(MUTED); c.setFont("Deck", 13); c.drawCentredString(W / 2, H * 0.30, "Team H   •   Reliable Numerical Simulation of Financial SDEs")
footer(c, "Conclusion", 27); end_page(c)

c.save()
print(OUT)
