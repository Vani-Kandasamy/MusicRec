import streamlit as st
import asyncio
from music import predict_favorite_genre, get_spotify_playlist
from datetime import datetime
from login import is_authenticated, show_login_page

# Set background color to match home page
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
""", unsafe_allow_html=True)

# Check authentication before showing page
if not is_authenticated():
    show_login_page()
else:
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
            
            if st.button("🎧 Get Spotify Playlist", key="get_spotify_playlist", type="primary"):
                with st.spinner('🎧 Finding your perfect playlist...'):
                    try:
                        playlist_url = get_spotify_playlist(predicted_genre)
                        
                        if playlist_url:
                            # Store in history
                            if 'playlist_history' not in st.session_state:
                                st.session_state.playlist_history = []
                            
                            st.session_state.playlist_history.append((predicted_genre, playlist_url, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            
                            st.success("✅ Playlist found! Click below to open.")
                            st.markdown(f"### 🎧 Your {predicted_genre} Playlist")
                            st.markdown(f"[Open Playlist]({playlist_url})")
                        else:
                            st.error("❌ No playlist found. Try a different genre.")
                    except Exception as e:
                        st.error(f"❌ Error getting playlist: {str(e)}")
        
        with col2:
            st.subheader("Playlist History")
            if 'playlist_history' not in st.session_state:
                st.session_state.playlist_history = []
            
            if st.session_state.playlist_history:
                for i, (genre, url, timestamp) in enumerate(st.session_state.playlist_history[-5:], 1):
                    st.write(f"{i}. [{genre}]({url}) - {timestamp}")
            else:
                st.write("No playlists generated yet.")
    
    # Get user data from session state
    if 'user_profile' in st.session_state and 'model' in st.session_state and 'sp_client' in st.session_state:
        asyncio.run(spotify_playlist_page(st.session_state.user_profile, st.session_state.sp_client, st.session_state.model))
    else:
        st.error("Please go to main page first to load your profile.")
