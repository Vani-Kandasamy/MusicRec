import streamlit as st
import asyncio
from login import show_login_page, is_authenticated, get_current_user, logout
from music import predict_favorite_genre, create_and_compose, get_spotify_playlist
from database import get_user_profile, create_initial_user_profile, display_stored_user_data, update_user_mood
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import nest_asyncio
from datetime import datetime
import pickle
from pathlib import Path
# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

def load_model():
    """Load the trained XGBoost model."""
    try:
        model_path = Path("best_xgb")
        if not model_path.exists():
            raise FileNotFoundError("Model file not found. Please ensure best_xgb.pkl is in the project root.")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"❌ Error loading model: {str(e)}")
        raise

def initialize_spotify():
    """Initialize Spotify client with error handling."""
    try:
        if not all(key in st.secrets for key in ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"]):
            st.error("❌ Spotify API credentials are missing. Please check your secrets.toml")
            return None
            
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=st.secrets["SPOTIFY_CLIENT_ID"],
            client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"]
        ))
    except Exception as e:
        st.error(f"❌ Failed to initialize Spotify client: {str(e)}")
        return None

async def home_page():
    """Display home page with welcome message."""
    
    # Set background color
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .welcome-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 70vh;
        text-align: center;
        color: white;
    }
    .main-title {
        font-size: 4rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        opacity: 0.9;
        max-width: 600px;
        line-height: 1.6;
    }
    .feature-cards {
        display: flex;
        gap: 2rem;
        margin-top: 3rem;
        flex-wrap: wrap;
        justify-content: center;
        align-items: stretch;
    }
    .feature-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        width: 280px;
        min-height: 200px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        opacity: 0.8;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Welcome content
    st.markdown("""
    <div class="welcome-container">
        <div class="main-title">Reimagining Music Therapy</div>
        <div class="subtitle">TheraBeat AI</div>
        <div class="subtitle">Your personalized journey to mental wellness through the power of generative audio landscapes.</div>
        
        <div class="feature-cards">
            <div class="feature-card">
                <div class="feature-icon">🎵</div>
                <div class="feature-title">AI Music</div>
                <div class="feature-desc">Generate personalized music based on your mood and preferences</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎧</div>
                <div class="feature-title">Spotify Playlists</div>
                <div class="feature-desc">Get curated playlists tailored to your emotional state</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">😊</div>
                <div class="feature-title">Mood Tracking</div>
                <div class="feature-desc">Track your emotional journey over time</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

async def main():
    # Initialize session state
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'music_history' not in st.session_state:
        st.session_state.music_history = []
    if 'playlist_history' not in st.session_state:
        st.session_state.playlist_history = []

    """Main application function."""
    try:
        # Set page config
        st.set_page_config(
            page_title="TheraBeat AI - Home",
            page_icon="🎵",
            layout="wide"
        )
        
        # Show login page if not authenticated
        if not is_authenticated():
            show_login_page()
            return

        # Get current user
        user = get_current_user()
        if not user:
            st.error("Failed to get user information. Please try logging in again.")
            show_login_page()
            return

        # Initialize Spotify client
        sp_client = initialize_spotify()
        if not sp_client:
            st.error("Failed to initialize Spotify client. Please check your credentials.")
            return

        # Load the trained model
        model = load_model()
        if not model:
            st.error("Failed to load the prediction model.")
            return
        
        # Get user profile
        user_email = user['email']
        user_profile = get_user_profile(user_email)
        
        if user_profile is None:
            # First-time user - show profile creation
            user_profile = create_initial_user_profile(user_email)
            
            if user_profile is None:
                # User didn't complete profile
                st.warning("Please complete your profile to continue.")
                return
        
        # Store data in session state for other pages
        st.session_state.user_profile = user_profile
        st.session_state.model = model
        st.session_state.sp_client = sp_client
        st.session_state.user = user
        
        # Add logout button in sidebar
        if st.sidebar.button("🚪 Logout", type="secondary"):
            logout()
            st.rerun()
        
        # Show welcome message in sidebar
        st.sidebar.write(f"Welcome, {user.get('name', 'User')}!")
        
        # Show the main home page
        await home_page()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    asyncio.run(main())
