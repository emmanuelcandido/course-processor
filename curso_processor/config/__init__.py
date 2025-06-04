"""
Configuration package for Curso Processor
"""

from .settings import *

# Import credentials conditionally to avoid keyring issues
try:
    from .credentials import *
    HAS_CREDENTIALS = True
except Exception:
    HAS_CREDENTIALS = False