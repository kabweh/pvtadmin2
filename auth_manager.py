"""
Authentication module for AI Tutor application.
Handles user authentication, invite-only signup, and subscription management.
"""
import os
import datetime
import secrets
import bcrypt
from typing import Dict, Any, Optional, Tuple, List

# Assuming database.py is in the same directory
from database import Database

class AuthManager:
    """
    Handles authentication and subscription management for the AI Tutor application.
    """

    def __init__(self, database: Database):
        """
        Initialize the authentication manager.

        Args:
            database: Database instance for user storage
        """
        self.database = database

    def register_user(self, username: str, password: str, email: Optional[str] = None,
                     invite_token: Optional[str] = None) -> Dict:
        """
        Register a new user.
        Allows the first user to register without an invite token and sets them as admin.

        Args:
            username: User's username
            password: User's password (will be hashed)
            email: User's email address (optional)
            invite_token: Invite token for invite-only signup (required for non-first users)

        Returns:
            Dictionary containing registration status and user info if successful
        """
        is_first_user = self.database.count_users() == 0

        # Check if invite token is required
        if not is_first_user:
            if not invite_token:
                return {
                    "success": False,
                    "message": "Invite token is required for registration."
                }
            # Validate the invite token before proceeding
            token_validation = self.validate_invite_token(invite_token)
            if not token_validation["success"]:
                 return {
                    "success": False,
                    "message": token_validation["message"] # Provide specific error
                }

        # Validate username and password
        if not username or len(username) < 3:
            return {
                "success": False,
                "message": "Username must be at least 3 characters long."
            }

        if not password or len(password) < 8:
            return {
                "success": False,
                "message": "Password must be at least 8 characters long."
            }

        # Hash the password
        password_hash = self._hash_password(password)

        # Add user to database, setting admin status for the first user
        user_id = self.database.add_user(username, password_hash, email, is_admin=is_first_user)

        if user_id == -1:
            return {
                "success": False,
                "message": "Username or email already exists."
            }

        # Mark invite token as used (only if not the first user)
        token_used_successfully = True
        if not is_first_user:
            if not self.database.use_invite_link(invite_token, user_id):
                # This case should ideally not happen if we validate the token first,
                # but keep it as a safeguard.
                token_used_successfully = False
                # Consider if registration should fail if token use fails *after* validation.
                # For now, proceed but warn.

        # Get the user info (including the new is_admin flag)
        user = self.database.get_user_by_id(user_id)

        message = "User registered successfully."
        if not is_first_user and not token_used_successfully:
            message = "User registered successfully, but there was an issue marking the invite token as used."
        elif is_first_user:
             message = "Administrator account registered successfully."

        return {
            "success": True,
            "message": message,
            "user": user
        }

    def login_user(self, username: str, password: str) -> Dict:
        """
        Log in a user.

        Args:
            username: User's username
            password: User's password

        Returns:
            Dictionary containing login status and user info if successful
        """
        # Get user from database
        user = self.database.get_user_by_username(username)

        if not user:
            return {
                "success": False,
                "message": "Invalid username or password."
            }

        # Check password
        if not self._check_password(password, user['password_hash']):
            return {
                "success": False,
                "message": "Invalid username or password."
            }

        return {
            "success": True,
            "message": "Login successful.",
            "user": user # User dict now includes 'is_admin'
        }

    def generate_invite_link(self, created_by_user_id: int, email: Optional[str] = None,
                            expires_in_days: int = 7) -> Dict:
        """
        Generate a new invite link, restricted to admin users.

        Args:
            created_by_user_id: User ID of the user attempting to create the invite
            email: Email address the invite is for (optional)
            expires_in_days: Number of days until the invite expires

        Returns:
            Dictionary with success status, message, and optionally the token.
        """
        # Check if the user is an admin
        if not self.database.is_user_admin(created_by_user_id):
            return {
                "success": False,
                "message": "Only administrators can generate invite links."
            }

        try:
            invite_id, token = self.database.create_invite_link(created_by_user_id, email, expires_in_days)
            return {
                "success": True,
                "message": f"Invite link generated successfully. Expires in {expires_in_days} days.",
                "token": token,
                "invite_id": invite_id
            }
        except Exception as e:
            # Log the exception e
            return {
                "success": False,
                "message": f"Failed to generate invite link: {e}"
            }

    def get_active_invites(self, requesting_user_id: int) -> Dict:
        """
        Get active invite links created by the requesting user (if admin).

        Args:
            requesting_user_id: User ID of the user requesting the list.

        Returns:
            Dictionary with success status, message, and list of invites.
        """
        if not self.database.is_user_admin(requesting_user_id):
            return {
                "success": False,
                "message": "Only administrators can view invite links.",
                "invites": []
            }

        try:
            invites = self.database.get_active_invites_by_creator(requesting_user_id)
            return {
                "success": True,
                "message": "Active invites retrieved successfully.",
                "invites": invites
            }
        except Exception as e:
            # Log the exception e
            return {
                "success": False,
                "message": f"Failed to retrieve invite links: {e}",
                "invites": []
            }

    def validate_invite_token(self, token: str) -> Dict:
        """
        Validate an invite token by checking the database.

        Args:
            token: The invite token

        Returns:
            Dictionary containing validation status and invite info if valid
        """
        conn = self.database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, expires_at FROM invite_links WHERE token = ? AND used = 0",
            (token,)
        )
        invite = cursor.fetchone()

        if not invite:
            return {
                "success": False,
                "message": "Invalid or already used invite token."
            }

        # Check if token is expired
        try:
            # Ensure expires_at is treated as a string before parsing
            expires_at_str = invite["expires_at"]
            if isinstance(expires_at_str, datetime.datetime):
                 # If it's already a datetime object (less likely with sqlite3.Row but possible)
                 expires_at = expires_at_str
            else:
                 expires_at = datetime.datetime.fromisoformat(str(expires_at_str))

            # Make comparison timezone-aware if necessary, assuming UTC for now
            if expires_at < datetime.datetime.now(): # Consider timezone if DB stores differently
                return {
                    "success": False,
                    "message": "Invite token has expired."
                }
        except ValueError:
            return {
                "success": False,
                "message": "Invalid expiration date format for invite token."
            }
        except TypeError:
             return {
                "success": False,
                "message": "Could not parse expiration date for invite token."
            }


        return {
            "success": True,
            "message": "Invite token is valid.",
            "invite": dict(invite)
        }

    def activate_subscription(self, user_id: int, duration_days: int = 30) -> Dict:
        """
        Activate a subscription for a user (Placeholder).

        Args:
            user_id: User ID
            duration_days: Number of days to activate the subscription for

        Returns:
            Dictionary containing activation status
        """
        # Placeholder - In real app, update DB: users table set subscription_active=1, subscription_expires=...
        expires_at_dt = datetime.datetime.now() + datetime.timedelta(days=duration_days)
        expires_at_iso = expires_at_dt.isoformat()

        # Simulate DB update (in real app, call self.database.update_subscription(user_id, expires_at_iso))
        print(f"Simulating subscription activation for user {user_id} until {expires_at_iso}")

        return {
            "success": True,
            "message": "Subscription activated successfully.",
            "expires_at": expires_at_iso
        }

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Password to hash

        Returns:
            Hashed password as a string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _check_password(self, password: str, hashed_password: str) -> bool:
        """
        Check if a password matches a hash.

        Args:
            password: Password to check
            hashed_password: Hashed password to compare against

        Returns:
            True if the password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
             # Handle cases where hashed_password might not be a valid bcrypt hash
             print(f"Warning: Invalid hash format encountered for user during login check.")
             return False

# End of class AuthManager

