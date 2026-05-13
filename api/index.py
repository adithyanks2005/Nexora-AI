import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import the main app from backend
try:
    from backend.main import app
    print("Successfully imported app from backend.main")
except Exception as e:
    print(f"Error importing app: {e}")
    raise

# Re-export for Vercel
application = app
# explicitly export 'app' as well
app = application
