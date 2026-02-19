import streamlit as st
import asyncio
from database import get_user_profile, save_user_profile, update_user_mood
from music import predict_favorite_genre
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
            
            insomnia = st.slider(
                "Insomnia Level",
                min_value=0,
                max_value=10,
                value=user_profile.get('Insomnia', 5),
                help="0 = No insomnia, 10 = Severe insomnia"
            )
            
            ocd = st.slider(
                "OCD Level",
                min_value=0,
                max_value=10,
                value=user_profile.get('OCD', 5),
                help="0 = No OCD, 10 = Severe OCD"
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
    st.markdown("---")
    st.header("🎵 Music Preferences Analysis")
    
    # Get model from session state
    model = st.session_state.get('model')
    if model:
        if st.button("Predict Your Favorite Genre", key="predict_genre_mood", type="primary"):
            with st.spinner('Analyzing your preferences...'):
                try:
                    genre = predict_favorite_genre(st.session_state.user_profile, st.session_state.model)
                    st.success(f"Based on your profile and current mood, your predicted favorite genre is: **{genre}**")
                    
                    # Show music recommendations based on profile and mood
                    st.info(f"💡 Try AI Music page to generate personalized {genre} tracks!")
                except Exception as e:
                    st.error(f"❌ Error predicting genre: {str(e)}")
    else:
        st.warning("Model not loaded. Please refresh the page.")

# Run the mood page
asyncio.run(current_mood_page())
