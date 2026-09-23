import re, zlib, sys, collections

PATH = r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf"
data = open(PATH, "rb").read()

SOF = re.compile(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\b")

def png_unpredict(raw, colors, columns, bpc=8):
    bpp = colors * bpc // 8
    rowlen = colors * columns * bpc // 8
    out = bytearray()
    prev = bytearray(rowlen)
    pos = 0
    while pos + 1 + rowlen <= len(raw):
        ft = raw[pos]; pos += 1
        row = bytearray(raw[pos:pos+rowlen]); pos += rowlen
        if ft == 0:
            pass
        elif ft == 1:
            for i in range(bpp, rowlen):
                row[i] = (row[i] + row[i-bpp]) & 0xFF
        elif ft == 2:
            for i in range(rowlen):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(rowlen):
                left = row[i-bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(rowlen):
                a = row[i-bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i-bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        out += row
        prev = row
    return bytes(out)

# gather all objects with their byte offsets (contains stream)
raw_objs = {}
for m in SOF.finditer(data):
    raw_objs[int(m.group(1))] = m.end()

print("raw objs found:", len(raw_objs), "max num", max(raw_objs))

def get_stream(body):
    sm = re.search(rb"stream\r?\n", body)
    if not sm:
        return None, body, None
    s = sm.end()
    e = body.find(b"endstream", s)
    raw = body[s:e]
    if raw.endswith(b"\r\n"): raw = raw[:-2]
    elif raw.endswith(b"\n") or raw.endswith(b"\r"): raw = raw[:-1]
    head = body[:sm.start()]
    return raw, head, sm.start()

def decode_stream(body):
    raw, head, _ = get_stream(body)
    if raw is None: return None, head
    if b"/FlateDecode" in head:
        try:
            out = zlib.decompress(raw)
        except Exception:
            try: out = zlib.decompressobj().decompress(raw)
            except Exception: return None, head
    else:
        out = raw
    dp = re.search(rb"/DecodeParms\s*<<([^>]*)>>", head)
    if dp and b"/Predictor" in dp.group(1):
        cols = int(re.search(rb"/Columns\s+(\d+)", dp.group(1)).group(1))
        colors = 1
        bpc = 8
        pred = int(re.search(rb"/Predictor\s+(\d+)", dp.group(1)).group(1))
        if pred >= 10:
            out = png_unpredict(out, colors, cols, bpc)
    return out, head

# Build xref map: objnum -> (type, offset_or_objstm, index)
xref = {}
for num, off in raw_objs.items():
    body = data[off: data.find(b"endobj", off)]
    if b"/Type /XRef" not in body and b"/Type/XRef" not in body:
        continue
    dec, head = decode_stream(body)
    if dec is None: continue
    W = [int(x) for x in re.search(rb"/W\s*\[([^\]]*)\]", head).group(1).split()]
    idx = re.search(rb"/Index\s*\[([^\]]*)\]", head)
    if idx:
        nums = [int(x) for x in idx.group(1).split()]
        ranges = list(zip(nums[0::2], nums[1::2]))
    else:
        size = int(re.search(rb"/Size\s+(\d+)", head).group(1))
        ranges = [(0, size)]
    wid = sum(W)
    pos = 0
    for start, cnt in ranges:
        for k in range(cnt):
            ent = dec[pos:pos+wid]; pos += wid
            if len(ent) < wid: break
            f = []
            p = 0
            for w in W:
                f.append(int.from_bytes(ent[p:p+w], "big") if w else None)
                p += w
            t = f[0] if f[0] is not None else 1
            onum = start + k
            if onum in xref: continue
            if t == 1:
                xref[onum] = ("n", f[1], f[2])
            elif t == 2:
                xref[onum] = ("o", f[1], f[2])
print("xref entries:", len(xref))

# object bodies
bodies = {}
for num, off in raw_objs.items():
    if xref.get(num, ("n", off, 0))[0] == "n":
        bodies[num] = data[off: data.find(b"endobj", off)]

# expand ObjStm
expanded = 0
for num in list(xref):
    ent = xref[num]
    if ent[0] == "o":
        stmnum, idx = ent[1], ent[2]
        if stmnum not in bodies:
            continue
        sd, head = decode_stream(bodies[stmnum])
        if sd is None: continue
        n = int(re.search(rb"/N\s+(\d+)", head).group(1))
        first = int(re.search(rb"/First\s+(\d+)", head).group(1))
        pairs = [int(x) for x in sd[:first].split()]
        offs = pairs[1::2]
        for k in range(n):
            onum = pairs[2*k]
            o = offs[k]
            nx = offs[k+1] if k+1 < n else len(sd) - first
            if onum in bodies: continue
            bodies[onum] = sd[first+o: first+nx]
            expanded += 1
print("bodies:", len(bodies), "expanded:", expanded)

import pickle
pickle.dump({"bodies": bodies, "xref": xref}, open(r"D:\ZZY\1LearningMore\AY4\project1.2\_pdfx\objs.pkl","wb"))

# font info
fonts = {n: b for n, b in bodies.items() if re.search(rb"/Type\s*/Font", b)}
print("fonts:", len(fonts))
for n, b in list(fonts.items())[:20]:
    print(n, b[:250])
