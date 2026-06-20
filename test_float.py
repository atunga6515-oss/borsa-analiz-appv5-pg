import numpy as np
def clean_nans(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    return obj

val = np.float64(1.0)
print("Is float:", isinstance(val, float))
print("Result:", clean_nans(val))
