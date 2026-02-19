import streamlit as st
import asyncio
from navigation import create_top_navigation

async def home_page():
    """Display home page with welcome message."""
    # Create top navigation
    create_top_navigation()
    
    # Set background color
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .welcome-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 70vh;
        text-align: center;
        color: white;
    }
    .main-title {
        font-size: 4rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        opacity: 0.9;
        max-width: 600px;
        line-height: 1.6;
    }
    .feature-cards {
        display: flex;
        gap: 2rem;
        margin-top: 3rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    .feature-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        width: 250px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        opacity: 0.8;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Welcome content
    st.markdown("""
    <div class="welcome-container">
        <div class="main-title">Reimagining Music Therapy</div>
        <div class="subtitle">TheraBeat AI</div>
        <div class="subtitle">Your personalized journey to mental wellness through the power of generative audio landscapes.</div>
        
        <div class="feature-cards">
            <div class="feature-card">
                <div class="feature-icon">🎵</div>
                <div class="feature-title">AI Music</div>
                <div class="feature-desc">Generate personalized music based on your mood and preferences</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎧</div>
                <div class="feature-title">Spotify Playlists</div>
                <div class="feature-desc">Get curated playlists tailored to your emotional state</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">😊</div>
                <div class="feature-title">Mood Tracking</div>
                <div class="feature-desc">Track your emotional journey over time</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Run the home page
asyncio.run(home_page())
