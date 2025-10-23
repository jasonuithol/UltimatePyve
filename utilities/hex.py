import sys
from pathlib import Path

def hex_dump(path, width=32):
    data = Path(path).read_bytes()
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hexs = " ".join(f"{b:02X}" for b in chunk)
        print(f"{i:08X}  {hexs}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hex32.py <file> [width]")
        sys.exit(1)
    file = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    hex_dump(file, w)
