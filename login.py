# login.py

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from urllib.parse import parse_qs

# OAuth2 configuration
def get_flow():
    """Create and return the OAuth flow using Streamlit secrets."""
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets.get("CALLBACK_URL", "http://localhost:8501")]
            }
        },
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ],
        redirect_uri=st.secrets.get("CALLBACK_URL")
    )

def get_google_auth_url():
    """Generate and return the Google OAuth URL."""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='select_account'  # Force account selection
    )
    return auth_url

def get_user_info(code):
    """Get user info using the authorization code."""
    flow = get_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        st.secrets["GOOGLE_CLIENT_ID"]
    )
    return {
        'email': id_info.get('email'),
        'name': id_info.get('name'),
        'picture': id_info.get('picture')
    }

def perform_login():
    """Handle the login flow."""
    query_params = st.experimental_get_query_params()
    code = query_params.get('code', [None])[0]
    
    if code:
        try:
            user_info = get_user_info(code)
            st.session_state['user_info'] = user_info
            st.experimental_set_query_params()  # Clear the code from URL
            return user_info['email'], user_info['name']
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return None, None
    return None, None

def session_logout():
    """Log out the current user."""
    if 'user_info' in st.session_state:
        del st.session_state['user_info']
    st.experimental_set_query_params()

def show_login_page():
    """Display the login page with Google sign-in button."""
    st.title("🎵 Music for Mental Health")
    st.image(
        "https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg",
        use_column_width=True,
        caption="Your personal music therapy companion"
    )
    
    st.markdown("### Sign in to continue")
    
    # Google sign-in button
    auth_url = get_google_auth_url()
    # Simple Google sign-in button
    if st.button('Sign in with Google', key='google_signin'):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
        st.stop()

def is_authenticated():
    """Check if user is authenticated."""
    return 'user_info' in st.session_state

def get_current_user():
    """Get current user info if authenticated."""
    return st.session_state.get('user_info')
