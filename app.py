import streamlit as st
import asyncio
from login import show_login_page, is_authenticated, get_current_user, logout
from music import predict_favorite_genre, create_and_compose, get_spotify_playlist
from database import get_user_profile, create_initial_user_profile, display_stored_user_data, update_user_mood
from navigation import create_top_navigation, handle_page_navigation
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

def main_page():
    """Main dashboard page with overview and quick actions."""
    st.title("🎵 Music for Mental Health Dashboard")
    
    # Get user data from session state
    user_profile = st.session_state.get('user_profile')
    model = st.session_state.get('model')
    sp_client = st.session_state.get('sp_client')
    
    if not user_profile or not model:
        st.error("User data not properly loaded. Please refresh the page.")
        return
    
    # Quick overview cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            predicted_genre = predict_favorite_genre(user_profile, model)
            st.metric("Your Genre", predicted_genre)
        except:
            st.metric("Your Genre", "Unknown")
    
    with col2:
        mood_score = user_profile.get('Depression', 5)
        st.metric("Mood Score", f"{mood_score}/10")
    
    with col3:
        music_hours = user_profile.get('Hours per day', 0)
        st.metric("Music Hours/Day", music_hours)
    
    st.markdown("---")
    
    # Quick actions
    st.header("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🎵 AI Music")
        st.write("Generate personalized AI music based on your mood.")
        if st.button("Generate AI Music", key="quick_ai_music", type="primary"):
            st.switch_page("pages/03_AI_Music.py")
    
    with col2:
        st.subheader("🎧 Spotify Playlists")
        st.write("Get curated playlists from Spotify.")
        if st.button("Get Spotify Playlist", key="quick_spotify", type="primary"):
            st.switch_page("pages/04_Spotify_Playlists.py")
    
    with col3:
        st.subheader("😊 Update Mood")
        st.write("Track your current emotional state.")
        if st.button("Update Mood", key="quick_mood", type="primary"):
            st.switch_page("pages/02_Current_Mood.py")
    
    # Recent activity
    st.markdown("---")
    st.header("Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Music")
        if 'music_history' in st.session_state and st.session_state.music_history:
            for genre, timestamp in st.session_state.music_history[-3:]:
                st.write(f"🎵 {genre} - {timestamp}")
        else:
            st.write("No music generated yet.")
    
    with col2:
        st.subheader("Recent Playlists")
        if 'playlist_history' in st.session_state and st.session_state.playlist_history:
            for genre, url, timestamp in st.session_state.playlist_history[-3:]:
                st.write(f"🎧 [{genre}]({url}) - {timestamp}")
        else:
            st.write("No playlists generated yet.")

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
            page_title="Music for Mental Health",
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
        
        # Handle page navigation
        is_dashboard = handle_page_navigation()
        
        if not is_dashboard:
            return  # Exit if redirected to another page
        
        # Create top navigation
        create_top_navigation()
        
        # Display header image
        st.image("https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg", 
                use_column_width=True)
        
        # Show the main dashboard
        main_page()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    asyncio.run(main())
