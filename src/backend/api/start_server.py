#!/usr/bin/env python
"""Start server and keep it running."""
import uvicorn
from main import app

print("=" * 70)
print("Starting Forensic Guardian API...")
print("=" * 70)

uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
