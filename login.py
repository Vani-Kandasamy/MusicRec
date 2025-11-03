# login.py
import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749 import OAuth2Token
import os
import json

# Configuration
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
    """Show login UI with Google OAuth button."""
    if not is_authenticated():
        st.write("### Log in with Google")
        
        # Create OAuth session
        oauth = create_oauth_session()
        authorization_url, state = oauth.create_authorization_url(
            AUTH_CONFIG["authorization_base_url"],
            access_type="offline",
            prompt="select_account"
        )
        
        # Store state in session
        st.session_state['oauth_state'] = state
        
        # Display login button
        if st.button('Log in with Google', type="primary"):
            st.session_state['auth_redirect'] = authorization_url
            st.experimental_rerun()
        
        # Handle redirect if needed
        if 'auth_redirect' in st.session_state:
            st.markdown(f'<meta http-equiv="refresh" content="0;url={st.session_state.auth_redirect}">', 
                       unsafe_allow_html=True)
    else:
        # Show user info and logout button
        user = get_current_user()
        st.write(f"Welcome, {user.get('name', 'User')}!")
        if st.button("Log out", type="secondary"):
            logout()

def handle_google_callback():
    """Handle OAuth callback and exchange code for token."""
    params = st.query_params
    if "code" in params and "state" in params:
        try:
            # Verify state
            if 'oauth_state' not in st.session_state or params["state"][0] != st.session_state.oauth_state:
                st.error("Invalid state parameter")
                return False

            # Create OAuth session and fetch token
            oauth = create_oauth_session()
            token = oauth.fetch_token(
                AUTH_CONFIG["token_url"],
                authorization_response=st.query_params.url,
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
            
            # Clear OAuth state
            st.session_state.pop('oauth_state', None)
            st.session_state.pop('auth_redirect', None)
            
            # Clear URL parameters
            st.query_params.clear()
            return True
            
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    return False

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
    for key in ['user_authenticated', 'user_name', 'user_email', 'access_token', 'oauth_state', 'auth_redirect']:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.experimental_rerun()
