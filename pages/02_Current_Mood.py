import streamlit as st
import asyncio
from database import get_user_profile, save_user_profile, update_user_mood
from music import predict_favorite_genre
from datetime import datetime

async def current_mood_page():
    """Display current mood management page."""
    st.title("😊 Current Mood Management")
    
    # Get user data from session state
    user = st.session_state.get('user')
    if not user:
        st.error("Please go to the main page first to load your profile.")
        return
    
    user_email = user['email']
    user_profile = get_user_profile(user_email)
    
    if not user_profile:
        st.error("User profile not found. Please complete your profile first.")
        return
    
    # Mood update form
    st.header("Update Your Mood")
    st.write("Track your current emotional state to get better music recommendations.")
    
    with st.form("mood_update_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Openness as Yes/No select box
            openness = st.selectbox(
                "Openness to new experiences",
                options=[1, 0],
                format_func=lambda x: "Yes" if x == 1 else "No",
                index=0 if user_profile.get('Exploratory', 1) == 1 else 1
            )
            
            # Mental Health Sliders
            anxiety = st.slider(
                "Anxiety Level",
                min_value=0,
                max_value=10,
                value=user_profile.get('Anxiety', 5),
                help="0 = No anxiety, 10 = Severe anxiety"
            )
            
            depression = st.slider(
                "Mood Level",
                min_value=0,
                max_value=10,
                value=user_profile.get('Depression', 5),
                help="0 = Very low mood, 10 = Excellent mood"
            )
        
        with col2:
            insomnia = st.slider(
                "Sleep Quality",
                min_value=0,
                max_value=10,
                value=user_profile.get('Insomnia', 5),
                help="0 = Excellent sleep, 10 = Very poor sleep"
            )
            
            ocd = st.slider(
                "Focus Level",
                min_value=0,
                max_value=10,
                value=user_profile.get('OCD', 5),
                help="0 = Excellent focus, 10 = Difficulty focusing"
            )
            
            # Additional mood factors
            music_effect = st.slider(
                "Music's Effect on Mood",
                min_value=0,
                max_value=10,
                value=user_profile.get('Music effects', 5),
                help="0 = No effect, 10 = Strong effect"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Update Mood", type="primary"):
                # Update mood data
                mood_data = {
                    'Exploratory': openness,
                    'Anxiety': anxiety,
                    'Depression': depression,
                    'Insomnia': insomnia,
                    'OCD': ocd,
                    'Music effects': music_effect,
                    'MoodLastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                user_profile.update(mood_data)
                
                if save_user_profile(user_email, user_profile):
                    st.session_state.user_profile = user_profile
                    st.success("✅ Mood updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update mood. Please try again.")
        
        with col2:
            if st.form_submit_button("Reset to Defaults"):
                # Reset to default values
                default_mood = {
                    'Exploratory': 1,
                    'Anxiety': 5,
                    'Depression': 5,
                    'Insomnia': 5,
                    'OCD': 5,
                    'Music effects': 5,
                    'MoodLastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                user_profile.update(default_mood)
                
                if save_user_profile(user_email, user_profile):
                    st.session_state.user_profile = user_profile
                    st.success("✅ Mood reset to defaults!")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset mood. Please try again.")
    
    # Music Preferences Analysis Section
    st.markdown("---")
    st.header("🎵 Music Preferences Analysis")
    
    # Get model from session state
    model = st.session_state.get('model')
    if model:
        if st.button("Predict Your Favorite Genre", key="predict_genre_mood", type="primary"):
            with st.spinner('Analyzing your preferences...'):
                try:
                    genre = predict_favorite_genre(user_profile, model)
                    st.success(f"Based on your profile and current mood, your predicted favorite genre is: **{genre}**")
                    
                    # Show music recommendations based on profile and mood
                    st.info(f"💡 Try AI Music page to generate personalized {genre} tracks!")
                except Exception as e:
                    st.error(f"❌ Error predicting genre: {str(e)}")
    else:
        st.warning("Model not loaded. Please refresh the page.")

# Run the mood page
asyncio.run(current_mood_page())
