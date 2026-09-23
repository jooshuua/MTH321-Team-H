import re, zlib, pickle, sys, collections

d = pickle.load(open(r"D:\ZZY\1LearningMore\AY4\project1.2\_pdfx\objs.pkl","rb"))
bodies, xref = d["bodies"], d["xref"]
data = open(r"D:\ZZY\1LearningMore\AY4\project1.2\Reliable_Numerical_Simulation_of_Financial_SDEs.pdf","rb").read()

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

# resolve indirect references
def deref(tok):
    m = re.match(rb"^(\d+)\s+0\s+R$", tok.strip())
    if m: return int(m.group(1))
    return None

# ---- pages in order
pages = []
for num, b in bodies.items():
    if re.search(rb"/Type\s*/Page\b", b) and not re.search(rb"/Type\s*/Pages", b):
        pages.append(num)

def page_index(num):
    b = bodies[num]
    # find /StructParents or use order in Pages kids
    return num

# build order from Pages tree
kids_order = []
def walk(num, depth=0):
    b = bodies.get(num, b"")
    if re.search(rb"/Type\s*/Page\b", b) and not re.search(rb"/Type\s*/Pages", b):
        kids_order.append(num); return
    km = re.search(rb"/Kids\s*\[([^\]]*)\]", b, re.S)
    if km:
        for tok in re.findall(rb"(\d+)\s+0\s+R", km.group(1)):
            walk(int(tok), depth+1)

root = None
for num, b in bodies.items():
    if b"/Type /Catalog" in b or b"/Type/Catalog" in b:
        root = num
print("catalog:", root, bodies.get(root, b"")[:200])
pg = re.search(rb"/Pages\s+(\d+)\s+0\s+R", bodies.get(root, b""))
if pg: walk(int(pg.group(1)))
print("pages in order:", len(kids_order), kids_order[:35])

pickle.dump(kids_order, open(r"D:\ZZY\1LearningMore\AY4\project1.2\_pdfx\pages.pkl","wb"))
