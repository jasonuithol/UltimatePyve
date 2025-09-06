# file: utilities/b64chunk.py
import base64, sys

CHUNK_SIZE = 10000  # characters per printed chunk

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <file>")
    sys.exit(1)

# Read and encode
with open(sys.argv[1], "rb") as f:
    b64_str = base64.b64encode(f.read()).decode()

if len(b64_str) < CHUNK_SIZE:
    print(b64_str)

else:

    # Output in labeled chunks
    for i in range(0, len(b64_str), CHUNK_SIZE):
        part_num = i // CHUNK_SIZE + 1
        print(f"--- PART {part_num} ---")
        print(b64_str[i:i+CHUNK_SIZE])