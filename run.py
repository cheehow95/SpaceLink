#!/usr/bin/env python3
"""
SpaceLink - Ultra-Low Latency Remote Desktop Solution
Run this file to start the server.
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    from src.core.server import app
    
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║           🛰️  SpaceLink v4.1                      ║
    ║     Ultra-Low Latency Remote Desktop Solution     ║
    ╠═══════════════════════════════════════════════════╣
    ║  Server:     http://localhost:8000                ║
    ║  Web Client: http://localhost:8000/webrtc-test    ║
    ║  API Docs:   http://localhost:8000/docs           ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
