import os
from toolbox import tb

host = os.environ.get("EXTENSION_HOST", "localhost")
port = int(os.environ.get("EXTENSION_PORT", "9876"))

tb.serve(host=host, port=port)
