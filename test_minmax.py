import sys
sys.path.append(".")
from debug_layered_4 import fetch_layered_data
import contextlib, io

f = io.StringIO()
with contextlib.redirect_stdout(f):
    payload = None
    import builtins
    original_print = builtins.print
    def mock_print(*args):
        pass
    builtins.print = mock_print
    # We will modify the function directly to return the dict instead of printing
