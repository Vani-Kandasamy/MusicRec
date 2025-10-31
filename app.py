# app.py

import streamlit as st
from login import is_authenticated, get_current_user, show_login_page, session_logout
from database import get_user_profile, create_initial_user_profile, display_stored_user_data
from music import predict_favorite_genre, create_and_compose, get_spotify_playlist
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import asyncio
from datetime import datetime
import pickle
from pathlib import Path

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

async def show_music_recommendations(user_profile, sp_client):
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
                playlist_url = await get_spotify_playlist(genre)  # Make sure this is awaited
                if playlist_url:
                    st.success(f"Here's a {genre} playlist for you:")
                    st.markdown(f"[Open Playlist in Spotify]({playlist_url})")
                else:
                    st.warning(f"No {genre} playlists found. Please try another genre.")
            except Exception as e:
                st.error(f"❌ Failed to fetch playlist: {str(e)}")


def show_error_page(message):
    """Display an error page with a message."""
    st.error(f"❌ {message}")
    if st.button("Return to Home"):
        st.rerun()

def track_mood(user_email, current_mood=None):
    """Display mood tracking form and save the data."""
    st.subheader("How are you feeling today?")
    
    with st.form("mood_tracking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Changed from slider to Yes/No selectbox
            exploratory = st.selectbox(
                "Are you open to exploring new music today?",
                ['Yes', 'No'],
                index=0 if not current_mood or current_mood.get('Exploratory', 1) == 1 else 1
            )
            anxiety = st.slider("Anxiety level (1-10)", 1, 10, 
                              current_mood.get('Anxiety', 5) if current_mood else 5)
            depression = st.slider("Mood level (1-10)", 1, 10, 
                                 current_mood.get('Depression', 5) if current_mood else 5)
        
        with col2:
            insomnia = st.slider("Sleep quality (1-10)", 1, 10, 
                               current_mood.get('Insomnia', 5) if current_mood else 5)
            ocd = st.slider("Focus level (1-10)", 1, 10, 
                           current_mood.get('OCD', 5) if current_mood else 5)
        
        if st.form_submit_button("Save Mood"):
            mood_data = {
                'Exploratory': 1 if exploratory == 'Yes' else 0,  # Encode as 1 for Yes, 0 for No
                'Anxiety': anxiety,
                'Depression': depression,
                'Insomnia': insomnia,
                'OCD': ocd,
                'last_mood_update': datetime.now().isoformat()
            }
            if update_user_mood(user_email, mood_data):
                st.success("Mood data saved successfully!")
                return mood_data
    return None

async def main():
    """Main application function."""
    try:
        # Set page config
        st.set_page_config(
            page_title="Music for Mental Health",
            page_icon="🎵",
            layout="wide"
        )
        
        # Check authentication
        if not is_authenticated():
            show_login_page()
            return
            
        # Get current user info
        user = get_current_user()
        user_email = user['email']
        user_name = user['name']
        
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
        
        # Show welcome message
        st.sidebar.success(f"Welcome, {user_name}!")
        
        # Add logout button
        if st.sidebar.button("Logout"):
            session_logout()
            st.rerun()
            
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
        await show_music_recommendations(user_profile, sp_client)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
