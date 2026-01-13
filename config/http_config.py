"""
StreamableHTTP Configuration
"""
import os
from dataclasses import dataclass

@dataclass
class HTTPConfigSTClient:
    "Configuration for remote server"
    backend_url : str = 'http://localhost:8001/mcp'
    #backend_url : str = 'https://techpaperai.onrender.com'
    health_check_timeout : float = 3.0
    backend_timeout : int = 60
