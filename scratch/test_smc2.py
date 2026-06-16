import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

import core.analysis_service as analysis_service

async def main():
    try:
        res = analysis_service.run_deep_analysis("AKSA")
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
