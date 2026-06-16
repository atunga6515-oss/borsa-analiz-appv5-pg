import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../core")

import analysis_service

def main():
    try:
        res = analysis_service.run_deep_analysis("AKSA")
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
