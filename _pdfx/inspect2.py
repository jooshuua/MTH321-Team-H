import re, zlib, sys, collections

path = r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf"
data = open(path, "rb").read()

print("Subtype values:", collections.Counter(re.findall(rb"/Subtype\s*/([A-Za-z0-9]+)", data)))
print("Type values:", collections.Counter(re.findall(rb"/Type\s*/([A-Za-z0-9]+)", data)))
print("has ObjStm:", b"/ObjStm" in data, "XRefStm:", b"/XRef" in data)

# Expand object streams
ostreams = []
for m in re.finditer(rb"stream\r?\n", data):
    i = m.end()
    j = data.find(b"endstream", i)
    raw = data[i:j]
    try:
        out = zlib.decompress(raw)
    except Exception:
        try:
            out = zlib.decompressobj().decompress(raw)
        except Exception:
            continue
    if b"/Type/ObjStm" in out or b"/Type /ObjStm" in out or re.match(rb"\s*\d+\s+\d+\s", out) and b"endobj" not in out[:200]:
        ostreams.append(out)

print("candidate objstm-like streams:", len(ostreams))

# Find the catalog / pages to understand
for out in ostreams:
    if b"/Pages" in out or b"/Catalog" in out:
        print("---")
        print(out[:1500])
        break
