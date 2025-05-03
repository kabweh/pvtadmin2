"""
Database module for AI Tutor application.
Sets up SQLite database for storing quiz results and user data.
"""
import os
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
import datetime
import secrets

class Database:
    """
    Handles database operations for the AI Tutor application.
    Uses SQLite for storing quiz results and user data.
    """

    def __init__(self, db_path: str = "ai_tutor.db"):
        """
        Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.initialize_db()

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection, creating one if it doesn't exist.

        Returns:
            SQLite connection object
        """
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False) # Added check_same_thread=False for Streamlit
                self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            except sqlite3.Error as e:
                print(f"Database connection error: {e}")
                raise
        return self.conn

    def close_connection(self) -> None:
        """Close the database connection if it exists."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_db(self) -> None:
        """Create database tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subscription_active BOOLEAN DEFAULT 0,
            subscription_expires TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0
        )
        """)

        # Create invite_links table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            email TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            used_by INTEGER,
            used_at TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (used_by) REFERENCES users (id)
        )
        """)

        # Create quizzes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source_material TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """)

        # Create questions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,  -- 'multiple_choice' or 'short_answer'
            correct_answer TEXT,
            options TEXT,  -- JSON string for multiple choice options
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
        """)

        # Create quiz_attempts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            score REAL,
            max_score INTEGER,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Create question_responses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            user_response TEXT,
            is_correct BOOLEAN,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts (id),
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
        """)

        # Create progress_reports table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_path TEXT,
            emailed_to TEXT,
            emailed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        conn.commit()

    # User management methods
    def add_user(self, username: str, password_hash: str, email: Optional[str] = None, is_admin: bool = False) -> int:
        """
        Add a new user to the database.

        Args:
            username: User's username
            password_hash: Hashed password
            email: User's email address (optional)
            is_admin: Whether the user should be an admin

        Returns:
            User ID of the newly created user or -1 if integrity error
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, ?)",
                (username, password_hash, email, is_admin)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Username or email already exists
            return -1

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user information by username.

        Args:
            username: User's username

        Returns:
            Dictionary containing user information or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            return dict(user)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user information by user ID.

        Args:
            user_id: User's ID

        Returns:
            Dictionary containing user information or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            return dict(user)
        return None

    def is_user_admin(self, user_id: int) -> bool:
        """
        Check if a user is an administrator.

        Args:
            user_id: User's ID

        Returns:
            True if the user is an admin, False otherwise.
        """
        user = self.get_user_by_id(user_id)
        return user is not None and bool(user.get('is_admin', 0))

    # Invite link methods
    def create_invite_link(self, created_by: int, email: Optional[str] = None, expires_in_days: int = 7) -> Tuple[int, str]:
        """
        Create a new invite link.

        Args:
            created_by: User ID of the creator
            email: Email address the invite is for (optional)
            expires_in_days: Number of days until the invite expires

        Returns:
            Tuple of (invite_id, token)
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.now() + datetime.timedelta(days=expires_in_days)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO invite_links (token, email, created_by, expires_at) VALUES (?, ?, ?, ?)",
            (token, email, created_by, expires_at)
        )
        conn.commit()

        return cursor.lastrowid, token

    def use_invite_link(self, token: str, user_id: int) -> bool:
        """
        Mark an invite link as used.

        Args:
            token: The invite token
            user_id: User ID of the user who used the invite

        Returns:
            True if successful, False if token is invalid, expired, or already used
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if token exists and is not used
        cursor.execute(
            "SELECT id, expires_at FROM invite_links WHERE token = ? AND used = 0",
            (token,)
        )
        invite = cursor.fetchone()

        if not invite:
            return False

        # Check if token is expired
        invite_id = invite["id"]
        try:
            expires_at = datetime.datetime.fromisoformat(invite["expires_at"])
        except ValueError:
             # Handle cases where expires_at might not be in ISO format (though it should be)
             return False

        if expires_at < datetime.datetime.now():
            return False

        # Mark as used
        cursor.execute(
            "UPDATE invite_links SET used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id, invite_id)
        )
        conn.commit()

        return True

    def get_active_invites_by_creator(self, creator_id: int) -> List[Dict]:
        """
        Get all active (unused and not expired) invite links created by a specific user.

        Args:
            creator_id: User ID of the creator

        Returns:
            List of dictionaries containing active invite link information
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now_iso = datetime.datetime.now().isoformat()

        cursor.execute(
            "SELECT * FROM invite_links WHERE created_by = ? AND used = 0 AND expires_at > ? ORDER BY created_at DESC",
            (creator_id, now_iso)
        )
        invites = cursor.fetchall()
        return [dict(invite) for invite in invites]

    # Quiz methods
    def create_quiz(self, title: str, source_material: str, created_by: Optional[int] = None) -> int:
        """
        Create a new quiz.

        Args:
            title: Quiz title
            source_material: Source material the quiz is based on
            created_by: User ID of the creator (optional)

        Returns:
            Quiz ID of the newly created quiz
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO quizzes (title, source_material, created_by) VALUES (?, ?, ?)",
            (title, source_material, created_by)
        )
        conn.commit()

        return cursor.lastrowid

    def add_question(self, quiz_id: int, question_text: str, question_type: str,
                    correct_answer: str, options: Optional[str] = None) -> int:
        """
        Add a question to a quiz.

        Args:
            quiz_id: Quiz ID
            question_text: The question text
            question_type: Type of question ('multiple_choice' or 'short_answer')
            correct_answer: The correct answer
            options: JSON string of options for multiple choice questions

        Returns:
            Question ID of the newly created question
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO questions (quiz_id, question_text, question_type, correct_answer, options) VALUES (?, ?, ?, ?, ?)",
            (quiz_id, question_text, question_type, correct_answer, options)
        )
        conn.commit()

        return cursor.lastrowid

    def get_quiz_with_questions(self, quiz_id: int) -> Optional[Dict]:
        """
        Get a quiz with all its questions.

        Args:
            quiz_id: Quiz ID

        Returns:
            Dictionary containing quiz information and questions or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get quiz information
        cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return None

        quiz_dict = dict(quiz)

        # Get questions
        cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions = cursor.fetchall()

        quiz_dict["questions"] = [dict(q) for q in questions]

        return quiz_dict

    # Quiz attempt methods
    def start_quiz_attempt(self, quiz_id: int, user_id: int) -> int:
        """
        Start a new quiz attempt.

        Args:
            quiz_id: Quiz ID
            user_id: User ID

        Returns:
            Attempt ID of the newly created attempt
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO quiz_attempts (quiz_id, user_id) VALUES (?, ?)",
            (quiz_id, user_id)
        )
        conn.commit()

        return cursor.lastrowid

    def record_question_response(self, attempt_id: int, question_id: int,
                                user_response: str, is_correct: bool) -> int:
        """
        Record a user's response to a question.

        Args:
            attempt_id: Attempt ID
            question_id: Question ID
            user_response: User's response
            is_correct: Whether the response is correct

        Returns:
            Response ID of the newly created response
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO question_responses (attempt_id, question_id, user_response, is_correct) VALUES (?, ?, ?, ?)",
            (attempt_id, question_id, user_response, is_correct)
        )
        conn.commit()

        return cursor.lastrowid

    def complete_quiz_attempt(self, attempt_id: int, score: float, max_score: int) -> bool:
        """
        Complete a quiz attempt and record the score.

        Args:
            attempt_id: Attempt ID
            score: Score achieved
            max_score: Maximum possible score

        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE quiz_attempts SET completed_at = CURRENT_TIMESTAMP, score = ?, max_score = ? WHERE id = ?",
            (score, max_score, attempt_id)
        )
        conn.commit()

        return True

    # Progress report methods
    def add_progress_report(self, user_id: int, title: str, report_path: str) -> int:
        """
        Add a new progress report.

        Args:
            user_id: User ID
            title: Report title
            report_path: Path to the report file

        Returns:
            Report ID of the newly created report
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO progress_reports (user_id, title, report_path) VALUES (?, ?, ?)",
            (user_id, title, report_path)
        )
        conn.commit()

        return cursor.lastrowid

    def update_report_email_status(self, report_id: int, emailed_to: str) -> bool:
        """
        Update the email status of a progress report.

        Args:
            report_id: Report ID
            emailed_to: Email address the report was sent to

        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE progress_reports SET emailed_to = ?, emailed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (emailed_to, report_id)
        )
        conn.commit()

        return True

    def get_user_quiz_history(self, user_id: int) -> List[Dict]:
        """
        Get a user's quiz attempt history.

        Args:
            user_id: User ID

        Returns:
            List of dictionaries containing quiz attempt information
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT qa.*, q.title as quiz_title
            FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            WHERE qa.user_id = ?
            ORDER BY qa.started_at DESC
        """, (user_id,))

        attempts = cursor.fetchall()
        return [dict(a) for a in attempts]

    def get_user_progress_reports(self, user_id: int) -> List[Dict]:
        """
        Get a user's progress reports.

        Args:
            user_id: User ID

        Returns:
            List of dictionaries containing progress report information
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM progress_reports WHERE user_id = ? ORDER BY generated_at DESC",
            (user_id,)
        )

        reports = cursor.fetchall()
        return [dict(r) for r in reports]

    def count_users(self) -> int:
        """Count the total number of users in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count

# End of class Database

