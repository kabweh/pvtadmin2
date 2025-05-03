"""
Main Streamlit application file for AI Tutor.
Integrates all components and provides the main user interface.
"""
import os
import sys # Added import
import streamlit as st
from PIL import Image

# Add the project root directory to the Python path (using append)
# This ensures Streamlit Cloud can find custom modules
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import components from modules
from upload_manager import UploadManager
from upload_component import UploadComponent
from lesson_explainer import LessonExplainer
from explanation_component import ExplanationComponent
from text_to_speech import TextToSpeech
from tts_component import TTSComponent
from database import Database
from quiz_generator import QuizGenerator
from report_generator import ReportGenerator
from quiz_component import QuizComponent
from report_component import ReportComponent
from auth_manager import AuthManager
from auth_component import AuthComponent

# Set page configuration
st.set_page_config(
    page_title="AI Tutor",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.current_page = "Home"
    st.session_state.user = None

def initialize_app():
    """Initialize application components and database."""
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)
    os.makedirs("static/reports", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    # Initialize database
    st.session_state.db = Database()
    
    # Initialize components
    st.session_state.upload_manager = UploadManager()
    st.session_state.upload_component = UploadComponent(st.session_state.upload_manager)
    
    st.session_state.lesson_explainer = LessonExplainer()
    st.session_state.explanation_component = ExplanationComponent(st.session_state.lesson_explainer)
    
    st.session_state.tts_handler = TextToSpeech()
    st.session_state.tts_component = TTSComponent(st.session_state.tts_handler)
    
    st.session_state.quiz_generator = QuizGenerator()
    st.session_state.quiz_component = QuizComponent(st.session_state.quiz_generator, st.session_state.db)
    
    st.session_state.report_generator = ReportGenerator()
    st.session_state.report_component = ReportComponent(st.session_state.report_generator, st.session_state.db)
    
    st.session_state.auth_manager = AuthManager(st.session_state.db)
    st.session_state.auth_component = AuthComponent(st.session_state.auth_manager)
    
    st.session_state.initialized = True

# Initialize app if not already initialized
if not st.session_state.initialized:
    initialize_app()

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #424242;
            margin-bottom: 1rem;
        }
        .sidebar-header {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .stButton>button {
            width: 100%;
        }
        .nav-button {
            margin-bottom: 0.5rem;
        }
        .footer {
            text-align: center;
            color: #9E9E9E;
            font-size: 0.8rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #E0E0E0;
        }
        .highlight-box {
            background-color: #F5F5F5;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1E88E5;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Sidebar navigation
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-header">AI Tutor</div>', unsafe_allow_html=True)
        
        # User authentication section
        st.session_state.auth_component.render_auth_status_and_admin()
        
        st.markdown("---")
        st.markdown('<div class="sidebar-header">Navigation</div>', unsafe_allow_html=True)
        
        # Navigation buttons (Corrected Indentation)
        if st.button("Home", key="nav_home", help="Go to the home page"):
            st.session_state.current_page = "Home"
            st.experimental_rerun()
            
        if st.button("Upload Material", key="nav_upload", help="Upload and process learning materials"):
            st.session_state.current_page = "Upload"
            st.experimental_rerun()
            
        if st.button("Lessons", key="nav_lessons", help="View and explain lessons"):
            st.session_state.current_page = "Lessons"
            st.experimental_rerun()
            
        if st.button("Quizzes", key="nav_quizzes", help="Take quizzes on lesson content"):
            st.session_state.current_page = "Quizzes"
            st.experimental_rerun()
            
        if st.button("Progress Reports", key="nav_reports", help="View your progress reports"):
            st.session_state.current_page = "Reports"
            st.experimental_rerun()
        
        # Admin section (only visible to admins) (Corrected Indentation)
        if st.session_state.user and st.session_state.user.get('is_admin', False):
            st.markdown("---")
            st.markdown('<div class="sidebar-header">Admin</div>', unsafe_allow_html=True)
            
            if st.button("Manage Users", key="nav_admin_users"):
                st.session_state.current_page = "Admin_Users"
                st.experimental_rerun()
                
            if st.button("Generate Invites", key="nav_admin_invites"):
                st.session_state.current_page = "Admin_Invites"
                st.experimental_rerun()
        
        # Footer
        st.markdown('<div class="footer">AI Tutor © 2025</div>', unsafe_allow_html=True)

# Home page
def render_home_page():
    st.markdown('<h1 class="main-header">Welcome to AI Tutor</h1>', unsafe_allow_html=True)
    
    # Check if user is logged in
    if not st.session_state.user:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown("👋 **Welcome!** Please sign in or sign up to access all features.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show auth component
        st.session_state.auth_component.render_auth_forms()
    else:
        st.markdown(f"👋 **Welcome back, {st.session_state.user['username']}!**")
        
        # Quick stats if user has activity
        quiz_history = st.session_state.db.get_user_quiz_history(st.session_state.user['id'])
        if quiz_history:
            st.markdown("### Your Stats")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Quizzes Taken", len(quiz_history))
            
            with col2:
                completed_quizzes = [q for q in quiz_history if q.get('completed_at')]
                avg_score = sum(q.get('score', 0) / q.get('max_score', 1) * 100 for q in completed_quizzes if q.get('max_score', 0) > 0) / len(completed_quizzes) if completed_quizzes else 0
                st.metric("Average Score", f"{avg_score:.1f}%")
            
            with col3:
                reports = st.session_state.db.get_user_progress_reports(st.session_state.user['id'])
                st.metric("Reports Generated", len(reports))
    
    # Feature overview
    st.markdown("## How AI Tutor Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📚 Upload Learning Materials")
        st.markdown("""
        - Upload images, PDFs, and DOCX files
        - AI automatically extracts text content
        - All your materials in one place
        """)
        
        st.markdown("### 🎓 Get Personalized Explanations")
        st.markdown("""
        - Click "Explain" on any uploaded content
        - Receive clear, conversational explanations
        - Choose simple, medium, or advanced complexity
        """)
    
    with col2:
        st.markdown("### 🔊 Listen to Lessons")
        st.markdown("""
        - Convert explanations to speech
        - Adjust volume and playback controls
        - Learn on the go with audio lessons
        """)
        
        st.markdown("### 📊 Track Your Progress")
        st.markdown("""
        - Take quizzes to test your understanding
        - View detailed progress reports
        - Email reports to parents or teachers
        """)
    
    # Getting started guide
    st.markdown("## Getting Started")
    st.markdown("""
    1. **Sign up or log in** to access all features
    2. **Upload your learning materials** (textbooks, notes, etc.)
    3. **Get explanations** for difficult concepts
    4. **Take quizzes** to test your understanding
    5. **Track your progress** with detailed reports
    """)
    
    # Call to action
    st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
    st.markdown("Ready to start learning? Click **Upload Material** in the sidebar to begin!")
    st.markdown("</div>", unsafe_allow_html=True)

# Upload page
def render_upload_page():
    st.markdown('<h1 class="main-header">Upload Learning Materials</h1>', unsafe_allow_html=True)
    
    # Check if user is logged in for subscription-gated content
    if not st.session_state.user:
        st.warning("Please log in to upload and process learning materials.")
        st.session_state.auth_component.render_auth_forms()
        return
    
    # Check if user has active subscription
    if not st.session_state.user.get('subscription_active', False):
        st.warning("This feature requires an active subscription. Please subscribe to access all features.")
        # Show subscription options (placeholder)
        st.markdown("### Subscription Options")
        st.markdown("Contact an administrator to activate your subscription.")
        return
    
    # Render upload component
    st.session_state.upload_component.render_upload_section()
    st.session_state.upload_component.render_uploaded_files()

# Lessons page
def render_lessons_page():
    st.markdown('<h1 class="main-header">Lesson Explanations</h1>', unsafe_allow_html=True)
    
    # Check if user is logged in for subscription-gated content
    if not st.session_state.user:
        st.warning("Please log in to access lesson explanations.")
        st.session_state.auth_component.render_auth_forms()
        return
    
    # Check if user has active subscription
    if not st.session_state.user.get('subscription_active', False):
        st.warning("This feature requires an active subscription. Please subscribe to access all features.")
        # Show subscription options (placeholder)
        st.markdown("### Subscription Options")
        st.markdown("Contact an administrator to activate your subscription.")
        return
    
    # Render explanation component
    st.session_state.explanation_component.render_explanation_section()
    
    # Render TTS component if there's an explanation
    if 'current_explanation' in st.session_state and st.session_state.current_explanation:
        st.session_state.tts_component.render_audio_player()
    
    # Show explanation history
    st.session_state.explanation_component.render_explanation_history()

# Quizzes page
def render_quizzes_page():
    st.markdown('<h1 class="main-header">Quizzes & Assessments</h1>', unsafe_allow_html=True)
    
    # Check if user is logged in for subscription-gated content
    if not st.session_state.user:
        st.warning("Please log in to access quizzes and assessments.")
        st.session_state.auth_component.render_auth_forms()
        return
    
    # Check if user has active subscription
    if not st.session_state.user.get('subscription_active', False):
        st.warning("This feature requires an active subscription. Please subscribe to access all features.")
        # Show subscription options (placeholder)
        st.markdown("### Subscription Options")
        st.markdown("Contact an administrator to activate your subscription.")
        return
    
    # Render quiz component
    st.session_state.quiz_component.render_quiz_section()

# Reports page
def render_reports_page():
    st.markdown('<h1 class="main-header">Progress Reports</h1>', unsafe_allow_html=True)
    
    # Check if user is logged in for subscription-gated content
    if not st.session_state.user:
        st.warning("Please log in to access progress reports.")
        st.session_state.auth_component.render_auth_forms()
        return
    
    # Check if user has active subscription
    if not st.session_state.user.get('subscription_active', False):
        st.warning("This feature requires an active subscription. Please subscribe to access all features.")
        # Show subscription options (placeholder)
        st.markdown("### Subscription Options")
        st.markdown("Contact an administrator to activate your subscription.")
        return
    
    # Render report component
    st.session_state.report_component.render_report_section()

# Admin pages (placeholder)
def render_admin_users_page():
    st.markdown('<h1 class="main-header">Admin: Manage Users</h1>', unsafe_allow_html=True)
    
    # Check if user is admin
    if not st.session_state.user or not st.session_state.user.get('is_admin', False):
        st.error("You don't have permission to access this page.")
        return
    
    st.markdown("### User Management")
    st.markdown("This is a placeholder for the user management interface.")

def render_admin_invites_page():
    st.markdown('<h1 class="main-header">Admin: Generate Invites</h1>', unsafe_allow_html=True)
    
    # Check if user is admin
    if not st.session_state.user or not st.session_state.user.get('is_admin', False):
        st.error("You don't have permission to access this page.")
        return
    
    st.markdown("### Invite Management")
    
    # Form to generate new invite
    with st.form("generate_invite"): 
        st.markdown("#### Generate New Invite")
        email = st.text_input("Email Address (optional)")
        expires_in = st.slider("Expires in (days)", 1, 30, 7)
        
        submitted = st.form_submit_button("Generate Invite Link")
        if submitted:
            invite_id, token = st.session_state.db.create_invite_link(
                st.session_state.user['id'],
                email,
                expires_in
            )
            
            # Display the invite link
            invite_link = f"http://yourdomain.com/signup?invite={token}" # Placeholder URL
            st.success(f"Invite link generated successfully!")
            st.code(invite_link)
            st.markdown("Copy this link and share it with the user.")

# Main app routing
def main():
    # Render sidebar
    render_sidebar()
    
    # Render current page based on navigation state (Corrected Indentation)
    if st.session_state.current_page == "Home":
        render_home_page()
    elif st.session_state.current_page == "Upload":
        render_upload_page()
    elif st.session_state.current_page == "Lessons":
        render_lessons_page()
    elif st.session_state.current_page == "Quizzes":
        render_quizzes_page()
    elif st.session_state.current_page == "Reports":
        render_reports_page()
    elif st.session_state.current_page == "Admin_Users":
        render_admin_users_page()
    elif st.session_state.current_page == "Admin_Invites":
        render_admin_invites_page()
    else:
        # Default to home page
        render_home_page()

if __name__ == "__main__":
    main()

