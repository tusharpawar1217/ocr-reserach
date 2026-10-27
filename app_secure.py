"""
CIV Board OCR Streamlit Application - Secure Version with Authentication
"""

import streamlit as st

# Configure page first
st.set_page_config(
    page_title="CIV Board OCR System - Secure",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with Charcoal, Forest Green, Crimson Red, White
st.markdown("""
<style>
    /* Main color scheme */
    :root {
        --charcoal-black: #171717;
        --forest-green: #06110C;
        --crimson-red: #A31C18;
        --white: #FFFFFF;
    }
    
    /* Headers styling */
    .main h1, .main h2, .main h3 {
        color: #A31C18 !important;
        font-weight: 700;
    }
    
    /* Buttons - Crimson Red */
    .stButton>button {
        background-color: #A31C18;
        color: white;
        border: 2px solid #A31C18;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #8B1714;
        border-color: #8B1714;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(163, 28, 24, 0.3);
    }
    
    /* Success messages - Forest Green accent */
    .stSuccess {
        background-color: rgba(6, 17, 12, 0.3);
        border-left: 4px solid #06110C;
    }
    
    /* Info messages */
    .stInfo {
        background-color: rgba(163, 28, 24, 0.1);
        border-left: 4px solid #A31C18;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #A31C18;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #06110C;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        background-color: rgba(6, 17, 12, 0.5);
        color: white;
        font-weight: 600;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #A31C18;
        background-color: rgba(6, 17, 12, 0.2);
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #06110C;
        color: white;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #A31C18;
    }
    
    /* Text input and textarea */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-color: #06110C;
        background-color: rgba(23, 23, 23, 0.9);
        color: white;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #A31C18;
        box-shadow: 0 0 0 1px #A31C18;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #A31C18;
    }
    
    /* Links */
    a {
        color: #A31C18 !important;
        font-weight: 600;
    }
    
    a:hover {
        color: #8B1714 !important;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Import authentication module
from auth import (
    init_session_auth, is_authenticated, show_login_page, 
    logout, get_user_info, change_password
)

# Initialize authentication session
init_session_auth()

def show_change_password():
    """Show change password interface in sidebar"""
    with st.sidebar.expander("🔑 Change Password"):
        with st.form("change_password_form"):
            old_password = st.text_input("Current Password", type="password", key="old_pwd")
            new_password = st.text_input("New Password", type="password", key="new_pwd")
            confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_pwd")
            
            if st.form_submit_button("Update Password"):
                if not old_password or not new_password or not confirm_password:
                    st.error("All fields are required")
                elif new_password != confirm_password:
                    st.error("New passwords don't match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, message = change_password(
                        st.session_state.username, 
                        old_password, 
                        new_password
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def show_secure_app():
    """Main secure application"""
    # Import main app after authentication
    from app import main_app
    
    # Sidebar with user info
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Information")
        
        user_info = get_user_info(st.session_state.username)
        st.write(f"**Name:** {user_info.get('full_name', st.session_state.username)}")
        st.write(f"**Role:** {user_info.get('role', 'user').title()}")
        st.write(f"**Username:** {st.session_state.username}")
        
        # Change password option
        show_change_password()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🔒 Logout", use_container_width=True):
            logout()
            st.success("Logged out successfully!")
            st.rerun()
    
    # Run main application
    main_app()

def main():
    """Main entry point with authentication check"""
    if not is_authenticated():
        # Show login page
        show_login_page()
    else:
        # Show main app
        show_secure_app()

if __name__ == "__main__":
    main()
