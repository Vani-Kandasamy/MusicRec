import streamlit as st
from login import logout

def create_top_navigation():
    """Create top navigation bar with page links and logout."""
    
    # CSS for top navigation
    st.markdown("""
    <style>
    .top-nav {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .nav-links {
        display: flex;
        gap: 20px;
        align-items: center;
        flex-wrap: wrap;
    }
    .nav-link {
        text-decoration: none;
        color: #1f77b4;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 5px;
        transition: background-color 0.3s;
        border: 2px solid transparent;
    }
    .nav-link:hover {
        background-color: #e1e5ea;
        border-color: #1f77b4;
    }
    .nav-link.active {
        background-color: #1f77b4;
        color: white;
    }
    .logout-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .logout-btn:hover {
        background-color: #ff6b6b;
    }
    .app-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get current page from URL parameters or session state
    query_params = st.query_params
    current_page = query_params.get('page', 'dashboard')
    
    # Create top navigation
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="top-nav">
            <div class="nav-links">
                <span class="app-title">🎵 Music for Mental Health</span>
                <a href="?page=dashboard" class="nav-link {'active' if current_page == 'dashboard' else ''}">📊 Dashboard</a>
                <a href="?page=profile" class="nav-link {'active' if current_page == 'profile' else ''}">👤 Profile</a>
                <a href="?page=mood" class="nav-link {'active' if current_page == 'mood' else ''}">😊 Mood</a>
                <a href="?page=ai_music" class="nav-link {'active' if current_page == 'ai_music' else ''}">🎵 AI Music</a>
                <a href="?page=spotify" class="nav-link {'active' if current_page == 'spotify' else ''}">🎧 Spotify</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🚪 Logout", key="top_logout", type="secondary"):
            logout()
            st.rerun()
    
    # Add welcome message in sidebar
    if 'user' in st.session_state:
        user = st.session_state.user
        st.sidebar.write(f"Welcome, {user.get('name', 'User')}!")

def handle_page_navigation():
    """Handle navigation between pages based on URL parameters."""
    query_params = st.query_params
    page = query_params.get('page', 'dashboard')
    
    # Map page names to file paths
    page_map = {
        'dashboard': 'app_simple.py',
        'profile': 'pages/01_Profile.py',
        'mood': 'pages/02_Current_Mood.py',
        'ai_music': 'pages/03_AI_Music.py',
        'spotify': 'pages/04_Spotify_Playlists.py'
    }
    
    # If not on dashboard and page exists in map, switch to that page
    if page != 'dashboard' and page in page_map:
        st.switch_page(page_map[page])
    
    return page == 'dashboard'
