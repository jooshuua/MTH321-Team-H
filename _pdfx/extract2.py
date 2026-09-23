import re, zlib, collections

path = r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf"
data = open(path, "rb").read()

# find XRef streams
for m in re.finditer(rb"(\d+)\s+0\s+obj", data):
    num = int(m.group(1))
    start = m.end()
    end = data.find(b"endobj", start)
    body = data[start:end]
    sm = re.search(rb"stream\r?\n", body)
    if not sm: continue
    head = body[:sm.start()]
    if b"/XRef" in head:
        s = sm.end(); e = body.find(b"endstream", s)
        try:
            out = zlib.decompress(body[s:e])
        except Exception as ex:
            print(num, "decompress fail", ex); continue
        print("=== XRef obj", num)
        print(head[:400])
        print("len decoded", len(out), "first 80 bytes:", out[:80].hex())
        print("Index:", re.search(rb"/Index\s*\[[^\]]*\]", head).group(0) if re.search(rb"/Index\s*\[[^\]]*\]", head) else None)
        print("Size:", re.search(rb"/Size\s*(\d+)", head).group(1) if re.search(rb"/Size\s*(\d+)", head) else None)
        print("W:", re.search(rb"/W\s*\[[^\]]*\]", head).group(0) if re.search(rb"/W\s*\[[^\]]*\]", head) else None)
