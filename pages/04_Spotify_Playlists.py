import streamlit as st
import asyncio
from music import predict_favorite_genre, get_spotify_playlist
from datetime import datetime

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

# Get user data from session state
if 'user_profile' in st.session_state and 'model' in st.session_state and 'sp_client' in st.session_state:
    asyncio.run(spotify_playlist_page(st.session_state.user_profile, st.session_state.sp_client, st.session_state.model))
else:
    st.error("Please go to the main page first to load your profile.")
