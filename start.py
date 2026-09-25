import uvicorn
import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file if present
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

from backend.database import init_db
from backend.auth import ensure_demo_user
from backend.demo_generator import seed_demo_data

def main():
    print("=" * 65)
    print("  OMNIDOC AI -- Intelligent Document Processing Platform")
    print("  Enterprise Autonomous Classification, Extraction & Validation")
    print("=" * 65)
    
    print("\n[1/3] Initializing SQLite database schema...")
    init_db()
    
    print("[2/3] Setting up Demo Auditor authentication session...")
    ensure_demo_user()
    
    print("[3/3] Generating realistic sample PDF documents & intelligence seeds...")
    seed_demo_data()
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    print("\n" + "=" * 65)
    print("  >> Platform Ready! Serving live on:")
    print(f"     http://127.0.0.1:{port}")
    print(f"     http://localhost:{port}")
    print("=" * 65 + "\n")
    
    uvicorn.run("backend.app:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()

