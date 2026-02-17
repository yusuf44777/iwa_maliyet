"""
Vercel Python Serverless Function entry point.
FastAPI uygulamasını Vercel runtime'a sunar.
"""

import sys
from pathlib import Path

# Backend modüllerini import edebilmek için path'e ekle
_backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# FastAPI app'i import et – Vercel Python runtime ASGI app'i otomatik tanır
from main import app  # noqa: E402, F401
