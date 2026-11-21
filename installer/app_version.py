"""Print server.APP_VERSION without importing the server (used by build-windows.bat)."""
import re
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "server.py").read_text(encoding="utf-8")
print(re.search(r'^APP_VERSION = "(\d+\.\d+\.\d+)"', source, re.M).group(1))
