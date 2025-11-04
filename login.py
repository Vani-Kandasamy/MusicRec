import streamlit as st
import toml
from pathlib import Path

# Load users from secrets.toml
def load_users():
    try:
        # In Streamlit Cloud, use st.secrets directly
        if hasattr(st, 'secrets') and hasattr(st.secrets, 'users'):
            return st.secrets.users
        # For local development with secrets.toml
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            with open(secrets_path) as f:
                return toml.load(f).get('users', {})
    except Exception as e:
        st.error(f"Error loading user credentials: {e}")
    return {}

USERS = load_users()
#st.write("Loaded users:", USERS)
def validate_email(email):
    """Basic email validation."""
    return '@' in email and '.' in email.split('@')[-1]

def authenticate(email, password):
    """Check if the provided email and password are correct."""
    return email in USERS and USERS[email] == password

def show_login_page():
    """Display login form."""
    if not is_authenticated():
        st.write("### Login")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if not validate_email(email):
                    st.error("Please enter a valid email address")
                elif authenticate(email, password):
                    st.session_state.update({
                        'authenticated': True,
                        'user_email': email,
                        'user_name': email.split('@')[0]  # Use part before @ as display name
                    })
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    else:
        user = get_current_user()
        st.write(f"Welcome, {user.get('name', 'User')}!")
        if st.button("Logout"):
            logout()

def is_authenticated():
    """Check if user is logged in."""
    return st.session_state.get('authenticated', False)

def get_current_user():
    """Get current user info if logged in."""
    if is_authenticated():
        return {
            'email': st.session_state.get('user_email'),
            'name': st.session_state.get('user_name')
        }
    return None

def logout():
    """Log out the current user."""
    for key in ['authenticated', 'user_email', 'user_name']:
        st.session_state.pop(key, None)
    st.rerun()
