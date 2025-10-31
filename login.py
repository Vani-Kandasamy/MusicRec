# login.py

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from urllib.parse import parse_qs

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from urllib.parse import urlparse, parse_qs
import secrets

# OAuth2 configuration
def get_flow():
    try:
        redirect_uri = st.secrets.get("CALLBACK_URL", "http://localhost:8501")
        return Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                    "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ],
            redirect_uri=redirect_uri
        )
    except Exception as e:
        st.error(f"Error initializing OAuth flow: {str(e)}")
        raise

def get_google_auth_url():
    try:
        flow = get_flow()
        state = secrets.token_urlsafe(16)
        st.session_state['oauth_state'] = state

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account',
            state=state,
            approval_prompt='force',
            hd='*'
        )
        return auth_url
    except Exception as e:
        st.error(f"Error generating auth URL: {str(e)}")
        raise

def get_user_info(code):
    try:
        if 'oauth_state' not in st.session_state:
            raise ValueError("Invalid OAuth state")

        flow = get_flow()
        flow.fetch_token(code=code)

        id_info = id_token.verify_oauth2_token(
            flow.credentials.id_token,
            requests.Request(),
            st.secrets["GOOGLE_CLIENT_ID"]
        )

        if id_info['aud'] != st.secrets["GOOGLE_CLIENT_ID"]:
            raise ValueError("Invalid token audience")

        return {
            'email': id_info.get('email'),
            'name': id_info.get('name'),
            'picture': id_info.get('picture'),
            'access_token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'token_expiry': flow.credentials.expiry
        }
    except Exception as e:
        st.error(f"Error getting user info: {str(e)}")
        raise

def perform_login():
    try:
        query_string = urlparse(st.experimental_get_query_params()).query
        query_params = parse_qs(query_string)
        code = query_params.get('code', [None])[0]
        state = query_params.get('state', [None])[0]
        error = query_params.get('error', [None])[0]

        if error:
            st.error(f"OAuth error: {error}")
            return None, None

        if code and state:
            if 'oauth_state' not in st.session_state or st.session_state['oauth_state'] != state:
                st.error("Invalid OAuth state. Please try again.")
                return None, None

            try:
                user_info = get_user_info(code)
                if 'oauth_state' in st.session_state:
                    del st.session_state['oauth_state']

                st.session_state['user_info'] = user_info
                st.experimental_set_query_params()  # Clear the code from URL
                return user_info['email'], user_info['name']

            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                if 'oauth_state' in st.session_state:
                    del st.session_state['oauth_state']
                return None, None

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

    return None, None

def session_logout():
    if 'user_info' in st.session_state:
        del st.session_state['user_info']
    st.experimental_set_query_params()  # Clear URL parameters
    
# Add this function to your login.py file
def show_email_login():
    """Show email login form without database."""
    st.markdown("### Email Login")
    
    # Simple hardcoded credentials (for demo only)
    # In a real app, use proper authentication
    VALID_CREDENTIALS = {
        "user@example.com": "password123"  # email: password
    }
    
    with st.form("email_login"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            if not email or not password:
                st.warning("Please enter both email and password")
            elif email in VALID_CREDENTIALS and VALID_CREDENTIALS[email] == password:
                st.session_state['user_info'] = {
                    'email': email,
                    'name': email.split('@')[0]  # Use part before @ as name
                }
                st.success(f"Welcome back, {st.session_state['user_info']['name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password")

def show_login_page():
    """Display the login page with Google and email sign-in options."""
    st.title("🎵 Music for Mental Health")
    st.image(
        "https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg",
        use_container_width=True,
        caption="Your personal music therapy companion"
    )
    
    st.markdown("### Sign in to continue")
    
    # Google sign-in button
    try:
        auth_url = get_google_auth_url()
        st.markdown(
            f'<a href="{auth_url}" target="_self" style="text-decoration: none;">'
            '<button style="background-color: #4285F4; color: white; padding: 10px 20px; '
            'border: none; border-radius: 4px; font-weight: 500; cursor: pointer; '
            'display: flex; align-items: center; margin: 0 auto;">'
            '<svg width="18" height="18" viewBox="0 0 24 24" style="margin-right: 10px;">'
            '<path fill="white" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />'
            '<path fill="white" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />'
            '<path fill="white" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />'
            '<path fill="white" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />'
            '</svg>'
            'Sign in with Google'
            '</button>'
            '</a>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error setting up Google sign-in: {str(e)}")
    
    # Divider
    st.markdown("<div style='text-align: center; margin: 20px 0;'>OR</div>", unsafe_allow_html=True)
    
    # Show email login
    show_email_login()


def is_authenticated():
    """Check if user is authenticated."""
    return 'user_info' in st.session_state

def get_current_user():
    """Get current user info if authenticated."""
    return st.session_state.get('user_info')
