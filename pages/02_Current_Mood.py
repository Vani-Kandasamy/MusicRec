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
    st.title("😊 Current Mood Management")
    
    user = st.session_state.get('user')
    if not user:
        st.error("Please load your profile first.")
    else:
        user_email = user['email']
        user_profile = get_user_profile(user_email) or {}

        st.header("Update Your Mood")
        
        with st.form("mood_update_form"):
            # We use int() to make sure Streamlit gets the right data type
            openness = st.selectbox(
                "Openness to new experiences",
                options=[1, 0],
                format_func=lambda x: "Yes" if x == 1 else "No",
                index=0 if int(user_profile.get('Exploratory', 1)) == 1 else 1
            )

            anxiety = st.slider("Anxiety Level", 0, 10, value=int(user_profile.get('Anxiety', 5)))
            
            depression = st.slider("Depression Level", 0, 10, value=int(user_profile.get('Depression', 5)))
            
            insomnia = st.slider("Insomnia Level", 0, 10, value=int(user_profile.get('Insomnia', 5)))
            
            ocd = st.slider("OCD Level", 0, 10, value=int(user_profile.get('OCD', 5)))
            
            
            music_effect = st.slider(
                "Music's Effect on Mood", 
                min_value=0, 
                max_value=10, 
                value=int(user_profile.get('MusicEffects', 5))
            )

            submitted = st.form_submit_button("Update Mood", type="primary")

            if submitted:
                mood_data = {
                    'Exploratory': openness,
                    'Anxiety': anxiety,
                    'Depression': depression,
                    'Insomnia': insomnia,
                    'OCD': ocd,
                    'MusicEffects': music_effect,
                    'MoodLastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                user_profile.update(mood_data)
                if save_user_profile(user_email, user_profile):
                    st.success("✅ Mood updated!")
                    st.rerun()
                    
                else:
                    st.error("❌ Failed to update mood.")
            # --- END OF THE FORM ---
                        
    st.markdown("---")
    
    # Mental Health Resources Section
    st.header("🧠 Mental Health Resources & Information")
    st.write("Understanding mental health conditions can help you better track your mood and seek appropriate support when needed.")
    
    with st.expander("📘 Understanding Anxiety"):
        st.markdown("""
        **What to look for:**
        - Excessive worry or fear about everyday situations
        - Feeling restless or on edge
        - Difficulty concentrating or mind going blank
        - Physical symptoms: rapid heartbeat, sweating, trembling
        - Sleep disturbances and fatigue
        
        **When to seek help:**
        - If anxiety interferes with daily activities
        - If you experience panic attacks
        - If symptoms persist for more than a few weeks
        
        **Helpful resources:**
        - National Alliance on Mental Illness (NAMI): 1-800-950-NAMI
        - Anxiety and Depression Association of America (ADAA)
        - Crisis Text Line: Text HOME to 741741
        """)
    
    with st.expander("📘 Understanding Depression"):
        st.markdown("""
        **What to look for:**
        - Persistent sad, anxious, or empty mood
        - Loss of interest or pleasure in activities
        - Changes in appetite or weight
        - Sleep disturbances (too much or too little)
        - Fatigue and decreased energy
        - Feelings of worthlessness or guilt
        - Difficulty concentrating or making decisions
        
        **When to seek help:**
        - If symptoms last more than two weeks
        - If you have thoughts of self-harm
        - If depression affects work, school, or relationships
        
        **Helpful resources:**
        - National Suicide Prevention Lifeline: 988
        - Depression and Bipolar Support Alliance (DBSA)
        - Mental Health America (MHA)
        """)
    
    with st.expander("📘 Understanding Insomnia"):
        st.markdown("""
        **What to look for:**
        - Difficulty falling asleep
        - Waking up frequently during the night
        - Waking up too early and unable to fall back asleep
        - Feeling tired upon waking
        - Daytime fatigue or sleepiness
        - Irritability or concentration problems
        
        **When to seek help:**
        - If insomnia occurs at least 3 nights per week for 3 months
        - If it significantly impacts your daily functioning
        - If you've tried sleep hygiene without improvement
        
        **Helpful resources:**
        - National Sleep Foundation
        - American Academy of Sleep Medicine
        - Sleep Education by the AASM
        """)
    
    with st.expander("📘 Understanding OCD (Obsessive-Compulsive Disorder)"):
        st.markdown("""
        **What to look for:**
        **Obsessions:**
        - Unwanted, intrusive thoughts or images
        - Fear of contamination or germs
        - Need for symmetry or exactness
        - Forbidden thoughts about harm or religion
        
        **Compulsions:**
        - Excessive cleaning or handwashing
        - Repeating actions (checking, counting)
        - Arranging items in specific patterns
        - Mental rituals (praying, counting silently)
        
        **When to seek help:**
        - If obsessions/compulsions take more than 1 hour daily
        - If they significantly impact your quality of life
        - If you can't control the behaviors
        
        **Helpful resources:**
        - International OCD Foundation (IOCDF)
        - OCD Action
        - Made of Millions Foundation
        """)
    
    st.info("💡 **Note:** This information is for educational purposes only. If you're experiencing severe symptoms or having thoughts of self-harm, please contact a healthcare professional or emergency services immediately.")
    
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
                    st.error(f"Error predicting genre: {str(e)}")
    else:
        st.warning("Model not loaded. Please refresh the page.")
