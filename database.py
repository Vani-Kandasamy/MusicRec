# database.py

import firebase_admin
from firebase_admin import credentials, firestore
import json
import streamlit as st

# Initialize Firestore using credentials from secrets
if not firebase_admin._apps:
    firebase_creds_json = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    firebase_creds = credentials.Certificate(firebase_creds_json)
    firebase_admin.initialize_app(firebase_creds)

db = firestore.client()

def get_user_profile(user_email):
    doc_ref = db.collection('users').document(user_email)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None

def save_user_profile(user_email, user_data):
    doc_ref = db.collection('users').document(user_email)
    doc_ref.set(user_data)

def create_initial_user_profile():
    return {
        "Age": 25,
        "Instrumentalist": "No",
        "Composer": "No",
        "Hours per day": 2,
        "While working": "Yes",
        "Frequency [Classical]": 5,
        'Foreign languages':,
        'BPM':, 
        'Frequency [Classical]':,
       'Frequency [EDM]':, 
       'Frequency [Folk]':,
        'Frequency [Gospel]':,
       'Frequency [Hip hop]':, 
       'Frequency [Jazz]':, 
       'Frequency [K pop]':,
       'Frequency [Metal]':, 
       'Frequency [Pop]':, 
       'Frequency [R&B]':,
       'Frequency [Rock]':, 
       'Frequency [Video game music]:

    }

def display_stored_user_data(user_profile):
    st.write(f"""
        **Stored Profile**:
        - **Age**: {user_profile.get('Age', 'Not set')}
        - **Instrumentalist**: {user_profile.get('Instrumentalist', 'Not set')}
        - **Composer**: {user_profile.get('Composer', 'Not set')}
        - **Hours per day**: {user_profile.get('Hours per day', 'Not set')}
        - **While working**: {user_profile.get('While working', 'Not set')}
        - **Music Effects**: {user_profile.get('Music effects', 'Not set')}
      """)