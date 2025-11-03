# login.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
from urllib.parse import urlencode

def get_google_credentials():
    try:
        return {
            "client_id": st.secrets["auth"]["client_id"],
            "client_secret": st.secrets["auth"]["client_secret"],
            "redirect_uri": st.secrets["auth"]["redirect_uri"]
        }
    except Exception as e:
        st.error("❌ Google OAuth credentials are not properly configured.")
        st.stop()

# Get credentials
creds = get_google_credentials()
GOOGLE_CLIENT_ID = creds["client_id"]
GOOGLE_CLIENT_SECRET = creds["client_secret"]
REDIRECT_URI = creds["redirect_uri"]

SCOPES = ['https://www.googleapis.com/auth/userinfo.profile', 
          'https://www.googleapis.com/auth/userinfo.email']

def create_oauth_flow():
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )

def show_login_page():
    """Show login/logout UI and handle authentication state."""
    if not is_authenticated():
        st.write("### Log in with Google")
        if st.button('Log in', type="primary", key="google_login_button"):
            try:
                oauth_flow = create_oauth_flow()
                oauth_flow.redirect_uri = REDIRECT_URI
                authorization_url, state = oauth_flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='select_account'
                )
                
                # Store the state in session
                st.session_state['oauth_state'] = state
                
                # Use JavaScript to redirect
                js = f"window.location.href = '{authorization_url}';"
                st.components.v1.html(f"<script>{js}</script>", height=0, width=0)
                
            except Exception as e:
                st.error(f"Failed to initialize login: {str(e)}")
    else:
        st.write(f"Welcome, {st.session_state.get('user_name', 'User')}!")
        if st.button("Log out", type="secondary", key="logout_button"):
            for key in ['user_authenticated', 'user_name', 'user_email', 'oauth_state']:
                st.session_state.pop(key, None)
            st.query_params.clear()
            st.rerun()

def is_authenticated():
    """Check if user is logged in."""
    return st.session_state.get('user_authenticated', False)

def get_current_user():
    """Get current user's email if logged in."""
    if is_authenticated():
        return {
            'email': st.session_state.get('user_email'),
            'name': st.session_state.get('user_name')
        }
    return None

def handle_google_callback():
    """Handle the OAuth callback from Google."""
    params = st.query_params
    if "code" in params and "state" in params:
        try:
            # Get the state and code from URL parameters
            state = params.get("state", [None])[0]
            code = params.get("code", [None])[0]
            
            if not state or not code:
                st.error("Missing required parameters in the callback URL")
                return

            if 'oauth_state' not in st.session_state or state != st.session_state.oauth_state:
                st.error("Invalid state parameter. Please try logging in again.")
                return

            oauth_flow = create_oauth_flow()
            oauth_flow.redirect_uri = REDIRECT_URI
            
            # Build the full redirect URL for token exchange
            redirect_response = f"{REDIRECT_URI}?{urlencode(params)}"
            
            # Exchange the authorization code for a token
            token_response = oauth_flow.fetch_token(
                code=code,
                authorization_response=redirect_response
            )
            
            # Get user info
            user_info_response = requests.get(
                'https://www.googleapis.com/oauth2/v1/userinfo',
                headers={'Authorization': f'Bearer {oauth_flow.credentials.token}'},
                timeout=10
            )
            user_info = user_info_response.json()

            if 'error' in user_info:
                raise Exception(f"Google API error: {user_info.get('error_description', 'Unknown error')}")

            # Store user info in session
            st.session_state.update({
                'user_authenticated': True,
                'user_name': user_info.get('name', 'User'),
                'user_email': user_info.get('email'),
                'access_token': oauth_flow.credentials.token
            })
            
            # Clear the OAuth state after successful authentication
            st.session_state.pop('oauth_state', None)
            
            # Clear URL parameters
            st.query_params.clear()
            
            # Force a rerun to update the UI
            st.rerun()

        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.write("Debug info:", {
                "error_type": type(e).__name__,
                "error_details": str(e)
            })
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                st.json(e.response.text)
