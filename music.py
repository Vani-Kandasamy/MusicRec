import asyncio
import aiohttp
import nest_asyncio
import streamlit as st
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np

# Allow asyncio to run nested within Streamlit
nest_asyncio.apply()

# Configuration
BACKEND_V1_API_URL = "https://public-api.beatoven.ai/api/v1"

# Helper to safely get secrets
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except:
        return default

BEATOVEN_KEY = get_secret("BEATOVEN_API_KEY")

# Genre mapping and prompts
GENRE_MAPPING = ["Rock", "Pop", "Metal", "EDM", "Hip hop", "Classical", "Video game music", "R&B"]
GENRE_PROMPTS = {
    "Classical": "Compose a serene classical piano piece reminiscent of a peaceful afternoon in a garden.",
    "EDM": "Create an upbeat and energetic electronic dance track suitable for a vibrant festival atmosphere.",
    "Hip hop": "Generate a laid-back hip hop beat with a smooth rhythm and catchy bassline.",
    "Metal": "Produce a high-intensity metal track with fast guitar riffs and powerful drum beats.",
    "Pop": "Compose a catchy pop melody with an uplifting vibe and a memorable chorus.",
    "R&B": "Create a soulful R&B track with a slow groove and emotional vocal harmonies.",
    "Rock": "Generate a classic rock anthem with strong guitar chords and a steady, driving beat.",
    "Video game music": "Compose an adventurous theme suitable for an action-packed video game level."
}

def predict_favorite_genre(user_profile, model):
    """Predict the favorite music genre based on user profile using the provided model."""
    try:
        # Helper function to safely get and convert values to float32
        def get_feature(key, default=0):
            value = user_profile.get(key, default)
            
            # Handle None values
            if value is None:
                return float(default)
                
            # Convert to string for consistent handling
            if not isinstance(value, str):
                value = str(value)
                
            # Convert string numbers to float
            if value.replace('.', '').isdigit():
                return float(value)
                
            # Handle yes/no fields
            if value.lower() in ['yes', 'no']:
                return 1.0 if value.lower() == 'yes' else 0.0
                
            # Handle frequency strings (Never, Rarely, Sometimes, Very frequently)
            freq_map = {
                'never': 0.0,
                'rarely': 1.0,
                'sometimes': 2.0,
                'very frequently': 3.0
            }
            if value.lower() in freq_map:
                return freq_map[value.lower()]
                
            # Default case - try to convert to float, fallback to default
            try:
                return float(value)
            except (ValueError, TypeError):
                return float(default)
        
        # Prepare the input features for the model
        input_features = [
            float(get_feature('Age', 25)),
            float(get_feature('Hours per day', 2)),
            float(1 if str(user_profile.get('While working', 'No')).lower() == 'yes' else 0),
            float(1 if str(user_profile.get('Instrumentalist', 'No')).lower() == 'yes' else 0),
            float(1 if str(user_profile.get('Composer', 'No')).lower() == 'yes' else 0),
            float(1 if str(user_profile.get('Exploratory', 'No')).lower() == 'yes' else 0),
            float(1 if str(user_profile.get('Foreign languages', 'No')).lower() == 'yes' else 0),
            float(get_feature('BPM', 120)),
            # Handle both Frequency_Genre and Frequency [Genre] formats
            float(get_feature('Frequency_Classical', get_feature('Frequency [Classical]', 2))),
            float(get_feature('Frequency_EDM', get_feature('Frequency [EDM]', 2))),
            float(get_feature('Frequency_Folk', get_feature('Frequency [Folk]', 2))),
            float(get_feature('Frequency_Gospel', get_feature('Frequency [Gospel]', 2))),
            float(get_feature('Frequency_HipHop', get_feature('Frequency [Hip hop]', 2))),
            float(get_feature('Frequency_Jazz', get_feature('Frequency [Jazz]', 2))),
            float(get_feature('Frequency_KPop', get_feature('Frequency [K pop]', 2))),
            float(get_feature('Frequency_Metal', get_feature('Frequency [Metal]', 2))),
            float(get_feature('Frequency_Pop', get_feature('Frequency [Pop]', 2))),
            float(get_feature('Frequency_RnB', get_feature('Frequency [R&B]', 2))),
            float(get_feature('Frequency_Rock', get_feature('Frequency [Rock]', 2))),
            float(get_feature('Frequency_VGM', get_feature('Frequency [Video game music]', 2))),
            float(get_feature('Anxiety', 5)),
            float(get_feature('Depression', 5)),
            float(get_feature('Insomnia', 5)),
            float(get_feature('OCD', 5)),
            float(1 if str(user_profile.get('MusicEffects', 'No')).lower() == 'improve' else 0)
        ]
        
        # Ensure all features are float32 and in a 2D numpy array
        import numpy as np
        input_array = np.array([input_features], dtype=np.float32)
        
        # Get prediction from the model
        prediction = model.predict(input_array)
        
        # Ensure prediction is an integer index
        index = int(prediction[0]) if len(prediction) > 0 else 0
        index = max(0, min(index, len(GENRE_MAPPING) - 1))  # Ensure valid index
        
        return GENRE_MAPPING[index]
        
    except Exception:
        return "Pop"

async def get_spotify_playlist(genre, sp_client=None):
    """Fetch a random Spotify playlist for the given genre.
    
    Args:
        genre (str): The music genre to search for
        sp_client: Optional Spotify client instance. If not provided, will try to initialize one.
    """
    try:
        if sp_client is None:
            if not hasattr(st, 'secrets') or not st.secrets.get("SPOTIFY_CLIENT_ID"):
                st.error("❌ Spotify API credentials not configured.")
                return None
            sp_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=st.secrets['music']["SPOTIFY_CLIENT_ID"],
                client_secret=st.secrets['music']["SPOTIFY_CLIENT_SECRET"]
            ))
            
        results = sp_client.search(q=genre, type='playlist', limit=5)
        if not results or 'playlists' not in results or not results['playlists']['items']:
            st.error("❌ No playlists found for this genre. Please try another genre.")
            return None
            
        playlist = random.choice(results['playlists']['items'])
        return playlist['external_urls']['spotify']
        
    except Exception:
        return None

# --- API FUNCTIONS ---

async def compose_track(genre):
    """Initializes the composition task with Beatoven."""
    headers = {"Authorization": f"Bearer {BEATOVEN_KEY}", "Content-Type": "application/json"}
    payload = {
        "prompt": {
            "text": GENRE_PROMPTS.get(genre, "Upbeat music"),
            "genre": genre.lower() if genre != "Video game music" else "electronic"
        },
        "format": "wav",
        "looping": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BACKEND_V1_API_URL}/tracks/compose", json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_data = await resp.text()
                    st.error(f"Beatoven API Error ({resp.status}): {error_data}")
                    return None
                data = await resp.json()
                return data.get("task_id")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            return None

async def watch_task_status(task_id):
    """Polls the task status until completion or failure."""
    headers = {"Authorization": f"Bearer {BEATOVEN_KEY}"}
    status_display = st.empty()
    
    # Poll for up to 5 minutes (30 checks * 10 seconds)
    for attempt in range(30):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{BACKEND_V1_API_URL}/tasks/{task_id}", headers=headers) as resp:
                    data = await resp.json()
                    status = data.get("status")
                    
                    status_display.info(f"🎵 AI is composing... Status: **{status}** (Attempt {attempt+1}/30)")
                    
                    if status == "composed":
                        track_url = data.get("meta", {}).get("track_url")
                        status_display.empty()
                        return track_url
                    elif status == "failed":
                        status_display.error("❌ Beatoven failed to compose this track.")
                        return None
            except Exception as e:
                st.warning(f"Polling error: {e}")
        
        await asyncio.sleep(10) # Wait 10 seconds before next check
    
    status_display.error("⌛ Composition timed out.")
    return None

# --- UI LOGIC ---

async def create_and_compose(genre):
    st.title("🎸 AI Music Generator")
    
    if not BEATOVEN_KEY:
        st.error("Missing `BEATOVEN_API_KEY` in secrets.")
        return
      
    try:
        # Run the async orchestration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        with st.spinner("Initializing AI..."):
            task_id = loop.run_until_complete(compose_track(genre))
        
        if task_id:
            track_url = loop.run_until_complete(watch_task_status(task_id))
            if track_url:
                st.success("✨ Your track is ready!")
                st.audio(track_url)
                st.download_button("Download Track", track_url)
    
    except Exception:
        return False

