import time
import threading
from functools import wraps

def ttl_cache(ttl_seconds=300):
    """
    Basit, thread-safe, zaman (TTL) tabanlı bir in-memory cache decorator.
    Streamlit'in @st.cache_data yapısının yerini almak üzere tasarlandı.
    """
    def decorator(func):
        cache = {}
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Parametreleri string'e çevirip bir key üretiyoruz
            key = str(args) + str(kwargs)
            
            with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl_seconds:
                        return result
            
            # Cache'de yoksa veya süresi dolduysa fonksiyonu çalıştır
            result = func(*args, **kwargs)
            
            with lock:
                cache[key] = (result, time.time())
                
            return result
            
        return wrapper
    return decorator
