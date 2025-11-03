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
    import streamlit.components.v1 as components
    from urllib.parse import urlencode
    import time
    
    params = st.query_params
    if "code" in params and "state" in params:
        try:
            # Get the state from URL parameters
            state = params["state"][0] if isinstance(params["state"], list) else params["state"]
            
            # Debug output
            st.write("Session state:", st.session_state)
            st.write("URL state:", state)
            
            # Try to get state from session first, then from cookies
            if 'oauth_state' not in st.session_state:
                # Create a placeholder for the state
                state_placeholder = st.empty()
                
                # JavaScript to get the cookie
                get_cookie_js = """
                <script>
                function getCookie(name) {
                    const value = `; ${document.cookie}`;
                    const parts = value.split(`; ${name}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                }
                const state = getCookie('oauth_state');
                const element = window.parent.document.getElementById('state_placeholder');
                if (element) {
                    element.value = state || '';
                    element.dispatchEvent(new Event('input'));
                }
                </script>
                """
                
                # Add a hidden input to capture the state
                state_value = state_placeholder.text_input(
                    "state_input",
                    key="state_input",
                    label_visibility="collapsed",
                    placeholder="Loading..."
                )
                
                # Inject the JavaScript
                components.html(get_cookie_js, height=0, width=0)
                
                # Wait a moment for the JavaScript to execute
                time.sleep(1)
                
                # Get the state from the input
                state_from_cookie = st.session_state.get("state_input")
                
                if not state_from_cookie or state_from_cookie == "Loading...":
                    st.error("Could not retrieve OAuth state. Please try logging in again.")
                    return
                    
                st.session_state['oauth_state'] = state_from_cookie
                state_placeholder.empty()  # Remove the input
            
            if state != st.session_state.oauth_state:
                st.error("""
                    Invalid state parameter. Possible CSRF attack detected.
                    \n\n**Troubleshooting:**
                    - Try clearing your browser cookies for this site
                    - Try in an incognito window
                    - Make sure you're not using any ad blockers that might interfere
                """)
                return

            # Create OAuth flow and exchange code for token
            oauth_flow = create_oauth_flow()
            oauth_flow.redirect_uri = REDIRECT_URI
            
            # Build the full redirect URL
            redirect_response = f"{REDIRECT_URI}?{urlencode(params)}"
            
            # Exchange the authorization code for a token
            token_response = oauth_flow.fetch_token(
                code=params["code"][0] if isinstance(params["code"], list) else params["code"],
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
            
            # Clear the OAuth state and input after successful authentication
            st.session_state.pop('oauth_state', None)
            if 'state_input' in st.session_state:
                st.session_state.pop('state_input')
            
            # Clear URL parameters and cookies
            st.query_params.clear()
            components.html("""
                <script>
                document.cookie = 'oauth_state=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
                </script>
            """, height=0, width=0)
            
            # Force a rerun to update the UI
            st.rerun()

        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.write("Debug info:", {
                "params": dict(params),
                "session_state": {k: v for k, v in st.session_state.items() if k != '_last_rerun'}
            })
            st.exception(e)  # Show full traceback for debugging
