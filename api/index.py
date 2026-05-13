import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import the main app from backend
from backend.main import app

# Re-export for Vercel (both 'app' and 'application' work)
application = app
