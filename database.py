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
    """Update user's mood data in the database."""
    try:
        doc_ref = db.collection('users').document(user_email)
        doc_ref.update(mood_data)
        return True
    except Exception as e:
        st.error(f"Error updating mood data: {e}")
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
            classical = st.selectbox("Classical", frequency_options, index=2)  # Default to 'Sometimes'
            edm = st.selectbox("EDM", frequency_options, index=1)  # Default to 'Rarely'
            folk = st.selectbox("Folk", frequency_options, index=2)  # Default to 'Sometimes'
            gospel = st.selectbox("Gospel", frequency_options, index=1)  # Default to 'Rarely'
            hiphop = st.selectbox("Hip Hop", frequency_options, index=3)  # Default to 'Very frequently'
            jazz = st.selectbox("Jazz", frequency_options, index=2)  # Default to 'Sometimes'
            
        with col2:
            kpop = st.selectbox("K-Pop", frequency_options, index=3)  # Default to 'Very frequently'
            metal = st.selectbox("Metal", frequency_options, index=1)  # Default to 'Rarely'
            pop = st.selectbox("Pop", frequency_options, index=1)  # Default to 'Rarely'
            rb = st.selectbox("R&B", frequency_options, index=3)  # Default to 'Very frequently'
            rock = st.selectbox("Rock", frequency_options, index=2)  # Default to 'Sometimes'
            vgm = st.selectbox("Video Game Music", frequency_options, index=1)  # Default to 'Rarely'
        
        # Additional Information
        st.markdown("### Additional Information")
        col1, col2 = st.columns(2)
        with col1:
            instrumentalist = st.selectbox("Are you an instrumentalist?", ['No', 'Yes'])
        with col2:
            composer = st.selectbox("Are you a composer?", ['No', 'Yes'])
        
        exploratory = st.selectbox("Do you like exploring new music?", ['Yes', 'No'])
        foreign_languages = st.selectbox("Do you understand foreign languages?", ['No', 'Yes'])
        music_effect = st.selectbox("Does music affect your mood?", music_effect_options)
        
        bpm = st.slider("Preferred BPM (Beats Per Minute)", 60, 200, 120)
        
        submitted = st.form_submit_button("Save Profile")
        
        if submitted:
            # Encode categorical variables
            def encode_frequency(value):
                return frequency_options.index(value)
                
            def encode_yes_no(value):
                return 1 if value == 'Yes' else 0
            
            # Create user data with encoded values
            user_data = {
                'Age': age,
                'Hours per day': hours_per_day,
                'While working': encode_yes_no(while_working),
                'Instrumentalist': encode_yes_no(instrumentalist),
                'Composer': encode_yes_no(composer),
                'Exploratory': encode_yes_no(exploratory),
                'Foreign languages': encode_yes_no(foreign_languages),
                'BPM': bpm,
                # Music Frequencies with encoded values
                'Frequency [Classical]': encode_frequency(classical),
                'Frequency [EDM]': encode_frequency(edm),
                'Frequency [Folk]': encode_frequency(folk),
                'Frequency [Gospel]': encode_frequency(gospel),
                'Frequency [Hip hop]': encode_frequency(hiphop),
                'Frequency [Jazz]': encode_frequency(jazz),
                'Frequency [K pop]': encode_frequency(kpop),
                'Frequency [Metal]': encode_frequency(metal),
                'Frequency [Pop]': encode_frequency(pop),
                'Frequency [R&B]': encode_frequency(rb),
                'Frequency [Rock]': encode_frequency(rock),
                'Frequency [Video game music]': encode_frequency(vgm),
                # Music effect
                'Music effects': 0 if music_effect == 'Improve' else 1,
                # Metadata
                'LastUpdated': datetime.now().isoformat()
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
    """Display the user's profile information."""
    st.subheader("Your Profile")
    
    # Basic Information
    st.markdown("### Basic Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Age", user_profile.get('Age', 'Not set'))
        st.metric("Instrumentalist", user_profile.get('Instrumentalist', 'Not set'))
    with col2:
        st.metric("Hours per day", user_profile.get('Hours per day', 'Not set'))
        st.metric("Composer", user_profile.get('Composer', 'Not set'))
    
    # Music Preferences
    st.markdown("### Music Preferences")
    pref_columns = st.columns(4)
    genres = [
        ('Classical', 'Frequency_Classical'),
        ('EDM', 'Frequency_EDM'),
        ('Folk', 'Frequency_Folk'),
        ('Gospel', 'Frequency_Gospel'),
        ('Hip Hop', 'Frequency_HipHop'),
        ('Jazz', 'Frequency_Jazz'),
        ('K-Pop', 'Frequency_KPop'),
        ('Metal', 'Frequency_Metal'),
        ('Pop', 'Frequency_Pop'),
        ('R&B', 'Frequency_RnB'),
        ('Rock', 'Frequency_Rock'),
        ('Video Game Music', 'Frequency_VGM')
    ]
    
    for i, (display_name, key) in enumerate(genres):
        with pref_columns[i % 4]:
            st.metric(display_name, user_profile.get(key, 'N/A'))
    
    # Mood Settings
    st.markdown("### Current Mood")
    mood_cols = st.columns(5)
    with mood_cols[0]:
        st.metric("Openness", user_profile.get('Exploratory', 'N/A'))
    with mood_cols[1]:
        st.metric("Anxiety", user_profile.get('Anxiety', 'N/A'))
    with mood_cols[2]:
        st.metric("Depression", user_profile.get('Depression', 'N/A'))
    with mood_cols[3]:
        st.metric("Insomnia", user_profile.get('Insomnia', 'N/A'))
    with mood_cols[4]:
        st.metric("OCD", user_profile.get('OCD', 'N/A'))
    
    # Last updated
    if 'LastUpdated' in user_profile:
        st.caption(f"Last updated: {user_profile['LastUpdated']}")
    
    # Edit button
    if st.button("Edit Profile"):
        st.session_state.editing_profile = True
