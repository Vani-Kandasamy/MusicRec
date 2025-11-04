# database.py

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os

def initialize_firestore():
    """Initialize Firestore with credentials from Streamlit secrets."""
    try:
        if not firebase_admin._apps:
            # Get Firebase config from Streamlit secrets
            firebase_config = st.secrets.get("firebase", {})
            
            if not firebase_config:
                raise ValueError("Firebase configuration not found in secrets.toml")
                
            # Required fields
            required_fields = [
                "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "client_x509_cert_url"
            ]
            
            # Validate required fields
            for field in required_fields:
                if field not in firebase_config:
                    raise ValueError(f"Missing required Firebase config: {field}")
            
            # Prepare the service account info
            service_account_info = {
                "type": "service_account",
                "project_id": firebase_config["project_id"],
                "private_key_id": firebase_config["private_key_id"],
                "private_key": firebase_config["private_key"].replace('\\n', '\n'),
                "client_email": firebase_config["client_email"],
                "client_id": firebase_config["client_id"],
                "auth_uri": firebase_config.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": firebase_config.get("token_uri", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": firebase_config.get(
                    "auth_provider_x509_cert_url", 
                    "https://www.googleapis.com/oauth2/v1/certs"
                ),
                "client_x509_cert_url": firebase_config["client_x509_cert_url"]
            }
            
            # Initialize Firebase
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            
        return firestore.client()
        
    except Exception as e:
        st.error(f"Failed to initialize Firestore: {str(e)}")
        st.stop()  # Stop execution if Firebase can't be initialized

# Initialize Firestore
try:
    db = initialize_firestore()
except Exception as e:
    st.error(f"Critical error initializing database: {str(e)}")
    raise

def get_user_profile(user_email):
    """Retrieve user profile from Firestore."""
    try:
        doc_ref = db.collection('users').document(user_email)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        st.error(f"Error fetching user profile: {e}")
        return None

def save_user_profile(user_email, user_data):
    try:
        doc_ref = db.collection('users').document(user_email)
        doc_ref.set(user_data)
        return True
    except Exception as e:
        st.error(f"Error saving user profile: {e}")
        return False
        
def update_user_mood(user_email, mood_data):
    """Update user's mood data in the database.
    
    Args:
        user_email (str): The email of the user
        mood_data (dict): Dictionary containing mood data to update
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        doc_ref = db.collection('users').document(user_email)
        # Use set with merge=True to create or update the document
        doc_ref.set(mood_data, merge=True)
        return True
    except Exception as e:
        st.error(f"Error updating mood data: {str(e)}")
        return False

def show_user_profile_form():
    """Display a form to collect user profile information with categorical options."""
    with st.form("user_profile_form"):
        st.subheader("Tell us about your music preferences")
        
        # Define options
        yes_no_options = ['Yes', 'No']
        music_effect_options = ['Improve', 'Not']
        frequency_options = ['Never', 'Rarely', 'Sometimes', 'Very frequently']
        
        # Basic Information
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=5, max_value=120, value=25, step=1)
            hours_per_day = st.number_input("Hours of music per day", min_value=0, max_value=24, value=2, step=1)
            while_working = st.selectbox("While working", ['Yes', 'No'])
        
        # Music Preferences
        st.markdown("### Music Listening Frequency")
        col1, col2 = st.columns(2)
        
        with col1:
            classical = st.selectbox("Classical", frequency_options, index=2)
            edm = st.selectbox("EDM", frequency_options, index=1)
            folk = st.selectbox("Folk", frequency_options, index=2)
            gospel = st.selectbox("Gospel", frequency_options, index=1)
            hiphop = st.selectbox("Hip Hop", frequency_options, index=3)
            jazz = st.selectbox("Jazz", frequency_options, index=2)
            
        with col2:
            kpop = st.selectbox("K-Pop", frequency_options, index=3)
            metal = st.selectbox("Metal", frequency_options, index=1)
            pop = st.selectbox("Pop", frequency_options, index=1)
            rb = st.selectbox("R&B", frequency_options, index=3)
            rock = st.selectbox("Rock", frequency_options, index=2)
            vgm = st.selectbox("Video Game Music", frequency_options, index=1)
        
        # Additional Information
        st.markdown("### Additional Information")
        col1, col2 = st.columns(2)
        with col1:
            instrumentalist = st.selectbox("Are you an instrumentalist?", ['No', 'Yes'])
        with col2:
            composer = st.selectbox("Are you a composer?", ['No', 'Yes'])
        
        exploratory = st.selectbox("Do you like exploring new music?", ['Yes', 'No'])
        foreign_languages = st.selectbox("Do you understand foreign languages?", ['No', 'Yes'])
        
        # Mood Initialization
        st.markdown("### Initial Mood Settings")
        st.info("Please set your current mood. You can update this later at any time.")
        
        col1, col2 = st.columns(2)
        with col1:
            openness = st.selectbox("Open to new experiences?", ['Yes', 'No'], 
                                 help="Are you open to trying new types of music?")
            anxiety = st.slider("Anxiety (1-10)", 1, 10, 5,
                             help="Your current anxiety level (1=low, 10=high)")
            depression = st.slider("Mood (1-10)", 1, 10, 5,
                                help="Your current mood (1=low, 10=high)")
        with col2:
            insomnia = st.slider("Sleep Quality (1-10)", 1, 10, 5,
                              help="Your recent sleep quality (1=poor, 10=excellent)")
            ocd = st.slider("Focus Level (1-10)", 1, 10, 5,
                          help="Your current ability to focus (1=poor, 10=excellent)")

        music_effect = st.selectbox("Does music affect your mood?", music_effect_options)
        bpm = st.slider("Preferred BPM (Beats Per Minute)", 60, 200, 120)

        if st.form_submit_button("Save Profile"):
            user_data = {
                'Age': age,
                'Hours per day': hours_per_day,
                'While working': while_working,
                'Frequency_Classical': classical,
                'Frequency_EDM': edm,
                'Frequency_Folk': folk,
                'Frequency_Gospel': gospel,
                'Frequency_HipHop': hiphop,
                'Frequency_Jazz': jazz,
                'Frequency_KPop': kpop,
                'Frequency_Metal': metal,
                'Frequency_Pop': pop,
                'Frequency_RnB': rb,
                'Frequency_Rock': rock,
                'Frequency_VGM': vgm,
                'Instrumentalist': instrumentalist,
                'Composer': composer,
                'Exploratory': 1 if exploratory == 'Yes' else 0,
                'ForeignLanguages': 1 if foreign_languages == 'Yes' else 0,
                'MusicEffects': music_effect,
                'BPM': bpm,
                # Mood data
                'Openness': 1 if openness == 'Yes' else 0,
                'Anxiety': anxiety,
                'Depression': depression,
                'Insomnia': insomnia,
                'OCD': ocd,
                'LastUpdated': datetime.now().isoformat(),
                'MoodLastUpdated': datetime.now().isoformat()
            }
            return user_data
    return None

def create_initial_user_profile(user_email):
    """Show the profile creation form and save the data."""
    st.info("Welcome! Please complete your profile to get started.")
    user_data = show_user_profile_form()
    if user_data:
        if save_user_profile(user_email, user_data):
            st.success("Profile saved successfully!")
            return user_data
        else:
            st.error("Failed to save profile. Please try again.")
    return None

def display_stored_user_data(user_profile):
    """Display the user's profile information with expandable sections and editable mood."""
    st.subheader("Your Profile")
    
    # Basic Information - Expandable section
    with st.expander("Basic Information", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Age", user_profile.get('Age', 'Not set'))
            st.metric("Instrumentalist", user_profile.get('Instrumentalist', 'Not set'))
        with col2:
            st.metric("Hours per day", user_profile.get('Hours per day', 'Not set'))
            st.metric("Composer", user_profile.get('Composer', 'Not set'))
    
    # Music Preferences - Expandable section
    with st.expander("Music Preferences", expanded=False):
        pref_columns = st.columns(4)
        genres = [
            ('Classical', ['Frequency_Classical', 'Classical']),
            ('EDM', ['Frequency_EDM', 'EDM']),
            ('Folk', ['Frequency_Folk', 'Folk']),
            ('Gospel', ['Frequency_Gospel', 'Gospel']),
            ('Hip Hop', ['Frequency_HipHop', 'Hip Hop', 'HipHop']),
            ('Jazz', ['Frequency_Jazz', 'Jazz']),
            ('K-Pop', ['Frequency_KPop', 'K-Pop', 'KPop']),
            ('Metal', ['Frequency_Metal', 'Metal']),
            ('Pop', ['Frequency_Pop', 'Pop']),
            ('R&B', ['Frequency_RnB', 'R&B', 'RnB']),
            ('Rock', ['Frequency_Rock', 'Rock']),
            ('Video Game Music', ['Frequency_VGM', 'Video Game Music', 'VGM'])
        ]
        
        for i, (display_name, possible_keys) in enumerate(genres):
            with pref_columns[i % 4]:
                # Try all possible key variations
                value = 'Not set'
                for key in possible_keys:
                    if key in user_profile:
                        value = user_profile[key]
                        break
                st.metric(display_name, value)
    
    st.markdown("### Current Mood")
    with st.form("mood_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Openness as Yes/No select box
            openness = st.selectbox(
                "Open to new experiences?",
                ['Yes', 'No'],
                index=0 if user_profile.get('Exploratory', 1) == 1 else 1,
                key="mood_openness"
            )
            anxiety = st.slider(
                "Anxiety (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Anxiety', 5)),
                key="mood_anxiety"
            )
            depression = st.slider(
                "Depression (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Depression', 5)),
                key="mood_depression"
            )
        
        with col2:
            insomnia = st.slider(
                "Insomnia (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('Insomnia', 5)),
                help="1 = No trouble sleeping, 10 = Severe insomnia",
                key="mood_insomnia"
            )
            ocd = st.slider(
                "OCD (1-10)", 
                min_value=1, 
                max_value=10, 
                value=int(user_profile.get('OCD', 5)),
                help="1 = No symptoms, 10 = Severe symptoms",
                key="mood_ocd"
            )
        
        # Save button for mood updates
        if st.form_submit_button("Update Mood"):
            # Get user email from the profile or session state
            user_email = user_profile.get('email') or (st.session_state.get('user_email') if 'user_email' in st.session_state else None)
            
            if not user_email:
                st.error("Could not determine user email. Please log in again.")
                return
                
            # Update the user profile with new mood values
            mood_update = {
                'Exploratory': 1 if openness == 'Yes' else 0,
                'Anxiety': anxiety,
                'Depression': depression,
                'Insomnia': insomnia,
                'OCD': ocd,
                'LastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update local profile
            user_profile.update(mood_update)
            
            # Save the updated profile
            if save_user_profile(user_email, user_profile):
                # Update session state if needed
                if 'user_info' in st.session_state and st.session_state.user_info is not None:
                    st.session_state.user_info.update(mood_update)
                st.success("Mood updated successfully!")
            else:
                st.error("Failed to update mood. Please try again.")
    
    # Last updated
    if 'LastUpdated' in user_profile:
        st.caption(f"Last updated: {user_profile['LastUpdated']}")
