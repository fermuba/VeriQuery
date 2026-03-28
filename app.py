import sys
import os
from pathlib import Path

# Add src/backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

# Import the FastAPI app
from api.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
