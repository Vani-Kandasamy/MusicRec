# music.py

import asyncio
import os
import aiofiles
import aiohttp
import nest_asyncio
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pydub import AudioSegment
import streamlit as st

# Allow asyncio to run nested within Streamlit
nest_asyncio.apply()

# Load Beatoven AI key from Streamlit secrets
BACKEND_V1_API_URL = "https://public-api.beatoven.ai/api/v1"
BACKEND_API_HEADER_KEY = st.secrets["BEATOVEN_API_KEY"]

# Configure Spotify API using credentials from Streamlit secrets
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"]
))
# Genre mapping: Model predictions to genres
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
    prediction = model.predict(user_profile)
    index = prediction if isinstance(prediction, int) and 0 <= prediction < len(GENRE_MAPPING) else 0
    return GENRE_MAPPING[index]

async def compose_track(request_data):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BACKEND_V1_API_URL}/tracks/compose",
            json=request_data,
            headers={"Authorization": f"Bearer {BACKEND_API_HEADER_KEY}"},
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("task_id")

async def get_track_status(task_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BACKEND_V1_API_URL}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {BACKEND_API_HEADER_KEY}"},
        ) as response:
            response.raise_for_status()
            return await response.json()

async def handle_track_file(file_path, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await response.read())
    sound = AudioSegment.from_wav(file_path)
    sound.export(file_path.replace('.wav', '.mp3'), format="mp3")

async def watch_task_status(task_id, file_path):
    while True:
        track_status = await get_track_status(task_id)
        if track_status["status"] == "completed":
            url = track_status["meta"]["track_url"]
            await handle_track_file(file_path, url)
            break
        elif track_status["status"] == "failed":
            st.error("Music generation failed.")
            break
        await asyncio.sleep(10)

async def create_and_compose(genre):
    track_meta = {
        "prompt": {
            "text": GENRE_PROMPTS.get(genre, "Compose a melody"),
            "genre": genre
        },
        "format": "wav"
    }
    task_id = await compose_track(track_meta)
    file_path = os.path.join(os.getcwd(), "composed_track.wav")
    await watch_task_status(task_id, file_path)
    st.success("Music composed successfully! Listen below.")
    st.audio("composed_track.mp3")

if st.button("Generate AI Music"):
    asyncio.run(create_and_compose(selected_genre))

st.subheader("Explore Spotify Playlists")
if st.button("Get Spotify Playlist"):
    playlist_url = get_spotify_playlist(selected_genre)
    if playlist_url:
        st.write(f"Here's a {selected_genre} playlist for you:")
        st.markdown(f"[Open Playlist]({playlist_url})")
    else:
        st.write(f"No {selected_genre} playlists found.")

def get_spotify_playlist(fav_genre):
    results = sp.search(q=fav_genre, type='playlist', limit=1)
    if results['playlists']['items']:
        playlist = random.choice(results['playlists']['items'])
        return playlist['external_urls']['spotify']
    return None