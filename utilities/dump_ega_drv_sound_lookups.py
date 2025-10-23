from pathlib import Path
import struct

def dump_index_and_sequences(path, base_offset=0x7000, count=32, max_len=64):
    data = Path(path).read_bytes()
    assert len(data) > base_offset, f"offset too large for file_size={len(data)}"
    assert len(data) > base_offset + (max_len * count), f"search range goes past end of file_size={len(data)}"

    for i in range(count):
        off = base_offset + i*4
        if off+4 > len(data): break
        lo, hi = struct.unpack_from("<HH", data, off)
        ptr = lo  # offset within file
        if ptr == 0 or ptr >= len(data): 
            continue
        # read sequence
        seq = []
        j = ptr
        while j < len(data) and len(seq) < max_len:
            b1 = data[j]
            if b1 in (0x00, 0xFF):  # terminator
                break
            if j+1 >= len(data): break
            b2 = data[j+1]
            seq.append((b1, b2))
            j += 2
        print(f"ID {i:02X} @0x{ptr:04X} → {len(seq)} pairs")
        print(" ", seq)
        print("---")

if __name__ == "__main__":
    dump_index_and_sequences("u5/EGA.DRV")