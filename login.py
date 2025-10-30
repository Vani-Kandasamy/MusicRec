import streamlit as st
from streamlit_auth_component import login_button

def perform_login():
    # Retrieve Google OAuth credentials
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    CALLBACK_URL = st.secrets.get("CALLBACK_URL", "http://localhost:8501")

    user_data = login_button(client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET, redirect_uri=CALLBACK_URL)

    if user_data:
        return user_data.get('email'), user_data.get('name')
    else:
        return None, None

def auth_login(client_id, redirect_uri):
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=openid%20email%20profile&access_type=offline"
    st.experimental_rerun(auth_url)

def session_logout():
    if 'user_info' in st.session_state:
        del st.session_state['user_info']
    st.experimental_rerun()
