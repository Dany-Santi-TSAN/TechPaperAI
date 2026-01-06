"""
SSE Configuration
"""
import os
from dataclasses import dataclass

@dataclass
class SseConfigSTClient:
    "Configuration for remote server"
    backend_url : str = 'https://techpaperai.onrender.com/sse'
    backend_timeout : int = 60
