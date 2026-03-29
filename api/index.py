import os
import sys
from pathlib import Path

# Add the backend directory to Python path so "from app.*" imports resolve
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set DATA_DIR to the data/ directory using an absolute path
project_root = Path(__file__).resolve().parent.parent
os.environ.setdefault("DATA_DIR", str(project_root / "data"))

# Import the FastAPI app - Vercel's Python runtime auto-detects ASGI apps
from app.main import app  # noqa: E402
