# music.py

import asyncio
import os
import aiofiles
import aiohttp
import nest_asyncio
import soundfile as sf
import streamlit as st
import random


import ffmpeg
from io import BytesIO
from datetime import datetime, timedelta

import time

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Allow asyncio to run nested within Streamlit
nest_asyncio.apply()

# Load Beatoven AI key from Streamlit secrets
BACKEND_V1_API_URL = "https://public-api.beatoven.ai/api/v1"
BACKEND_API_HEADER_KEY = st.secrets.get("BEATOVEN_API_KEY")

if not BACKEND_API_HEADER_KEY:
    st.error("❌ Beatoven API key is not configured. Please check your secrets.toml file.")

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
        # Prepare the input features for the model
        input_features = [
            user_profile.get('Age', 25),
            user_profile.get('Hours per day', 2),
            user_profile.get('While working', 0),
            user_profile.get('Instrumentalist', 0),
            user_profile.get('Composer', 0),
            user_profile.get('Exploratory', 0),  # Binary (0 or 1)
            user_profile.get('Foreign languages', 0),
            user_profile.get('BPM', 120),
            user_profile.get('Frequency [Classical]', 2),
            user_profile.get('Frequency [EDM]', 2),
            user_profile.get('Frequency [Folk]', 2),
            user_profile.get('Frequency [Gospel]', 2),
            user_profile.get('Frequency [Hip hop]', 2),
            user_profile.get('Frequency [Jazz]', 2),
            user_profile.get('Frequency [K pop]', 2),
            user_profile.get('Frequency [Metal]', 2),
            user_profile.get('Frequency [Pop]', 2),
            user_profile.get('Frequency [R&B]', 2),
            user_profile.get('Frequency [Rock]', 2),
            user_profile.get('Frequency [Video game music]', 2),
            user_profile.get('Anxiety', 5),
            user_profile.get('Depression', 5),
            user_profile.get('Insomnia', 5),
            user_profile.get('OCD', 5),
            user_profile.get('Music effects', 0)
        ]
        
        # Get prediction from the model
        prediction = model.predict([input_features])
        
        index = prediction if isinstance(prediction, int) and 0 <= prediction < len(GENRE_MAPPING) else 0
        
        return GENRE_MAPPING[index]
        
    except Exception as e:
        st.error(f"❌ Error predicting genre: {str(e)}")
        raise  # Re-raise the exception to handle it in the calling function

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
                client_id=st.secrets["SPOTIFY_CLIENT_ID"],
                client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"]
            ))
            
        results = sp_client.search(q=genre, type='playlist', limit=5)
        if not results or 'playlists' not in results or not results['playlists']['items']:
            st.error("❌ No playlists found for this genre. Please try another genre.")
            return None
            
        playlist = random.choice(results['playlists']['items'])
        return playlist['external_urls']['spotify']
        
    except Exception as e:
        st.error(f"❌ Failed to fetch Spotify playlist: {str(e)}")
        return None

async def compose_track(request_data):
    """Send request to compose a new track."""
    try:
        if not BACKEND_API_HEADER_KEY:
            raise ValueError("Beatoven API key not configured")
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_V1_API_URL}/tracks/compose",
                json=request_data,
                headers={"Authorization": f"Bearer {BACKEND_API_HEADER_KEY}"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                data = await response.json()
                return data.get("task_id")
    except asyncio.TimeoutError:
        st.error("❌ Request to music generation service timed out.")
        return None
    except Exception as e:
        st.error(f"❌ Error in compose_track: {str(e)}")
        return None

async def get_track_status(task_id):
    """Check the status of a track composition."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BACKEND_V1_API_URL}/tasks/{task_id}",
                headers={"Authorization": f"Bearer {BACKEND_API_HEADER_KEY}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        st.error(f"❌ Error checking track status: {str(e)}")
        return {"status": "failed"}

async def handle_track_file_in_memory(url):
    """Download and convert the generated track for direct playback."""
    try:
        # Download the WAV data into memory
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                wav_data = await response.read()

        # Use ffmpeg to convert WAV to MP3 in memory
        input_buffer = BytesIO(wav_data)
        input_buffer.seek(0)

        output_buffer = BytesIO()
        stream = (
            ffmpeg
            .input('pipe:0', format='wav')
            .output('pipe:1', format='mp3')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )
        out, err = stream.communicate(input=input_buffer.read())
        output_buffer.write(out)
        output_buffer.seek(0)

        return output_buffer

    except Exception as e:
        st.error(f"❌ Error processing audio file: {str(e)}")
        return None

async def watch_task_status(task_id):
    """Monitor the status of a track generation task."""
    try:
        while True:
            track_status = await get_track_status(task_id)
            if track_status["status"] == "completed":
                url = track_status["meta"]["track_url"]
                mp3_buffer = await handle_track_file_in_memory(url)
                if mp3_buffer:
                    st.audio(mp3_buffer.read(), format='audio/mp3')
                    st.success("✅ Music generated successfully!")
                break
            elif track_status["status"] == "failed":
                st.error("Music generation failed.")
                break
            await asyncio.sleep(10)
    except Exception as e:
        st.error(f"❌ Error monitoring task: {str(e)}")

async def create_and_compose(genre):
    """Create and compose a new track of the specified genre."""
    if not BACKEND_API_HEADER_KEY:
        st.error("❌ Music generation is not available. Missing API key.")
        return False

    try:
        with st.spinner('🎵 Composing your personalized music...'):
            track_meta = {
                "prompt": {
                    "text": GENRE_PROMPTS.get(genre, "Compose a melody"),
                    "genre": genre
                },
                "format": "wav"
            }

            task_id = await compose_track(track_meta)
            if not task_id:
                st.error("Failed to start music generation.")
                return False

            await watch_task_status(task_id)
            return True

    except Exception as e:
        st.error(f"❌ Error generating music: {str(e)}")
        st.info("💡 Tip: Check your internet connection and API key if this error persists.")
        return False
