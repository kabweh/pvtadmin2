"""
Streamlit component for authentication in the AI Tutor application.
Provides UI elements for login, registration, invite management, and subscription management.
"""
import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd # To display invites nicely
import datetime # To format dates

# Use relative import within the package
from auth_manager import AuthManager

class AuthComponent:
    """
    Streamlit component for handling authentication in the AI Tutor application.
    """

    def __init__(self, auth_manager: AuthManager):
        """
        Initialize the authentication component.

        Args:
            auth_manager: Instance of AuthManager to handle authentication
        """
        self.auth_manager = auth_manager

    def render_auth_forms(self) -> None:
        """
        Render the authentication forms (login and registration).
        """
        # Create tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Sign Up"])

        # Login form
        with login_tab:
            with st.form("login_form"):
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                submitted = st.form_submit_button("Login")
                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    else:
                        # Attempt login
                        result = self.auth_manager.login_user(username, password)

                        if result["success"]:
                            # Store user in session state
                            st.session_state.user = result["user"]
                            st.success("Login successful!")
                            # Use st.rerun() instead of experimental_rerun()
                            st.rerun()
                        else:
                            st.error(result["message"])

        # Registration form
        with register_tab:
            with st.form("register_form"):
                st.subheader("Sign Up")

                # Check if this is the first user registration
                is_first_user = self.auth_manager.database.count_users() == 0

                if is_first_user:
                    st.info("Welcome! As the first user, you will be registered as an administrator. No invite code is needed.")
                    invite_token_required = False
                else:
                    st.info("Registration requires a valid invite code. Please contact an administrator if you don't have one.")
                    invite_token_required = True

                new_username = st.text_input("Username", key="reg_username")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                email = st.text_input("Email (optional)")
                invite_token = st.text_input("Invite Code", disabled=not invite_token_required)

                submitted = st.form_submit_button("Sign Up")
                if submitted:
                    # Validate inputs
                    if not new_username or not new_password:
                        st.error("Please enter both username and password.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif invite_token_required and not invite_token:
                        st.error("Invite code is required.")
                    else:
                        # Attempt registration (pass None for invite_token if not required)
                        actual_invite_token = invite_token if invite_token_required else None
                        result = self.auth_manager.register_user(
                            new_username,
                            new_password,
                            email,
                            invite_token=actual_invite_token
                        )

                        if result["success"]:
                            st.success(f"{result['message']} You can now log in.")
                            # Use st.rerun() instead of experimental_rerun()
                            st.rerun()
                        else:
                            st.error(result["message"])

    def render_auth_status_and_admin(self) -> None:
        """
        Render the authentication status and admin controls in the sidebar.
        """
        if st.session_state.get("user"):
            user = st.session_state.user

            st.write(f"Logged in as: **{user['username']}**")

            # Display Admin status
            is_admin = user.get('is_admin', False)
            if is_admin:
                st.success("Role: Administrator")

            # Subscription status (Optional - kept from original)
            # if user.get("subscription_active", False):
            #     st.success("Subscription: Active")
            #     if user.get("subscription_expires"):
            #         st.write(f"Expires: {user['subscription_expires']}")
            # else:
            #     st.warning("Subscription: Inactive")

            # Logout button
            if st.button("Logout"):
                # Clear user-specific session state
                keys_to_clear = [k for k in st.session_state.keys() if k not in ["initialized", "current_page"]]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.session_state.user = None # Ensure user is cleared
                # Use st.rerun() instead of experimental_rerun()
                st.rerun()

            # --- Admin Panel --- #
            if is_admin:
                st.sidebar.divider()
                st.sidebar.subheader("Admin Panel")
                self.render_invite_management()

        else:
            st.info("Not logged in")

    def render_invite_management(self) -> None:
        """
        Render the invite code generation and management section for admins.
        Placed in the sidebar under the Admin Panel section.
        """
        st.sidebar.write("**Invite Management**")

        # --- Generate New Invite --- #
        with st.sidebar.expander("Generate New Invite Code"):
            with st.form("generate_invite_form"):
                invite_email = st.text_input("Email (Optional)", help="Associate the invite with an email address.")
                invite_days = st.number_input("Expires in (days)", min_value=1, max_value=365, value=7)
                generate_submitted = st.form_submit_button("Generate Invite")

                if generate_submitted:
                    user_id = st.session_state.user['id']
                    result = self.auth_manager.generate_invite_link(user_id, invite_email or None, invite_days)
                    if result["success"]:
                        st.success(f"Invite generated! Code: `{result['token']}`")
                        # Rerun to refresh the list of active invites
                        st.rerun()
                    else:
                        st.error(result["message"])

        # --- View Active Invites --- #
        st.sidebar.write("**Active Invite Codes**")
        user_id = st.session_state.user['id']
        invites_result = self.auth_manager.get_active_invites(user_id)

        if invites_result["success"]:
            active_invites = invites_result["invites"]
            if active_invites:
                # Prepare data for display
                display_data = []
                for invite in active_invites:
                    try:
                        # Parse ISO string, handle potential errors
                        expires_dt = datetime.datetime.fromisoformat(str(invite['expires_at']))
                        expires_str = expires_dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        expires_str = "Invalid Date"

                    display_data.append({
                        "Code": invite['token'],
                        "Email": invite.get('email', 'N/A'),
                        "Expires": expires_str
                    })

                df = pd.DataFrame(display_data)
                st.sidebar.dataframe(df, use_container_width=True)
                # Add a copy button for convenience (requires streamlit-extras or similar)
                # Consider adding functionality to revoke invites if needed
            else:
                st.sidebar.info("No active invite codes found.")
        else:
            st.sidebar.error(f"Could not load invites: {invites_result['message']}")

    # Kept for potential future use, but not directly used in the main flow now
    def render_subscription_management(self) -> None:
        """
        Render the subscription management section (Placeholder).
        This would typically be on a separate Account or Billing page.
        """
        st.header("Subscription Management")

        # Check if user is logged in
        if not st.session_state.get("user"):
            st.warning("Please log in to manage your subscription.")
            return

        user = st.session_state.user

        # Display current subscription status
        if user.get("subscription_active", False):
            st.success("Your subscription is currently active.")
            if user.get("subscription_expires"):
                st.write(f"Your subscription expires on: {user['subscription_expires']}")

            # Renewal/Management options (placeholder)
            st.subheader("Manage Subscription")
            st.write("Contact an administrator or visit the billing portal (link placeholder) to manage your subscription.")
        else:
            st.warning("You don't have an active subscription.")

            # Subscription options (placeholder)
            st.subheader("Subscription Options")
            st.write("Contact an administrator or choose a plan below to activate your subscription.")

            if st.button("Subscribe (Test Mode)"):
                result = self.auth_manager.activate_subscription(user["id"])

                if result["success"]:
                    st.session_state.user["subscription_active"] = True
                    st.session_state.user["subscription_expires"] = result["expires_at"]
                    st.success("Subscription activated successfully!")
                    st.rerun()
                else:
                    st.error(result["message"])

