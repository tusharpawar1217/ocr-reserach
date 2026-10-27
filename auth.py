"""
Authentication module for CIV Board OCR System
Provides login functionality with password hashing
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
import streamlit as st

# Default credentials (first-time setup)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "ocr@2024"

# Auth config file
AUTH_CONFIG_FILE = ".auth_config.json"

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth():
    """Initialize authentication system with default credentials"""
    if not os.path.exists(AUTH_CONFIG_FILE):
        # Create default auth config
        auth_data = {
            "users": {
                DEFAULT_USERNAME: {
                    "password_hash": hash_password(DEFAULT_PASSWORD),
                    "created_at": datetime.now().isoformat(),
                    "role": "admin",
                    "full_name": "Administrator"
                }
            },
            "settings": {
                "session_timeout_minutes": 30,
                "max_login_attempts": 5
            }
        }
        
        with open(AUTH_CONFIG_FILE, 'w') as f:
            json.dump(auth_data, f, indent=2)
        
        print(f"✅ Authentication initialized")
        print(f"   Default Username: {DEFAULT_USERNAME}")
        print(f"   Default Password: {DEFAULT_PASSWORD}")
        return True
    return False

def load_auth_config():
    """Load authentication configuration"""
    if not os.path.exists(AUTH_CONFIG_FILE):
        init_auth()
    
    with open(AUTH_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_auth_config(auth_data):
    """Save authentication configuration"""
    with open(AUTH_CONFIG_FILE, 'w') as f:
        json.dump(auth_data, f, indent=2)

def verify_credentials(username: str, password: str) -> bool:
    """Verify username and password"""
    try:
        auth_data = load_auth_config()
        
        if username not in auth_data["users"]:
            return False
        
        user_data = auth_data["users"][username]
        password_hash = hash_password(password)
        
        return password_hash == user_data["password_hash"]
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def change_password(username: str, old_password: str, new_password: str) -> tuple:
    """
    Change user password
    Returns (success: bool, message: str)
    """
    try:
        auth_data = load_auth_config()
        
        # Verify old password
        if not verify_credentials(username, old_password):
            return False, "Current password is incorrect"
        
        # Update password
        auth_data["users"][username]["password_hash"] = hash_password(new_password)
        auth_data["users"][username]["password_changed_at"] = datetime.now().isoformat()
        
        save_auth_config(auth_data)
        return True, "Password changed successfully"
        
    except Exception as e:
        return False, f"Error changing password: {str(e)}"

def add_user(admin_username: str, admin_password: str, new_username: str, 
             new_password: str, full_name: str = "", role: str = "user") -> tuple:
    """
    Add a new user (admin only)
    Returns (success: bool, message: str)
    """
    try:
        # Verify admin credentials
        if not verify_credentials(admin_username, admin_password):
            return False, "Admin authentication failed"
        
        auth_data = load_auth_config()
        
        # Check if admin user has admin role
        if auth_data["users"][admin_username]["role"] != "admin":
            return False, "Only administrators can add users"
        
        # Check if user already exists
        if new_username in auth_data["users"]:
            return False, "Username already exists"
        
        # Add new user
        auth_data["users"][new_username] = {
            "password_hash": hash_password(new_password),
            "created_at": datetime.now().isoformat(),
            "role": role,
            "full_name": full_name or new_username,
            "created_by": admin_username
        }
        
        save_auth_config(auth_data)
        return True, f"User '{new_username}' added successfully"
        
    except Exception as e:
        return False, f"Error adding user: {str(e)}"

def get_user_info(username: str) -> dict:
    """Get user information"""
    try:
        auth_data = load_auth_config()
        if username in auth_data["users"]:
            user_data = auth_data["users"][username].copy()
            # Remove password hash from returned data
            user_data.pop("password_hash", None)
            return user_data
        return {}
    except Exception as e:
        print(f"Error getting user info: {e}")
        return {}

def list_users() -> list:
    """List all users (admin only)"""
    try:
        auth_data = load_auth_config()
        users = []
        for username, data in auth_data["users"].items():
            users.append({
                "username": username,
                "full_name": data.get("full_name", username),
                "role": data.get("role", "user"),
                "created_at": data.get("created_at", "N/A")
            })
        return users
    except Exception as e:
        print(f"Error listing users: {e}")
        return []

def init_session_auth():
    """Initialize session state for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

def login(username: str, password: str) -> bool:
    """
    Login user and create session
    Returns True if successful, False otherwise
    """
    if verify_credentials(username, password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.login_time = datetime.now()
        st.session_state.login_attempts = 0
        return True
    else:
        st.session_state.login_attempts += 1
        return False

def logout():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.login_time = None

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    if not st.session_state.get('authenticated', False):
        return False
    
    # Check session timeout
    auth_data = load_auth_config()
    timeout_minutes = auth_data["settings"].get("session_timeout_minutes", 30)
    
    if st.session_state.login_time:
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed > timedelta(minutes=timeout_minutes):
            logout()
            return False
    
    return True

def show_login_page():
    """Display login page"""
    st.set_page_config(
        page_title="Login - CIV Board OCR",
        page_icon="🔐",
        layout="centered"
    )
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/lock.png", width=100)
        st.title("🔐 CIV Board OCR System")
        st.markdown("### Secure Login")
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    # Check login attempts
                    max_attempts = load_auth_config()["settings"].get("max_login_attempts", 5)
                    
                    if st.session_state.get('login_attempts', 0) >= max_attempts:
                        st.error(f"🚫 Too many failed login attempts. Please refresh the page.")
                    else:
                        if login(username, password):
                            st.success("✅ Login successful!")
                            st.balloons()
                            st.rerun()
                        else:
                            attempts_left = max_attempts - st.session_state.login_attempts
                            st.error(f"❌ Invalid credentials. {attempts_left} attempts remaining.")
        
        st.markdown("---")
        
        # Default credentials info (for first-time users)
        with st.expander("ℹ️ First Time Login?"):
            st.info(f"""
            **Default Credentials:**
            - Username: `{DEFAULT_USERNAME}`
            - Password: `{DEFAULT_PASSWORD}`
            
            ⚠️ **Important**: Change your password after first login!
            """)
        
        # Footer
        st.markdown("---")
        st.caption("🔒 Secure authentication for CIV Board OCR data")

# Initialize auth on module import
init_auth()
