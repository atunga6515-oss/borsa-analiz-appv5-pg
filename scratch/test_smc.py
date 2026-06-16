import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.analysis_service import run_deep_analysis

async def main():
    try:
        res = run_deep_analysis("THYAO")
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
