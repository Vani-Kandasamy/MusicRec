# music.py

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import streamlit as st


# Initialize Spotify API using credentials stored in secrets.toml
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"]
))

# Genre mapping: Model predictions to genres
genre_mapping = [
    "Rock",
    "Pop",
    "Metal",
    "EDM",
    "Hip hop",
    "Classical",
    "Video game music",
    "R&B"
]

def predict_favorite_genre(user_profile, model):
    prediction = model.predict(user_profile)
    index = prediction if isinstance(prediction, int) and 0 <= prediction < len(genre_mapping) else 0
    return genre_mapping[index]

def get_spotify_playlist(fav_genre):
    results = sp.search(q=fav_genre, type='playlist', limit=1)
    if results['playlists']['items']:
        playlist = random.choice(results['playlists']['items'])
        return playlist['external_urls']['spotify']
    else:
        return None