import streamlit as st
from login import is_authenticated, show_login_page

def check_authentication():
    """Check if user is authenticated and show login page if not."""
    if not is_authenticated():
        show_login_page()
        return False
    return True

def require_auth():
    """Decorator to require authentication for a page."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator
