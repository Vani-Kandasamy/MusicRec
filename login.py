import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from urllib.parse import urlparse, parse_qs
import secrets

# login.py
import streamlit as st

def show_login_page():
    """Show login/logout UI and handle authentication state."""
    if not st.user.is_authenticated:
        # Show login button
        if st.button("🎵 Log in with Google", type="primary", use_container_width=True):
            st.login()
    else:
        # Show welcome message and user info
        col1, col2 = st.columns([4, 1])
        with col1:
            st.html(
                f"<div style='font-size: 1.2rem;'>"
                f"Welcome, <span style='color: #FF4B4B; font-weight: bold;'>{st.user.name}</span>!"
                f"</div>"
            )
        with col2:
            if st.button("🚪 Log out", type="secondary", use_container_width=True):
                st.logout()
                st.rerun()

def is_authenticated():
    """Check if user is logged in."""
    return st.user.is_authenticated

def get_current_user():
    """Get current user's email if logged in."""
    return st.user.email if is_authenticated() else None
