import streamlit as st
import asyncio
from database import display_stored_user_data

async def profile_page(user_profile, model):
    """Display user profile page."""
    st.title("👤 Your Profile")
    
    # Display user profile information (without mood section)
    display_stored_user_data(user_profile)
    
    # Quick navigation to mood page
    st.markdown("---")
    st.info("📊 **Want to update your current mood or analyze music preferences?** Navigate to 'Current Mood' page to track your emotional state and get personalized music recommendations.")

# Get user data from session state
if 'user_profile' in st.session_state and 'model' in st.session_state:
    asyncio.run(profile_page(st.session_state.user_profile, st.session_state.model))
else:
    st.error("Please go to main page first to load your profile.")
