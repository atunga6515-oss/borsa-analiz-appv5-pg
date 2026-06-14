import os
import json
from alpharank_engine import AlphaRank15D

# Mock out DB calls in AlphaRank15D just for this test
class TestEngine(AlphaRank15D):
    def get_current_pool(self, username):
        return [{"ticker": "AKBNK.IS"}]
        
engine_obj = TestEngine()
res = engine_obj.analyze_ticker("AKBNK.IS")
print(json.dumps(res, indent=2))
