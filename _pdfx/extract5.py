import re, zlib, pickle, sys, collections

BASE = r"D:\ZZY\1LearningMore\AY4\project1.2"
d = pickle.load(open(BASE + r"\_pdfx\objs.pkl","rb"))
bodies = d["bodies"]
pages = pickle.load(open(BASE + r"\_pdfx\pages.pkl","rb"))

def get_stream_raw(body):
    sm = re.search(rb"stream\r?\n", body)
    if not sm: return None, body
    s = sm.end(); e = body.find(b"endstream", s)
    raw = body[s:e]
    if raw.endswith(b"\r\n"): raw = raw[:-2]
    elif raw.endswith(b"\n") or raw.endswith(b"\r"): raw = raw[:-1]
    return raw, body[:sm.start()]

def decode(body):
    raw, head = get_stream_raw(body)
    if raw is None: return None, head
    if b"/FlateDecode" in head:
        try: out = zlib.decompress(raw)
        except Exception:
            try: out = zlib.decompressobj().decompress(raw)
            except Exception: return None, head
    else:
        out = raw
    return out, head

cmap_cache = {}
def get_cmap(num):
    if num in cmap_cache: return cmap_cache[num]
    b = bodies.get(num)
    if b is None:
        cmap_cache[num] = {}; return {}
    out, head = decode(b)
    mp = {}
    if out:
        txt = out
        for m in re.finditer(rb"beginbfchar(.*?)endbfchar", txt, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", m.group(1)):
                code = int(src, 16)
                s = bytes.fromhex(dst.decode()).decode("utf-16-be", "replace")
                mp[code] = s
        for m in re.finditer(rb"beginbfrange(.*?)endbfrange", txt, re.S):
            body = m.group(1)
            for lo, hi, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", body):
                a, b2 = int(lo,16), int(hi,16)
                base = int(dst,16)
                for k in range(a, b2+1):
                    mp[k] = chr(base + (k-a))
            for lo, hi, arr in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", body, re.S):
                a = int(lo,16)
                items = re.findall(rb"<([0-9A-Fa-f]+)>", arr)
                for i, it in enumerate(items):
                    mp[a+i] = bytes.fromhex(it.decode()).decode("utf-16-be","replace")
    cmap_cache[num] = mp
    return mp

# per-page text
class S(bytes):
    pass

def parse_content(content, fonts):
    out = []
    toks = tokenize(content)
    cur = None
    stack = []
    for t in toks:
        if t == b"Tf":
            if len(stack) >= 2:
                nm = stack[-2]
                if isinstance(nm, bytes) and not isinstance(nm, S):
                    cur = fonts.get(nm)
        if t == b"Tj" or t == b"'" or t == b'"':
            s = stack[-1] if stack else None
            if isinstance(s, S):
                out.append(decode_str(bytes(s), cur))
        if t == b"TJ":
            arr = stack[-1] if stack else None
            if isinstance(arr, list):
                buf = []
                for el in arr:
                    if isinstance(el, S):
                        buf.append(decode_str(bytes(el), cur))
                    elif isinstance(el, (int, float)):
                        if el < -150: buf.append(" ")
                    elif isinstance(el, list):
                        for e2 in el:
                            if isinstance(e2, S):
                                buf.append(decode_str(bytes(e2), cur))
                out.append("".join(buf))
        if t in (b"Td", b"TD", b"T*", b"ET"):
            out.append("\n")
        if t == "]":
            arr = []
            while stack and stack[-1] != "[":
                arr.insert(0, stack.pop())
            if stack: stack.pop()
            stack.append(arr)
            continue
        if t == "[":
            stack.append(t); continue
        stack.append(t)
    return out

def tokenize(c):
    toks = []
    i = 0
    n = len(c)
    while i < n:
        ch = c[i:i+1]
        if ch in b" \t\r\n":
            i += 1; continue
        if ch == b"(":
            depth = 1; j = i+1; buf = bytearray()
            while j < n and depth:
                if c[j:j+1] == b"\\":
                    buf += c[j:j+2]; j += 2; continue
                if c[j:j+1] == b"(": depth += 1
                if c[j:j+1] == b")":
                    depth -= 1
                    if depth == 0: break
                buf += c[j:j+1]; j += 1
            toks.append(S(unescape(bytes(buf)))); i = j+1; continue
        if ch == b"<":
            j = c.find(b">", i)
            hexs = c[i+1:j].replace(b" ", b"").replace(b"\n", b"")
            if len(hexs) % 2: hexs += b"0"
            toks.append(S(bytes.fromhex(hexs.decode()))); i = j+1; continue
        if ch == b"[":
            toks.append("["); i += 1; continue
        if ch == b"]":
            toks.append("]"); i += 1; continue
        if ch == b"/":
            j = i+1
            while j < n and c[j:j+1] not in b" \t\r\n/[]<>()": j += 1
            toks.append(c[i:j]); i = j; continue
        j = i
        while j < n and c[j:j+1] not in b" \t\r\n/[]<>()": j += 1
        w = c[i:j]
        try:
            toks.append(float(w))
        except Exception:
            toks.append(w)
        i = j
    return toks

def unescape(b):
    out = bytearray(); i = 0
    while i < len(b):
        ch = b[i:i+1]
        if ch == b"\\" and i+1 < len(b):
            nx = b[i+1:i+2]
            mp = {b"n":10, b"r":13, b"t":9, b"b":8, b"f":12, b"(":40, b")":41, b"\\":92}
            if nx in mp: out.append(mp[nx]); i += 2; continue
            m = re.match(rb"[0-7]{1,3}", b[i+1:i+4])
            if m: out.append(int(m.group(0), 8) & 0xFF); i += 1 + len(m.group(0)); continue
            i += 2; continue
        out.append(b[i]); i += 1
    return bytes(out)

def decode_str(s, cmap):
    if not cmap:
        return s.decode("latin-1", "replace")
    two = max(cmap.keys()) > 255
    res = []
    if two:
        for k in range(0, len(s)-1, 2):
            code = (s[k] << 8) | s[k+1]
            res.append(cmap.get(code, ""))
    else:
        for k in range(len(s)):
            res.append(cmap.get(s[k], chr(s[k]) if 32 <= s[k] < 127 else ""))
    return "".join(res)

pages_text = []
for pnum in pages:
    pb = bodies[pnum]
    # resources
    res = re.search(rb"/Resources\s+(\d+)\s+0\s+R", pb)
    resbody = bodies.get(int(res.group(1)), b"") if res else pb
    # fonts dict
    fonts = {}
    fd = re.search(rb"/Font\s*<<(.*?)>>", resbody, re.S)
    fdict = {}
    if fd:
        for nm, on in re.findall(rb"/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R", fd.group(1)):
            fdict[nm] = int(on)
    else:
        fdr = re.search(rb"/Font\s+(\d+)\s+0\s+R", resbody)
        if fdr:
            fb = bodies.get(int(fdr.group(1)), b"")
            for nm, on in re.findall(rb"/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R", fb):
                fdict[nm] = int(on)
    for nm, on in fdict.items():
        fb = bodies.get(on, b"")
        tu = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", fb)
        fonts[("/" + nm.decode()).encode()] = get_cmap(int(tu.group(1))) if tu else {}
    # contents
    cm = re.search(rb"/Contents\s+(\d+)\s+0\s+R", pb)
    cs = b""
    if cm:
        cs, _ = decode(bodies.get(int(cm.group(1)), b"")) or (b"", b"")
    cs = cs or b""
    txt = parse_content(cs, fonts)
    sys.stdout.write("\n\n========== PAGE %d (obj %d) ==========\n" % (len(pages_text)+1, pnum))
    sys.stdout.write("".join(txt))
    pages_text.append("".join(txt))

open(BASE + r"\_pdfx\pdf_text.txt","w",encoding="utf-8").write("".join(pages_text))
print("\n\nWROTE", sum(len(t) for t in pages_text), "chars")
