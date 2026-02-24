# music.py

import asyncio
import os
import wave
import streamlit as st
import random
import numpy as np
from io import BytesIO
from datetime import datetime, timedelta
import time
import google.generativeai as genai
from google.generativeai import types

# Allow asyncio to run nested within Streamlit
nest_asyncio.apply()

# Load Lyria API key from Streamlit secrets
API_KEY = st.secrets.get("LYRIA_API_KEY")
MODEL_ID = "models/lyria-v1"

if not API_KEY:
    st.error("❌ Lyria API key is not configured. Please check your secrets.toml file.")

# Initialize Lyria client
client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})

# Genre mapping and prompts
GENRE_MAPPING = [
    "Rock", "Pop", "Metal", "EDM", "Hip hop", "Classical", "Video game music", "R&B"
]

GENRE_PROMPTS = {
    "Classical": "Compose a serene classical piano piece reminiscent of a peaceful afternoon in a garden.",
    "EDM": "Create an upbeat and energetic electronic dance track suitable for a vibrant festival atmosphere.",
    "Hip hop": "Generate a laid-back hip hop beat with a smooth rhythm and catchy bassline, perfect for a chill evening.",
    "Metal": "Produce a high-intensity metal track with fast guitar riffs and powerful drum beats.",
    "Pop": "Compose a catchy pop melody with an uplifting vibe and a memorable chorus.",
    "R&B": "Create a soulful R&B track with a slow groove and emotional vocal harmonies.",
    "Rock": "Generate a classic rock anthem with strong guitar chords and a steady, driving beat.",
    "Video game music": "Compose an adventurous and dynamic theme suitable for an action-packed video game level."
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
        
        # Debug: Print prediction and features
        st.write(f"Debug: Raw prediction = {prediction}")
        st.write(f"Debug: Input features = {input_features}")
        
        # Ensure prediction is an integer index
        index = int(prediction[0]) if len(prediction) > 0 else 0
        index = max(0, min(index, len(GENRE_MAPPING) - 1))  # Ensure valid index
        
        predicted_genre = GENRE_MAPPING[index]
        
        # Debug: Print final result
        st.write(f"Debug: Index = {index}, Predicted Genre = {predicted_genre}")
        
        return predicted_genre
        
    except Exception:
        return "Pop"

async def generate_genre_track(genre_name, duration_seconds=10):
    """Generate a music track using Lyria AI for the specified genre."""
    prompt_text = GENRE_PROMPTS.get(genre_name)
    if not prompt_text:
        st.error(f"Genre {genre_name} not found.")
        return None

    filename = f"{genre_name.replace(' ', '_')}_track.wav"
    
    try:
        # Lyria outputs 48kHz Stereo 16-bit PCM
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)

            async with client.aio.live.music.connect(model=MODEL_ID) as session:
                st.write(f"🎵 Generating {genre_name}...")
                
                # Set the musical style (Weighted prompts allow blending later)
                await session.set_weighted_prompts(
                    prompts=[types.WeightedPrompt(text=prompt_text, weight=1.0)]
                )

                # Optional: Add specific BPM or Brightness for the genre
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(brightness=0.6)
                )

                await session.play()

                # Each chunk is roughly 2 seconds
                chunks_to_get = duration_seconds // 2
                received = 0
                
                async for message in session.receive():
                    if message.server_content.audio_chunks:
                        wf.writeframes(message.server_content.audio_chunks[0].data)
                        received += 1
                    
                    if received >= chunks_to_get:
                        break
                
                st.success(f"✅ {genre_name} generation complete.")

        # Display audio in Streamlit
        st.audio(filename, format='audio/wav')
        return filename
        
    except Exception as e:
        st.error(f"❌ Error generating {genre_name} track: {str(e)}")
        return None

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
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
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

async def create_and_compose(genre):
    """Create and compose a new track of the specified genre using Lyria."""
    if not API_KEY:
        st.error("❌ Music generation is not available. Missing Lyria API key.")
        return False

    try:
        with st.spinner('🎵 Composing your personalized music...'):
            filename = await generate_genre_track(genre, duration_seconds=10)
            if filename:
                st.success("✅ Music generated successfully!")
                return True
            else:
                st.error("Failed to generate music.")
                return False
    except Exception as e:
        st.error(f"❌ Error in music generation: {str(e)}")
        return False
