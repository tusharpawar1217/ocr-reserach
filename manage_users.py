"""
User Management Script for CIV Board OCR System
Command-line tool for managing users
"""

import sys
from auth import (
    init_auth, verify_credentials, add_user, change_password,
    list_users, get_user_info, load_auth_config
)

def print_menu():
    """Print main menu"""
    print("\n" + "="*60)
    print("CIV Board OCR - User Management")
    print("="*60)
    print("1. List all users")
    print("2. Add new user")
    print("3. Change password")
    print("4. View user details")
    print("5. View system settings")
    print("6. Exit")
    print("="*60)

def list_all_users():
    """List all users"""
    print("\n📋 User List:")
    print("-" * 80)
    users = list_users()
    
    if not users:
        print("No users found.")
        return
    
    print(f"{'Username':<20} {'Full Name':<25} {'Role':<10} {'Created'}")
    print("-" * 80)
    
    for user in users:
        print(f"{user['username']:<20} {user['full_name']:<25} {user['role']:<10} {user['created_at'][:10]}")
    
    print("-" * 80)
    print(f"Total users: {len(users)}")

def add_new_user():
    """Add new user"""
    print("\n➕ Add New User")
    print("-" * 60)
    
    # Admin authentication
    admin_username = input("Admin Username: ").strip()
    admin_password = input("Admin Password: ").strip()
    
    if not verify_credentials(admin_username, admin_password):
        print("❌ Invalid admin credentials!")
        return
    
    print("\n✅ Admin authenticated")
    print("\nNew User Details:")
    
    new_username = input("Username: ").strip()
    new_password = input("Password: ").strip()
    confirm_password = input("Confirm Password: ").strip()
    
    if new_password != confirm_password:
        print("❌ Passwords don't match!")
        return
    
    if len(new_password) < 6:
        print("❌ Password must be at least 6 characters!")
        return
    
    full_name = input("Full Name (optional): ").strip()
    
    print("\nSelect Role:")
    print("1. Admin (full access)")
    print("2. User (standard access)")
    role_choice = input("Choice (1/2): ").strip()
    
    role = "admin" if role_choice == "1" else "user"
    
    # Add user
    success, message = add_user(
        admin_username, admin_password,
        new_username, new_password,
        full_name, role
    )
    
    if success:
        print(f"\n✅ {message}")
        print(f"\n📝 User Details:")
        print(f"   Username: {new_username}")
        print(f"   Full Name: {full_name or new_username}")
        print(f"   Role: {role}")
    else:
        print(f"\n❌ {message}")

def change_user_password():
    """Change user password"""
    print("\n🔑 Change Password")
    print("-" * 60)
    
    username = input("Username: ").strip()
    old_password = input("Current Password: ").strip()
    new_password = input("New Password: ").strip()
    confirm_password = input("Confirm New Password: ").strip()
    
    if new_password != confirm_password:
        print("❌ Passwords don't match!")
        return
    
    if len(new_password) < 6:
        print("❌ Password must be at least 6 characters!")
        return
    
    success, message = change_password(username, old_password, new_password)
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")

def view_user_details():
    """View user details"""
    print("\n👤 View User Details")
    print("-" * 60)
    
    username = input("Username: ").strip()
    user_info = get_user_info(username)
    
    if not user_info:
        print(f"❌ User '{username}' not found!")
        return
    
    print(f"\n📝 User Details:")
    print(f"   Username: {username}")
    print(f"   Full Name: {user_info.get('full_name', 'N/A')}")
    print(f"   Role: {user_info.get('role', 'N/A')}")
    print(f"   Created: {user_info.get('created_at', 'N/A')[:19]}")
    
    if 'created_by' in user_info:
        print(f"   Created By: {user_info['created_by']}")
    
    if 'password_changed_at' in user_info:
        print(f"   Password Changed: {user_info['password_changed_at'][:19]}")

def view_system_settings():
    """View system settings"""
    print("\n⚙️ System Settings")
    print("-" * 60)
    
    auth_data = load_auth_config()
    settings = auth_data.get("settings", {})
    
    print(f"Session Timeout: {settings.get('session_timeout_minutes', 30)} minutes")
    print(f"Max Login Attempts: {settings.get('max_login_attempts', 5)}")
    print(f"Total Users: {len(auth_data.get('users', {}))}")

def main():
    """Main function"""
    # Initialize auth system
    init_auth()
    
    print("\n🔐 CIV Board OCR - User Management System")
    
    while True:
        print_menu()
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            list_all_users()
        elif choice == "2":
            add_new_user()
        elif choice == "3":
            change_user_password()
        elif choice == "4":
            view_user_details()
        elif choice == "5":
            view_system_settings()
        elif choice == "6":
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            print("\n❌ Invalid option! Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
