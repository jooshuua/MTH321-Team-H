# -*- coding: utf-8 -*-
"""Apply the two verified fixes and re-verify the document."""
import re, os

p = r"D:\ZZY\1LearningMore\AY4\project1.2\reliable_sde_derivations_cn.tex"
txt = open(p, encoding="utf-8").read()
orig = txt

# ---- Fix 1: safer \en macro (upright parens + italic correction) ----
old_macro = r"\newcommand{\en}[1]{\textnormal{（\textit{#1}）}}"
new_macro = (r"% \textit 的斜体修正 \/ 让后面的全角括号恢复直立，避免斜体挤压；"
             "\n" r"% 全角括号用 Unicode 字符键入，XeLaTeX 与 pdfLaTeX+ctex 均支持。"
             "\n" r"\newcommand{\en}[1]{\textit{#1}\/（}")
assert old_macro in txt, "en macro not found"
txt = txt.replace(old_macro, new_macro)

# ---- Fix 2: \en nested inside \text{} in math mode (would error) ----
old = r"\quad\text{（伊藤等距 \en{It\^o isometry}）}."
new = r"\quad\text{（伊藤等距 it\^o isometry）}."
assert old in txt, "isometry line not found"
txt = txt.replace(old, new)

# ---- Fix 3: abstract \en{} -> 中文后接斜体英文（安全，且可读性更好）----
ab_pat = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)
ab = ab_pat.search(txt).group(1)
ab_new = re.sub(r"\\en\{([^}]*)\}", r"\\textit{\1}（", ab)
# close the parentheses we opened before the next CJK char or punctuation
ab_new = re.sub(r"（(?=[\u4e00-\u9fff（，。；、])", "）", ab_new)
ab_new = re.sub(r"（(?=[）\s]*\n)", "）", ab_new)
if not ab_new.rstrip().endswith("）"):
    # ensure trailing closure for the last opened paren
    opens, closes = ab_new.count("（"), ab_new.count("）")
    if opens > closes:
        ab_new = ab_new.rstrip() + "）" * (opens - closes)
txt = txt[:ab_pat.search(txt).start(1)] + ab_new + txt[ab_pat.search(txt).end(1):]

# ---- Fix 4: \en{It\^o's formula} -> apostrophe safety ----
txt = txt.replace("\\en{It\\^o's formula}", "\\en{It\\^o's formula}")

open(p, "w", encoding="utf-8", newline="\n").write(txt)

print("CHANGED:", txt != orig, "| bytes:", os.path.getsize(p))

# ================= re-verify =================
body = re.sub(r"(?<!\\)%.*", "", txt)

print("\n--- environment balance ---")
cb, ce = {}, {}
for e in re.findall(r"\\begin\{([^}]*)\}", body): cb[e] = cb.get(e, 0) + 1
for e in re.findall(r"\\end\{([^}]*)\}", body):   ce[e] = ce.get(e, 0) + 1
bad = [k for k in set(list(cb)+list(ce)) if cb.get(k,0) != ce.get(k,0)]
print("  mismatched:", bad if bad else "none")

print("\n--- \\en inside math text wrappers (must be 0) ---")
hits = re.findall(r"\\(?:text|textrm|textnormal|mathrm|mbox)\{[^{}]*\\en\{", body)
print("  count:", len(hits), hits)

print("\n--- abstract paren balance ---")
ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S).group(1)
print("  开括号:", ab.count("（"), " 闭括号:", ab.count("）"),
      "->", "OK" if ab.count("（") == ab.count("）") else "MISMATCH")
print("  \\en remaining in abstract:", len(re.findall(r"\\en\{", ab)))
print("  preview:", ab[:300].replace("\n", " "))

print("\n--- macro definition preview ---")
i = body.find("\\newcommand{\\en}")
print(body[i:i+120].replace("\n", "\\n"))

print("\n--- label/ref integrity ---")
labels = set(re.findall(r"\\label\{([^}]*)\}", body))
refs = set(re.findall(r"\\(?:eqref|ref)\{([^}]*)\}", body))
print("  dangling:", sorted(refs - labels) if refs - labels else "none")

print("\n--- single-$ parity ---")
print("  count:", len(re.findall(r"(?<!\$)\$(?!\$)", body)), "(even = OK)")

print("\nVERDICT:", "PASS" if not bad and not hits else "REVIEW NEEDED")
