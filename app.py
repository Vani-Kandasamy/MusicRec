# app.py

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

async def show_music_recommendations(user_profile, sp_client, model):
    """Display music recommendations based on user profile."""
    st.title("Music for Mental Health")
    
    # Display user profile information
    display_stored_user_data(user_profile)
    
    # Main content area with two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🎵 AI-Generated Music")
        if st.button("Generate AI Music", key="generate_ai_music"):
            with st.spinner('Composing your personalized music...'):
                try:
                    genre = predict_favorite_genre(user_profile,model)
                    await create_and_compose(genre)  # Make sure this is awaited
                except Exception as e:
                    st.error(f"❌ Error generating music: {str(e)}")
    
    with col2:
        st.header("🎧 Spotify Playlists")
        if st.button("Get Spotify Playlist", key="get_spotify_playlist"):
            if not sp_client:
                st.error("Spotify is not available. Please check your credentials.")
                return
                
            try:
                genre = predict_favorite_genre(user_profile,model)
                playlist_url = await get_spotify_playlist(genre,sp_client)  # Make sure this is awaited
                
                if playlist_url:
                    st.success(f"Here's a {genre} playlist for you:")
                    st.markdown(f"[Open Playlist in Spotify]({playlist_url})")
                else:
                    st.warning(f"No {genre} playlists found. Please try another genre.")
            except Exception as e:
                st.error(f"❌ Failed to fetch playlist: {str(e)}")

async def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
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
        
        # Display header
        st.image("https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg", 
                use_column_width=True)
        
        
        # Add logout button in sidebar
        if st.sidebar.button("Logout", type="secondary"):
            logout()
            st.rerun()
            
            
        user_email = user['email']
        # Get or create user profile
        user_profile = get_user_profile(user_email)
        
        if user_profile is None:
            # First-time user - show profile creation
            user_profile = create_initial_user_profile(user_email)
            
            if user_profile is None:
                # User didn't complete profile
                st.warning("Please complete your profile to continue.")
                return
        
        # Show the main application
        await show_music_recommendations(user_profile, sp_client, model)    

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    asyncio.run(main())
