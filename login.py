import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
import os
import json

# --- Configuration ---
# This part is unchanged, it correctly reads from st.secrets
# Ensure your Streamlit Cloud secrets are set up like this:
# [auth]
# client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
# client_secret = "YOUR_CLIENT_SECRET"
# redirect_uri = "YOUR_APP_URL" (e.g., "https://yourapp.streamlit.app/")

AUTH_CONFIG = {
    "client_id": st.secrets["auth"]["client_id"],
    "client_secret": st.secrets["auth"]["client_secret"],
    "redirect_uri": st.secrets["auth"]["redirect_uri"],
    "authorization_base_url": "https://accounts.google.com/o/oauth2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
    "scope": ["openid", "email", "profile"]
}

def create_oauth_session():
    """Create and return an OAuth2 session."""
    return OAuth2Session(
        AUTH_CONFIG["client_id"],
        AUTH_CONFIG["client_secret"],
        scope=AUTH_CONFIG["scope"],
        redirect_uri=AUTH_CONFIG["redirect_uri"]
    )

def show_login_page():
    """
    Show login UI or user info.
    This function is "smart":
    - If not authenticated, it shows the login button.
    - If authenticated, it shows user info and the logout button.
    """
    if not is_authenticated():
        st.write("### Please log in to continue")
        
        # Create OAuth session
        oauth = create_oauth_session()
        authorization_url, state = oauth.create_authorization_url(
            AUTH_CONFIG["authorization_base_url"],
            access_type="offline",
            prompt="select_account"
        )
        
        # Store state in session for verification on callback
        st.session_state['oauth_state'] = state
        
        # *** CHANGED: Use st.link_button instead of st.button and meta refresh ***
        # This directly navigates the user's browser to the Google auth page.
        st.link_button(
            "Log in with Google",
            authorization_url,
            type="primary",
            use_container_width=True
        )
        
    else:
        # Show user info and logout button
        user = get_current_user()
        st.write(f"Welcome, **{user.get('name', 'User')}**!")
        st.write(f"Email: `{user.get('email')}`")
        if st.button("Log out", type="secondary", use_container_width=True):
            logout()

def handle_google_callback():
    """Handle OAuth callback, exchange code for token, and store user info."""
    params = st.query_params
    
    # Check for 'code' and 'state' in URL
    if "code" not in params or "state" not in params:
        st.error("Invalid callback request. Missing 'code' or 'state'.")
        return

    # --- State Verification ---
    # Check if 'oauth_state' is in session and matches the URL 'state'
    if 'oauth_state' not in st.session_state:
        st.error("Login state not found. Please try logging in again.")
        return
        
    # Get state from query params (it's a list)
    url_state = params["state"][0]
    
    if url_state != st.session_state.oauth_state:
        st.error(f"Invalid state parameter. Please try logging in again.")
        return

    # State is valid, clear it from session
    st.session_state.pop('oauth_state', None)

    # --- Token Fetching ---
    try:
        oauth = create_oauth_session()
        
        # *** CHANGED: Fetch token using 'code' directly ***
        token = oauth.fetch_token(
            AUTH_CONFIG["token_url"],
            code=params["code"][0],
            client_secret=AUTH_CONFIG["client_secret"]
        )
        
        # Get user info
        user_info = oauth.get(AUTH_CONFIG["userinfo_endpoint"]).json()
        
        # Store user data in session
        st.session_state.update({
            'user_authenticated': True,
            'user_name': user_info.get('name'),
            'user_email': user_info.get('email'),
            'access_token': token['access_token']
        })
        
        # *** ADDED: Clear query params and rerun ***
        # This is crucial to remove the 'code' and 'state' from the URL
        # and transition to the "logged in" app state.
        st.query_params.clear()
        st.rerun()
            
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        # Clean up session state on failure
        st.session_state.pop('user_authenticated', None)
        st.session_state.pop('user_name', None)
        st.session_state.pop('user_email', None)
        st.session_state.pop('access_token', None)

def is_authenticated():
    """Check if user is logged in."""
    return st.session_state.get('user_authenticated', False)

def get_current_user():
    """Get current user's info if logged in."""
    if is_authenticated():
        return {
            'name': st.session_state.get('user_name'),
            'email': st.session_state.get('user_email')
        }
    return None

def logout():
    """Log out the current user."""
    # Clear all authentication-related session state
    for key in ['user_authenticated', 'user_name', 'user_email', 'access_token', 'oauth_state']:
        st.session_state.pop(key, None)
    
    # Clear query parameters
    st.query_params.clear()
    
    # Rerun to refresh the page
    st.rerun()
