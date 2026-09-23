# -*- coding: utf-8 -*-
import re
p = r"D:\ZZY\1LearningMore\AY4\project1.2\reliable_sde_derivations_cn.tex"
txt = open(p, encoding="utf-8").read()
body = re.sub(r"(?<!\\)%.*", "", txt)

print("=== bare qquad / Var / frac occurrences ===")
for pat in [r"(?<!\\)qquad", r"(?<!\\)Var\b", r"(?<!\\)frac\{"]:
    for m in re.finditer(pat, body):
        s = max(0, m.start()-90); e = min(len(body), m.end()+90)
        print("\n[%s]" % pat)
        print("   ..." + body[s:e].replace("\n", "\\n") + "...")

print("\n=== \\en usage inside title/abstract ===")
ti = re.search(r"\\title\{(.*?)\n\}", body, re.S)
ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
for nm, blk in [("title", ti.group(1) if ti else ""), ("abstract", ab.group(1) if ab else "")]:
    hits = re.findall(r"\\en\{[^}]*\}", blk)
    print("%s: %d \\en uses" % (nm, len(hits)))
    for h in hits[:3]:
        print("    ", h)

print("\n=== contexts of every \\en (check for fragile nesting) ===")
risky = []
for m in re.finditer(r"\\en\{", body):
    # find enclosing line
    ls = body.rfind("\n", 0, m.start()) + 1
    le = body.find("\n", m.end())
    line = body[ls:le]
    if "\\parbox" in line or "\\colorbox" in line or line.strip().startswith("%"):
        risky.append(line.strip()[:100])
print("risky \\en lines:", risky if risky else "none")

print("\n=== custom-macro nesting: \\why / \\key bodies containing \\colorbox or \\parbox ===")
for mac in ["\\why{", "\\key{"]:
    i = 0
    while True:
        i = body.find(mac, i)
        if i < 0: break
        # brace match
        j = i + len(mac) - 1
        depth = 0; k = j
        while k < len(body):
            if body[k] == "{": depth += 1
            elif body[k] == "}":
                depth -= 1
                if depth == 0: break
            k += 1
        arg = body[j:k+1]
        if "\\colorbox" in arg or "\\parbox" in arg or "\\why" in arg[1:] or "\\key" in arg[1:]:
            print("  NESTING RISK in", mac, "->", arg[:120].replace("\n", " "))
        i = k + 1
print("  (empty above = OK)")

print("\n=== display math sanity ===")
print("  \\[ or \\] display delims:", body.count("\\["), body.count("\\]"))
print("  \\begin{equation} block count:", len(re.findall(r"\\begin\{equation\}", body)))
print("  align with & column count consistency:")
for m in re.finditer(r"\\begin\{align\}(.*?)\\end\{align\}", body, re.S):
    rows = [r for r in m.group(1).split("\\\\") if r.strip() and not r.strip().startswith("\\notag") and "&" in r]
    counts = [r.count("&") for r in rows]
    if len(set(counts)) > 1:
        print("    WARN differing & counts:", counts, "->", m.group(1)[:80].replace("\n"," "))

print("\n=== undefined-command risk scan (macros used vs defined) ===")
defined = set(re.findall(r"\\newcommand\{\\([A-Za-z@]+)\}", body))
print("  user macros defined:", sorted(defined))
print("\nDONE")
