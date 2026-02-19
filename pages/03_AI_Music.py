import streamlit as st
import asyncio
from music import predict_favorite_genre, create_and_compose
from datetime import datetime
from login_simple import is_authenticated, show_login_page

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
    async def ai_music_page(user_profile, model):
        """Display AI-generated music page."""
        st.title("🎵 AI-Generated Music")
        
    # Show user's predicted genre
    try:
        predicted_genre = predict_favorite_genre(user_profile, model)
        st.info(f"Your predicted favorite genre: **{predicted_genre}**")
    except Exception as e:
        predicted_genre = "Pop"
        st.warning(f"Could not predict genre: {str(e)}. Using default: {predicted_genre}")
        
        # Music generation section
        st.header("Generate Personalized Music")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Generate a unique AI-composed track based on your mood and preferences.")
        
        if st.button("🎼 Generate AI Music", key="generate_ai_music", type="primary"):
            with st.spinner('🎵 Composing your personalized music...'):
                try:
                    success = create_and_compose(predicted_genre)
                    if success:
                        # Store in history
                        if 'music_history' not in st.session_state:
                            st.session_state.music_history = []
                        st.session_state.music_history.append((predicted_genre, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        
                        st.success("✅ Music generated successfully! Check the player above.")
                    else:
                        st.error("❌ Failed to generate music. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error generating music: {str(e)}")
    
    with col2:
        st.subheader("Music History")
        if 'music_history' not in st.session_state:
            st.session_state.music_history = []
        
        if st.session_state.music_history:
            for i, (genre, timestamp) in enumerate(st.session_state.music_history[-5:], 1):
                st.write(f"{i}. {genre} - {timestamp}")
        else:
            st.write("No music generated yet.")

# Get user data from session state
if 'user_profile' in st.session_state and 'model' in st.session_state:
    asyncio.run(ai_music_page(st.session_state.user_profile, st.session_state.model))
else:
    st.error("Please go to the main page first to load your profile.")
