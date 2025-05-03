"""
Streamlit component for quiz functionality in the AI Tutor application.
Provides UI elements for taking quizzes and viewing results.
"""
import streamlit as st
import json
from typing import Dict, List, Any, Optional

# Use relative imports within the package
from quiz_generator import QuizGenerator
from database import Database

class QuizComponent:
    """
    Streamlit component for handling quizzes in the AI Tutor application.
    """
    
    def __init__(self, quiz_generator: QuizGenerator, database: Database):
        """
        Initialize the quiz component.
        
        Args:
            quiz_generator: Instance of QuizGenerator to generate quizzes
            database: Instance of Database to store quiz results
        """
        self.quiz_generator = quiz_generator
        self.database = database
        
        # Create session state variables if they don't exist
        if 'current_quiz' not in st.session_state:
            st.session_state.current_quiz = None
        
        if 'quiz_attempt_id' not in st.session_state:
            st.session_state.quiz_attempt_id = None
        
        if 'quiz_responses' not in st.session_state:
            st.session_state.quiz_responses = {}
        
        if 'quiz_results' not in st.session_state:
            st.session_state.quiz_results = None
    
    def render_quiz_generator(self) -> None:
        """
        Render the quiz generation section in the Streamlit UI.
        """
        st.header("Generate Quiz")
        
        # Check if there's content to create a quiz from
        if 'current_explanation' in st.session_state and st.session_state.current_explanation:
            explanation = st.session_state.current_explanation
            
            st.write(f"Generate a quiz based on the explanation for: **{explanation['source']}**")
            
            num_questions = st.slider(
                "Number of questions",
                min_value=3,
                max_value=10,
                value=5,
                step=1
            )
            
            if st.button("Generate Quiz"):
                with st.spinner("Generating quiz questions..."):
                    # Generate quiz
                    quiz = self.quiz_generator.generate_quiz(
                        explanation['text'],
                        f"Quiz on {explanation['source']}",
                        num_questions
                    )
                    
                    # Store in session state
                    st.session_state.current_quiz = quiz
                    st.session_state.quiz_responses = {}
                    st.session_state.quiz_results = None
                    
                    # Create quiz in database if user is logged in
                    if 'user' in st.session_state and st.session_state.user:
                        quiz_id = self.database.create_quiz(
                            quiz['title'],
                            quiz['source_material'],
                            st.session_state.user['id']
                        )
                        
                        # Add questions to database
                        for q_idx, question in enumerate(quiz['questions']):
                            self.database.add_question(
                                quiz_id,
                                question['question_text'],
                                question['question_type'],
                                question['correct_answer'],
                                question['options']
                            )
                        
                        # Start quiz attempt
                        attempt_id = self.database.start_quiz_attempt(
                            quiz_id,
                            st.session_state.user['id']
                        )
                        
                        st.session_state.quiz_attempt_id = attempt_id
                    
                    st.success("Quiz generated successfully!")
                    st.experimental_rerun()
        else:
            st.info("Generate an explanation first to create a quiz based on it.")
    
    def render_quiz_taking(self) -> None:
        """
        Render the quiz-taking section in the Streamlit UI.
        """
        if not st.session_state.current_quiz:
            return
        
        quiz = st.session_state.current_quiz
        
        st.header(quiz['title'])
        st.write("Answer the following questions based on the material you've learned.")
        
        # Display each question
        for i, question in enumerate(quiz['questions']):
            st.subheader(f"Question {i+1}")
            st.write(question['question_text'])
            
            # Different input based on question type
            if question['question_type'] == 'multiple_choice':
                options = json.loads(question['options'])
                
                # Use radio buttons for multiple choice
                response = st.radio(
                    "Select your answer:",
                    options,
                    key=f"q_{i}",
                    index=None # Start with no selection
                )
                
                # Store response in session state
                if response is not None: # Check if a selection was made
                    st.session_state.quiz_responses[i] = {
                        'question_id': i,
                        'response': response,
                        'is_correct': response == question['correct_answer']
                    }
            
            elif question['question_type'] == 'short_answer':
                # Use text input for short answer
                response = st.text_area(
                    "Your answer:",
                    key=f"q_{i}",
                    height=100
                )
                
                # Store response in session state
                if response: # Check if response is not empty
                    # For short answer, we'll do a simple check if key terms are present
                    correct_terms = set(question['correct_answer'].lower().split())
                    response_terms = set(response.lower().split())
                    
                    # Calculate overlap
                    overlap = len(correct_terms.intersection(response_terms))
                    is_correct = overlap >= len(correct_terms) * 0.5  # At least 50% of terms
                    
                    st.session_state.quiz_responses[i] = {
                        'question_id': i,
                        'response': response,
                        'is_correct': is_correct
                    }
            
            st.markdown("---")
        
        # Submit button
        if st.button("Submit Quiz"):
            if len(st.session_state.quiz_responses) < len(quiz['questions']):
                st.warning("Please answer all questions before submitting.")
            else:
                self._process_quiz_submission()
                st.experimental_rerun() # Rerun to show results
    
    def _process_quiz_submission(self) -> None:
        """Process quiz submission and calculate results."""
        quiz = st.session_state.current_quiz
        responses = st.session_state.quiz_responses
        
        # Calculate score
        correct_count = sum(1 for resp in responses.values() if resp['is_correct'])
        total_questions = len(quiz['questions'])
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Prepare results
        results = {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'questions': []
        }
        
        # Add detailed question results
        for i, question in enumerate(quiz['questions']):
            response = responses.get(i, {})
            
            question_result = {
                'question_text': question['question_text'],
                'question_type': question['question_type'],
                'correct_answer': question['correct_answer'],
                'user_response': response.get('response', 'No answer'),
                'is_correct': response.get('is_correct', False)
            }
            
            results['questions'].append(question_result)
        
        # Store results in session state
        st.session_state.quiz_results = results
        
        # Record in database if user is logged in
        if 'user' in st.session_state and st.session_state.user and st.session_state.quiz_attempt_id:
            # Record each response
            for i, response in responses.items():
                # Find the actual question ID from the database if possible
                # For now, using index 'i' as a placeholder for question_db_id
                question_db_id = i # Placeholder - ideally fetch real ID
                self.database.record_question_response(
                    st.session_state.quiz_attempt_id,
                    question_db_id, 
                    response['response'],
                    response['is_correct']
                )
            
            # Complete the attempt
            self.database.complete_quiz_attempt(
                st.session_state.quiz_attempt_id,
                correct_count,
                total_questions
            )
    
    def render_quiz_results(self) -> None:
        """
        Render the quiz results section in the Streamlit UI.
        """
        if not st.session_state.quiz_results:
            return
        
        results = st.session_state.quiz_results
        
        st.header("Quiz Results")
        
        # Display score
        score_percentage = results['score']
        st.subheader(f"Your Score: {results['correct_count']}/{results['total_questions']} ({score_percentage:.1f}%)")
        
        # Display feedback based on score
        if score_percentage >= 80:
            st.success("Excellent work! You have a strong understanding of this material.")
        elif score_percentage >= 60:
            st.info("Good job! You understand most of the material, but there's room for improvement.")
        else:
            st.warning("You might need to review this material again to improve your understanding.")
        
        # Display detailed results for each question
        st.subheader("Question Details")
        
        for i, question in enumerate(results['questions']):
            # Use a more descriptive expander title
            status_icon = "✅" if question['is_correct'] else "❌"
            with st.expander(f"{status_icon} Question {i+1}"):
                st.write(f"**Question:** {question['question_text']}")
                st.write(f"**Your Answer:** {question['user_response']}")
                st.write(f"**Correct Answer:** {question['correct_answer']}")
                
                if question['is_correct']:
                    st.success("Your answer is correct!")
                else:
                    st.error("Your answer is incorrect.")
                    
                    # Provide explanation (placeholder)
                    st.write("**Explanation:** The correct answer can be found in the lesson material.")
        
        # Option to retake or create new quiz
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Retake Quiz"):
                st.session_state.quiz_responses = {}
                st.session_state.quiz_results = None
                # Reset attempt ID if needed, or start new attempt
                # st.session_state.quiz_attempt_id = None 
                st.experimental_rerun()
        
        with col2:
            if st.button("New Quiz"):
                st.session_state.current_quiz = None
                st.session_state.quiz_responses = {}
                st.session_state.quiz_results = None
                st.session_state.quiz_attempt_id = None
                st.experimental_rerun()
    
    def render_quiz_section(self) -> None:
        """
        Render the complete quiz section in the Streamlit UI.
        """
        st.title("Quizzes & Assessments")
        
        # If we have results, show them
        if st.session_state.quiz_results:
            self.render_quiz_results()
        # If we have a current quiz but no results, show the quiz
        elif st.session_state.current_quiz:
            self.render_quiz_taking()
        # Otherwise, show the quiz generator
        else:
            self.render_quiz_generator()
    
    def get_quiz_history(self, user_id: int) -> List[Dict]:
        """
        Get quiz history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of dictionaries containing quiz attempt information
        """
        return self.database.get_user_quiz_history(user_id)

