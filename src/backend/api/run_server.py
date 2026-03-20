#!/usr/bin/env python
"""Simple server runner with custom port."""

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9000,
        log_level="info"
    )
