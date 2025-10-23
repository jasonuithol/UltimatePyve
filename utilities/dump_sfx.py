from pathlib import Path
import struct

def load_driver(path):
    return Path(path).read_bytes()

def get_index_table(buf, base=0x2C00, count=32):
    """Read `count` far pointers from index table at `base`."""
    table = []
    for i in range(count):
        off = base + i*4
        if off+4 > len(buf): break
        lo, hi = struct.unpack_from("<HH", buf, off)
        table.append((i, lo, hi))
    return table

def read_sequence(buf, ptr, max_len=64, terms=(0x00,0xFF)):
    seq = []
    j = ptr
    while j < len(buf) and len(seq) < max_len:
        b1 = buf[j]
        if b1 in terms: break
        if j+1 >= len(buf): break
        b2 = buf[j+1]
        seq.append((b1, b2))
        j += 2
    return seq

def scan_sequences(buf, start=0x2800, end=None):
    if end is None: end = len(buf)
    for i in range(start, end-4):
        seq = []
        j = i
        while j+1 < end:
            n, d = buf[j], buf[j+1]
            if n in (0x00,0xFF): break
            if d in (0x00,0xFF): break
            if n > 0x7F or d > 0xF0: break
            seq.append((n,d))
            j += 2
        if len(seq) >= 3:
            print(f"seq @0x{i:04X} len={len(seq)} {seq[:6]}...")

def dump_id(buf, idnum, base=0x2C00, load_base=0x1C20):

    table = get_index_table(buf, base, idnum+1)
    lo, hi = table[idnum][1], table[idnum][2]
#    ptr = lo  # offset within file
    linear = (hi << 4) + lo  # offset within file
    ptr = linear - load_base

    if ptr < 0x2000:
        print(f"# Skipping ptr={ptr}")

    seq = read_sequence(buf, ptr)
    print(f"ID {idnum:02X} @0x{ptr:04X} → {len(seq)} pairs")
    for note, dur in seq:
        print(f"  note={note:02X} dur={dur}")
    print("---")

def guess_load_base(buf, base=0x2C00, entries=32):
    table = get_index_table(buf, base, entries)
    best = None
    for load_base in range(0x0800, 0x3000, 0x10):  # scan plausible ranges
        hits = 0
        for _, lo, hi in table:
            linear = (hi << 4) + lo
            ptr = linear - load_base
            if 0 <= ptr < len(buf) and 0x2800 <= ptr <= 0x2D80:
                hits += 1
        if best is None or hits > best[1]:
            best = (load_base, hits)
    return best

if __name__ == "__main__":

    buf = load_driver("u5/EGA.DRV")

    scan_sequences(buf)
    exit()
    
    load_base = guess_load_base(buf)
    print(f"# load base guess = {load_base}")
    # Example: dump first 8 IDs
    for i in range(8):
        dump_id(buf, i, load_base[0])
