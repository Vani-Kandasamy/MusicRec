import streamlit as st
import asyncio
from music import predict_favorite_genre
from database import display_stored_user_data

async def profile_page(user_profile, model):
    """Display user profile page."""
    st.title("👤 Your Profile")
    
    # Display user profile information (without mood section)
    display_stored_user_data(user_profile)
    
    # Show predicted genre
    st.markdown("---")
    st.header("Music Preferences Analysis")
    
    if st.button("Predict Your Favorite Genre", key="predict_genre_profile", type="primary"):
        with st.spinner('Analyzing your preferences...'):
            try:
                genre = predict_favorite_genre(user_profile, model)
                st.success(f"Based on your profile, your predicted favorite genre is: **{genre}**")
                
                # Show music recommendations based on profile
                st.info(f"💡 Try AI Music page to generate personalized {genre} tracks!")
            except Exception as e:
                st.error(f"❌ Error predicting genre: {str(e)}")
    
    # Quick navigation to mood page
    st.markdown("---")
    st.info("📊 **Want to update your current mood?** Navigate to 'Current Mood' page to track your emotional state for better music recommendations.")

# Get user data from session state
if 'user_profile' in st.session_state and 'model' in st.session_state:
    asyncio.run(profile_page(st.session_state.user_profile, st.session_state.model))
else:
    st.error("Please go to main page first to load your profile.")
