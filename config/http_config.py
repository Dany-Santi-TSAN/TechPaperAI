"""
StreamableHTTP Configuration
"""
import os
from dataclasses import dataclass

@dataclass
class HTTPConfigSTClient:
    "Configuration for remote server"
    backend_url : str = 'http://localhost:8001'
    #backend_url : str = 'https://techpaperai.onrender.com'
    backend_timeout : int = 60
