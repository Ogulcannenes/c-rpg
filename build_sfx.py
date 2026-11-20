"""Append the compressed app payload and a small footer to the native installer stub."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

MARKER = b"CPPADVENTURE_PAYLOAD_V1".ljust(24, b"\0")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: build_sfx.py installer-stub.exe payload.zip output.exe")
        return 2
    stub, archive, output = (Path(arg) for arg in sys.argv[1:])
    payload = archive.read_bytes()
    footer = MARKER + struct.pack("<Q", len(payload))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(stub.read_bytes() + payload + footer)
    print(f"Built {output} ({output.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
