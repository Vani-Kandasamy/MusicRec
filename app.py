# app.py

import streamlit as st
from login import perform_login, session_logout
from database import get_user_profile, save_user_profile, create_initial_user_profile, display_stored_user_data
from music import predict_favorite_genre, get_spotify_playlist
import your_model_module  # Your ML model

IMAGE_ADDRESS = "https://cdn.punchng.com/wp-content/uploads/2022/03/28122921/Brain-Train-Blog-Image-2.jpg"

def run_app(user_email):
    st.title("Music for Mental Health")

    user_profile = get_user_profile(user_email)

    if user_profile:
        st.write("Welcome back!")
        display_stored_user_data(user_profile)
    else:
        st.write("Creating new profile...")
        user_profile = create_initial_user_profile()

    exploratory = st.slider("Openness to New Music", 0, 10, 5)
    anxiety = st.slider("Anxiety Level", 0, 10, 5)
    depression = st.slider("Depression Level", 0, 10, 5)
    insomnia = st.slider("Insomnia Level", 0, 10, 5)
    ocd = st.slider("OCD Level", 0, 10, 5)

    real_time_data = {
        "Exploratory": exploratory,
        "Anxiety": anxiety,
        "Depression": depression,
        "Insomnia": insomnia,
        "OCD": ocd

    }
    user_profile.update(real_time_data)

    fav_genre = predict_favorite_genre(user_profile, your_model_module)
    st.write(f"Predicted Favorite Genre: {fav_genre}")

    playlist_url = get_spotify_playlist(fav_genre)
    if playlist_url:
        st.write(f"Here's a {fav_genre} playlist: [Listen on Spotify]({playlist_url})")
    else:
        st.write("Couldn't find a playlist for this genre.")

def main():
    st.image(IMAGE_ADDRESS)

    user_email, user_name = perform_login()
    if user_email:
        st.write(f"Hello, <span style='color: orange; font-weight: bold;'>{user_name}</span>", unsafe_allow_html=True)
        if st.sidebar.button("Log out"):
            session_logout()
        run_app(user_email)
    else:
        st.sidebar.write("Please log in to use the app.")

if __name__ == "__main__":
    main()