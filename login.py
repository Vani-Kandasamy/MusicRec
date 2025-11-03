import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from urllib.parse import urlparse, parse_qs
import secrets


def show_login_page():
    """Show login/logout UI and handle authentication state."""
    if not st.session_state.get('user_authenticated', False):
        # Show login button
        if st.button("🎵 Log in with Google", type="primary", use_container_width=True):
            st.session_state['user_authenticated'] = True
            st.session_state['user_name'] = "User"  # Default name, can be updated after login
            st.rerun()
    else:
        # Show welcome message and user info
        col1, col2 = st.columns([4, 1])
        with col1:
            st.html(
                f"<div style='font-size: 1.2rem;'>"
                f"Welcome, <span style='color: #FF4B4B; font-weight: bold;'>{st.session_state.get('user_name', 'User')}</span>!"
                f"</div>"
            )
        with col2:
            if st.button("🚪 Log out", type="secondary", use_container_width=True):
                st.session_state.pop('user_authenticated', None)
                st.session_state.pop('user_name', None)
                st.rerun()

def is_authenticated():
    """Check if user is logged in."""
    return st.session_state.get('user_authenticated', False)

def get_current_user():
    """Get current user's email if logged in."""
    return st.session_state.get('user_name', 'user@example.com') if is_authenticated() else None
