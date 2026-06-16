import json
import numpy as np

try:
    val = np.float64(1.23)
    json.dumps({"val": val})
except Exception as e:
    print("JSON dumps failed on np.float64:", type(e).__name__, e)

try:
    from fastapi.encoders import jsonable_encoder
    jsonable_encoder({"val": val})
except Exception as e:
    print("jsonable_encoder failed on np.float64:", type(e).__name__, e)
