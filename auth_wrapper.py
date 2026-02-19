import streamlit as st
from login_simple import is_authenticated, show_login_page

def check_authentication():
    """Check if user is authenticated and show login page if not."""
    if not is_authenticated():
        show_login_page()
        return False
    return True

def require_auth(func):
    """Decorator to require authentication for a page."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper
