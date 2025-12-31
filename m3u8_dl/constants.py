from pathlib import Path
import sys

FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR =  Path(__file__).resolve().parent.parent

WAIT_SECONDS = 10
NB_PARTS = 15

# french stream
FRENCH_STREAM_BASE_URL = "https://fs2.lol"