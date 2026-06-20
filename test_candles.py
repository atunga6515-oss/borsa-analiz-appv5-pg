import sys
sys.path.append(".")
from debug_layered_4 import fetch_layered_data
import contextlib, io

f = io.StringIO()
with contextlib.redirect_stdout(f):
    fetch_layered_data("ASTOR")
