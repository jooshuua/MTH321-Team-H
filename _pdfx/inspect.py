import re, sys, zlib

data = open(r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf","rb").read()
print("size", len(data))
print("head", data[:40])
print("n obj", len(re.findall(rb"\d+\s+\d+\s+obj", data)))
print("n stream", len(re.findall(rb"stream\r?\n", data)))
print("filters", set(re.findall(rb"/Filter\s*/(\w+)", data)))
print("fonts", set(re.findall(rb"/Subtype\s*/(\w+)", data)))
print("ToUnicode count", len(re.findall(rb"/ToUnicode", data)))
# check FlateDecode first stream
m = re.search(rb"stream\r?\n", data)
i = m.end()
j = data.find(b"endstream", i)
raw = data[i:j]
try:
    out = zlib.decompress(raw)
    print("decompressed ok", len(out))
    print(out[:600])
except Exception as e:
    print("fail", e)
