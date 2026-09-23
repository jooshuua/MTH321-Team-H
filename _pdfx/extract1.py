import re, zlib, collections, sys

path = r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf"
data = open(path, "rb").read()

objs = {}   # num -> bytes body (dictionary part)
streams = {}  # num -> decompressed stream bytes

# --- pass 1: raw top-level objects
for m in re.finditer(rb"(\d+)\s+(\d+)\s+obj\b", data):
    num = int(m.group(1))
    start = m.end()
    end = data.find(b"endobj", start)
    body = data[start:end]
    objs[num] = body
    sm = re.search(rb"stream\r?\n", body)
    if sm:
        s = sm.end()
        e = body.find(b"endstream", s)
        raw = body[s:e]
        try:
            streams[num] = zlib.decompress(raw)
        except Exception:
            pass

print("raw objects:", len(objs), "raw streams:", len(streams))

# --- pass 2: expand ObjStm
def expand_objstm(sd):
    hdr_end = sd.find(b">>")
    head = sd[:hdr_end+2]
    n = int(re.search(rb"/N\s+(\d+)", head).group(1))
    first = int(re.search(rb"/First\s+(\d+)", head).group(1))
    pairs = sd[hdr_end+2:first].split()
    nums = [int(x) for x in pairs]
    out = {}
    for k in range(n):
        onum = nums[2*k]
        off = nums[2*k+1]
        nxt = nums[2*k+3] if 2*k+3 < len(nums) else None
        seg = sd[first+off: first+nxt] if nxt is not None else sd[first+off:]
        out[onum] = seg
    return out

expanded = 0
for num, sd in list(streams.items()):
    head = sd[:sd.find(b">>")+2]
    if b"/ObjStm" in head:
        for onum, seg in expand_objstm(sd).items():
            if onum not in objs:
                objs[onum] = seg
                expanded += 1
print("expanded from ObjStm:", expanded, "total objects:", len(objs))

# --- fonts
fonts = {}
for num, body in objs.items():
    if re.search(rb"/Type\s*/Font", body):
        fonts[num] = body
print("fonts:", len(fonts))
for num, body in list(fonts.items())[:15]:
    print(num, body[:220])
