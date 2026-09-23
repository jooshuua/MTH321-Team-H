# -*- coding: utf-8 -*-
import re
p = r"D:\ZZY\1LearningMore\AY4\project1.2\reliable_sde_derivations_cn.tex"
txt = open(p, encoding="utf-8").read()

print("=== \\en nested inside math-mode text wrappers ===")
pat = re.compile(r"\\(?:text|textrm|textnormal|mathrm|mbox|operatorname)\{[^{}]*(?:\\en\{[^}]*\}|\\textit\{[^}]*\})")
found = 0
for m in pat.finditer(txt):
    found += 1
    s = max(0, m.start()-80)
    print("\n[%d] %s" % (found, txt[s:m.end()+40].replace("\n", "\\n")))
print("\ntotal:", found)

print("\n=== all \\textit{...} inside math text wrappers ===")
for m in re.finditer(r"\\(?:text|textrm|textnormal|mbox)\{[^{}]*\\textit\{[^}]*\}", txt):
    print("  ", m.group(0))

print("\n=== abstract block \\en lines ===")
ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", txt, re.S).group(1)
print(ab[:900])
