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
    
    # Current mood overview
    st.header("Your Current Mood Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        anxiety = user_profile.get('Anxiety', 5)
        st.metric("Anxiety Level", f"{anxiety}/10")
    
    with col2:
        depression = user_profile.get('Depression', 5)
        st.metric("Mood Score", f"{depression}/10")
    
    with col3:
        insomnia = user_profile.get('Insomnia', 5)
        st.metric("Sleep Quality", f"{insomnia}/10")
    
    st.markdown("---")
    
    # Mood update form
    st.header("Update Your Mood")
    st.write("Track your current emotional state to get better music recommendations.")
    
    with st.form("mood_update_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Openness as Yes/No select box
            openness = st.selectbox(
                "Open to new experiences?",
                ['Yes', 'No'],
                index=0 if user_profile.get('Exploratory', 1) == 1 else 1,
                key="mood_openness",
                help="Are you open to trying new types of music?"
            )
            anxiety = st.slider(
                "Anxiety Level (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Anxiety', 5)),
                key="mood_anxiety",
                help="1 = Very calm, 10 = Very anxious"
            )
            depression = st.slider(
                "Mood Level (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Depression', 5)),
                key="mood_depression",
                help="1 = Very low mood, 10 = Very high mood"
            )
        
        with col2:
            insomnia = st.slider(
                "Sleep Quality (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Insomnia', 5)),
                help="1 = Excellent sleep, 10 = Very poor sleep",
                key="mood_insomnia"
            )
            ocd = st.slider(
                "Focus Level (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('OCD', 5)),
                help="1 = Very focused, 10 = Very distracted",
                key="mood_ocd"
            )
        
        # Save button for mood updates
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("Update Mood", type="primary"):
                # Update the user profile with new mood values
                mood_update = {
                    'Exploratory': 1 if openness == 'Yes' else 0,
                    'Anxiety': anxiety,
                    'Depression': depression,
                    'Insomnia': insomnia,
                    'OCD': ocd,
                    'MoodLastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Update local profile
                user_profile.update(mood_update)
                
                # Save the updated profile
                if save_user_profile(user_email, user_profile):
                    # Update session state
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
                    'MoodLastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                user_profile.update(default_mood)
                
                if save_user_profile(user_email, user_profile):
                    st.session_state.user_profile = user_profile
                    st.success("✅ Mood reset to defaults!")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset mood. Please try again.")
    
    st.markdown("---")
    
    # Mood history and insights
    st.header("Mood Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Music Recommendations Based on Mood")
        
        # Provide recommendations based on current mood
        anxiety_level = user_profile.get('Anxiety', 5)
        mood_level = user_profile.get('Depression', 5)
        sleep_quality = user_profile.get('Insomnia', 5)
        
        if anxiety_level > 7:
            st.info("🎵 **High Anxiety**: Try calming Classical or Jazz music")
        elif mood_level < 4:
            st.info("🎵 **Low Mood**: Consider uplifting Pop or Rock music")
        elif sleep_quality > 7:
            st.info("🎵 **Poor Sleep**: Try soothing Ambient or Classical music")
        else:
            st.info("🎵 **Balanced Mood**: Explore your predicted favorite genre!")
    
    with col2:
        st.subheader("Mood Tracking Tips")
        st.write("• Update your mood daily for better recommendations")
        st.write("• Be honest about your emotional state")
        st.write("• Track patterns in your mood changes")
        st.write("• Use music to help manage your mood")
    
    # Last updated info
    if 'MoodLastUpdated' in user_profile:
        st.caption(f"Last mood update: {user_profile['MoodLastUpdated']}")
    
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
    
    # Show current mood-based recommendations
    st.subheader("Current Mood-Based Recommendations")
    
    anxiety_level = user_profile.get('Anxiety', 5)
    mood_level = user_profile.get('Depression', 5)
    sleep_quality = user_profile.get('Insomnia', 5)
    
    if anxiety_level > 7:
        st.info("🎵 **High Anxiety**: Try calming Classical or Jazz music")
    elif mood_level < 4:
        st.info("🎵 **Low Mood**: Consider uplifting Pop or Rock music")
    elif sleep_quality > 7:
        st.info("🎵 **Poor Sleep**: Try soothing Ambient or Classical music")
    else:
        st.info("🎵 **Balanced Mood**: Explore your predicted favorite genre!")

# Run the mood page
asyncio.run(current_mood_page())
