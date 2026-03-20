#!/usr/bin/env python
"""Debug server runner."""

import sys
import traceback
import uvicorn
from main import app

if __name__ == "__main__":
    try:
        print("Starting server...")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=9000,
            log_level="debug"
        )
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
