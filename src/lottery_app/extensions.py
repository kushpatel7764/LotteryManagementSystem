"""
Shared Flask extension instances.

Initialized here so they can be imported by blueprints without causing
circular imports with the application factory in __init__.py.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")
