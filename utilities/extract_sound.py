#!/usr/bin/env python3
import struct
from pathlib import Path

PIT_CLOCK = 1193180.0   # Hz
#TICK_HZ   = 18.2065     # system timer frequency
TICK_HZ   = 360     # system timer frequency
TICK_SEC  = 1.0 / TICK_HZ

def load_divisor_table(buf, offset=0x2540, count=64):
    """Read 16-bit little-endian divisors from the driver."""
    table = []
    for i in range(count):
        val = struct.unpack_from("<H", buf, offset + i*2)[0]
        table.append(val)
    return table

def scan_sequences(buf, start=0x2800, end=None, min_pairs=3, max_pairs=64):
    """Scan for plausible note/duration sequences in the data section."""
    if end is None:
        end = len(buf)
    seqs = []
    i = start
    while i < end-2:
        s = i
        pairs = []
        while i+1 < end:
            n, d = buf[i], buf[i+1]
            if n in (0x00, 0xFF) or d in (0x00, 0xFF):
                break
            if n > 0x7F or d > 0xF0:  # sanity filter
                break
            pairs.append((n, d))
            i += 2
        if len(pairs) >= min_pairs:
            seqs.append((s, pairs))
            i += 1
        else:
            i = s+1
    return seqs

def sequence_to_freqs(seq, divisors):
    """Convert note indices to (Hz, seconds) tuples."""
    out = []
    for note, dur in seq:
        hz = 0.0
        if note < len(divisors):
            div = divisors[note]
            if div != 0:
                hz = PIT_CLOCK / div
        seconds = dur * TICK_SEC
        out.append((hz, seconds))
    return out

if __name__ == "__main__":
    buf = Path("u5/EGA.DRV").read_bytes()
    divisors = load_divisor_table(buf)

    sequences = scan_sequences(buf, start=0x2800, end=0x2D80)
    for addr, seq in sequences: #[:10]:  # show first 10 sequences
#        print(f"Sequence @0x{addr:04X}, {len(seq)} pairs")
        freqs = sequence_to_freqs(seq, divisors)
        '''
        for hz, sec in freqs:
            if hz > 0:
                print(f"  {hz:7.1f} Hz for {sec:.3f} s")
            else:
                print(f"   rest     for {sec:.3f} s")
        '''
        for hz, sec in freqs:
            if not (0 <= hz < 20000):
                hz = 0
            print(f"{hz:.1f},{sec:.3f}")
        print("---")