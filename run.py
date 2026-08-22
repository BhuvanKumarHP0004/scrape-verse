#!/usr/bin/env python3
"""
SentinelScrape - Main Application Entrypoint
Launches the FastAPI backend and serves the interactive cyber-observability frontend.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Load .env file from project root or current working directory
load_dotenv()

# Add backend directory to Python path
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def main():
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("\n" + "="*70)
    print(" 🚀 SentinelScrape — Autonomous Scraping Trust Layer & Observability")
    print("="*70)
    print(f" • Dashboard UI:      http://localhost:{port}/")
    print(f" • API Documentation: http://localhost:{port}/docs")
    print(f" • Health Endpoint:   http://localhost:{port}/health")
    print(f" • Bright Data Mesh:  Active (Browser / DCA Studio)")
    print("="*70 + "\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        app_dir=str(BACKEND_DIR),
        log_level="info",
    )

if __name__ == "__main__":
    main()
