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

async def profile_page(user_profile, model):
    """Display user profile and mood management page."""
    st.title("👤 Your Profile & Mood")
    
    # Display user profile information
    display_stored_user_data(user_profile)
    
    # Show predicted genre
    if st.button("Predict Your Favorite Genre", key="predict_genre_profile"):
        with st.spinner('Analyzing your preferences...'):
            try:
                genre = predict_favorite_genre(user_profile, model)
                st.success(f"Based on your profile, your predicted favorite genre is: **{genre}**")
            except Exception as e:
                st.error(f"❌ Error predicting genre: {str(e)}")

async def ai_music_page(user_profile, model):
    """Display AI-generated music page."""
    st.title("🎵 AI-Generated Music")
    
    # Show user's predicted genre
    try:
        predicted_genre = predict_favorite_genre(user_profile, model)
        st.info(f"Your predicted favorite genre: **{predicted_genre}**")
    except Exception as e:
        predicted_genre = "Pop"
        st.warning(f"Could not predict genre: {str(e)}. Using default: {predicted_genre}")
    
    # Music generation section
    st.header("Generate Personalized Music")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Generate a unique AI-composed track based on your mood and preferences.")
        
        if st.button("🎼 Generate AI Music", key="generate_ai_music", type="primary"):
            with st.spinner('🎵 Composing your personalized music...'):
                try:
                    success = await create_and_compose(predicted_genre)
                    if success:
                        st.success("✅ Music generated successfully! Check the player above.")
                    else:
                        st.error("❌ Failed to generate music. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error generating music: {str(e)}")
    
    with col2:
        st.subheader("Music History")
        if 'music_history' not in st.session_state:
            st.session_state.music_history = []
        
        if st.session_state.music_history:
            for i, (genre, timestamp) in enumerate(st.session_state.music_history[-5:], 1):
                st.write(f"{i}. {genre} - {timestamp}")
        else:
            st.write("No music generated yet.")

async def spotify_playlist_page(user_profile, sp_client, model):
    """Display Spotify playlist page."""
    st.title("🎧 Spotify Playlists")
    
    # Show user's predicted genre
    try:
        predicted_genre = predict_favorite_genre(user_profile, model)
        st.info(f"Your predicted favorite genre: **{predicted_genre}**")
    except Exception as e:
        predicted_genre = "Pop"
        st.warning(f"Could not predict genre: {str(e)}. Using default: {predicted_genre}")
    
    # Playlist generation section
    st.header("Get Personalized Playlists")
    
    if not sp_client:
        st.error("❌ Spotify is not available. Please check your credentials.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Get curated Spotify playlists based on your music preferences and current mood.")
        
        if st.button("🎵 Get Spotify Playlist", key="get_spotify_playlist", type="primary"):
            with st.spinner('🔍 Finding the perfect playlist for you...'):
                try:
                    playlist_url = await get_spotify_playlist(predicted_genre, sp_client)
                    
                    if playlist_url:
                        # Store in history
                        if 'playlist_history' not in st.session_state:
                            st.session_state.playlist_history = []
                        
                        st.session_state.playlist_history.append((predicted_genre, playlist_url, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        
                        st.success(f"✅ Here's a {predicted_genre} playlist for you:")
                        st.markdown(f"### [🎧 Open Playlist in Spotify]({playlist_url})")
                    else:
                        st.warning(f"No {predicted_genre} playlists found. Please try another genre.")
                except Exception as e:
                    st.error(f"❌ Failed to fetch playlist: {str(e)}")
    
    with col2:
        st.subheader("Playlist History")
        if 'playlist_history' not in st.session_state:
            st.session_state.playlist_history = []
        
        if st.session_state.playlist_history:
            for i, (genre, url, timestamp) in enumerate(st.session_state.playlist_history[-5:], 1):
                st.write(f"{i}. [{genre}]({url}) - {timestamp}")
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
        
        # Sidebar navigation
        st.sidebar.title("🎵 Music for Mental Health")
        st.sidebar.write(f"Welcome, {user.get('name', 'User')}!")
        
        # Add logout button in sidebar
        if st.sidebar.button("Logout", type="secondary"):
            logout()
            st.rerun()
        
        # Page selection
        st.sidebar.markdown("---")
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["👤 Profile & Mood", "🎵 AI Music", "🎧 Spotify Playlists"],
            index=0
        )
        
        # Display header image
        st.image("https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg", 
                use_column_width=True)
        
        # Show the selected page
        if page == "👤 Profile & Mood":
            await profile_page(user_profile, model)
        elif page == "🎵 AI Music":
            await ai_music_page(user_profile, model)
        elif page == "🎧 Spotify Playlists":
            await spotify_playlist_page(user_profile, sp_client, model)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    asyncio.run(main())
