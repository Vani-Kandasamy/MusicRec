# login.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests

# Move secrets check to a function to handle missing secrets gracefully
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
        if st.button('Log in', type="primary"):
            oauth_flow = create_oauth_flow()
            oauth_flow.redirect_uri = REDIRECT_URI
            authorization_url, state = oauth_flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account'
            )
            
            # Store state in both session and a cookie
            st.session_state['oauth_state'] = state
            
            # Use JavaScript to set a cookie with the state
            js = f"""
            document.cookie = 'oauth_state={state}; path=/; max-age=3600; SameSite=Lax';
            window.location.href = '{authorization_url}';
            """
            st.components.v1.html(f"<script>{js}</script>", height=0, width=0)
    else:
        st.write(f"Welcome, {st.session_state.get('user_name', 'User')}!")
        if st.button("Log out", type="secondary"):
            # Clear all session data
            for key in ['user_authenticated', 'user_name', 'user_email', 'oauth_state']:
                st.session_state.pop(key, None)
            # Clear the cookie
            st.components.v1.html("""
                <script>
                document.cookie = 'oauth_state=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
                </script>
            """, height=0, width=0)
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
            # Get the state from URL parameters
            state = params["state"][0] if isinstance(params["state"], list) else params["state"]
            
            # Debug output
            st.write("Session state:", st.session_state)
            st.write("URL state:", state)
            
            if 'oauth_state' not in st.session_state:
                st.error("No OAuth state found in session. Please try logging in again.")
                return
                
            if state != st.session_state.oauth_state:
                st.error("Invalid state parameter. Possible CSRF attack detected.")
                return

            oauth_flow = create_oauth_flow()
            oauth_flow.redirect_uri = REDIRECT_URI
            token_response = oauth_flow.fetch_token(
                code=params["code"][0] if isinstance(params["code"], list) else params["code"],
                authorization_response=st.query_params.url
            )
            
            # Get user info
            user_info_response = requests.get(
                'https://www.googleapis.com/oauth2/v1/userinfo',
                headers={'Authorization': f'Bearer {oauth_flow.credentials.token}'},
            )
            user_info = user_info_response.json()

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
            st.rerun()

        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.write("Debug info:", {
                "params": dict(params),
                "session_state": dict(st.session_state)
            })
