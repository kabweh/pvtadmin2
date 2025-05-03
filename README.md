# AI Tutor

AI Tutor is a comprehensive web application that provides personalized educational support through AI-powered explanations, text-to-speech functionality, and automated assessments. The application allows students to upload learning materials, receive conversational explanations, listen to lessons, take quizzes, and track their progress.

## Features

- **Material Upload**: Upload and process images (JPG/PNG), PDF, and DOCX files
- **Lesson Explanations**: Receive clear, conversational explanations of uploaded content
- **Text-to-Speech**: Listen to explanations with adjustable playback controls
- **Assessment & Progress Reports**: Take quizzes and generate detailed progress reports
- **User-Friendly Interface**: Clean, responsive design with intuitive navigation
- **Authentication & Subscription**: Invite-only signup and subscription management

## Installation

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR (for image text extraction)
- Poppler (for PDF processing)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-tutor.git
   cd ai-tutor
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install system dependencies:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils
   
   # For macOS
   brew install tesseract poppler
   ```

4. Run the application:
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage

### Admin Setup

1. The first user must be created manually in the database as an admin:
   ```python
   from auth import AuthManager
   from assessment import Database
   
   db = Database()
   auth = AuthManager(db)
   
   # Create admin user
   user_id = db.add_user("admin", auth._hash_password("your_password"), "admin@example.com")
   
   # Set as admin
   conn = db.get_connection()
   cursor = conn.cursor()
   cursor.execute("UPDATE users SET is_admin = 1, subscription_active = 1 WHERE id = ?", (user_id,))
   conn.commit()
   ```

2. Generate invite links for new users:
   - Log in as admin
   - Navigate to "Admin: Generate Invites" page
   - Create invite links and share them with users

### Student Usage

1. **Sign Up/Login**:
   - Use an invite link to create an account
   - Log in with your credentials

2. **Upload Materials**:
   - Navigate to "Upload Material" page
   - Upload images, PDFs, or DOCX files
   - View extracted text from your materials

3. **Get Explanations**:
   - Click "Explain" on any uploaded content
   - Choose complexity level (simple, medium, advanced)
   - View conversational explanations

4. **Listen to Lessons**:
   - Generate audio from explanations
   - Use playback controls to listen to the content

5. **Take Quizzes**:
   - Generate quizzes based on explanations
   - Answer multiple-choice and short-answer questions
   - View your results and performance

6. **Track Progress**:
   - Generate progress reports in HTML or PDF format
   - Email reports to parents or teachers
   - View improvement areas and trends

## Project Structure

```
ai_tutor/
├── upload_handlers/       # Handles file uploads and processing
├── lesson_system/         # Generates explanations for content
├── tts/                   # Text-to-speech functionality
├── assessment/            # Quiz generation and progress reporting
├── auth/                  # User authentication and subscription
├── tests/                 # Automated tests
├── static/                # Static assets (CSS, JS, images)
├── templates/             # HTML templates for reports
├── streamlit_app.py       # Main application entry point
└── requirements.txt       # Required packages
```

## Configuration

The application uses SQLite for data storage by default. The database file is created in the root directory as `ai_tutor.db`.

### Environment Variables

You can customize the application behavior with environment variables:

- `UPLOAD_FOLDER`: Directory for uploaded files (default: "uploads")
- `REPORT_FOLDER`: Directory for generated reports (default: "static/reports")
- `DATABASE_PATH`: Path to SQLite database file (default: "ai_tutor.db")

## Testing

Run the automated tests with pytest:

```bash
pytest
```

The tests cover all major components:
- Upload handlers
- Lesson explanation system
- Text-to-speech functionality
- Assessment and reporting
- Authentication and subscription

## Deployment

### Local Deployment

For local deployment, simply run:

```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect it to your GitHub repository
4. Set the main file path to `streamlit_app.py`

### Heroku Deployment

1. Create a `Procfile`:
   ```
   web: streamlit run streamlit_app.py
   ```

2. Deploy to Heroku:
   ```bash
   heroku create ai-tutor-app
   git push heroku main
   ```

## Subscription Management

The application includes a placeholder for subscription management using Stripe's test mode. In a production environment, you would need to:

1. Set up a Stripe account
2. Configure API keys in environment variables
3. Implement webhook handling for subscription events

## Limitations and Future Improvements

- The current implementation uses simplified explanation generation logic that could be enhanced with more sophisticated NLP techniques
- Quiz generation could be improved with better question formation and distractor generation
- The email functionality is currently a placeholder and would need to be connected to an actual email service

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Streamlit for the web application framework
- Tesseract OCR for image text extraction
- PyPDF2 and python-docx for document processing
- gTTS for text-to-speech conversion
- WeasyPrint for PDF report generation
