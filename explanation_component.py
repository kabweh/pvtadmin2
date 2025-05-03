"""
Streamlit component for lesson explanation in the AI Tutor application.
Provides UI elements for explaining uploaded content.
"""
import streamlit as st
from typing import Dict, Any, Optional

# Use relative import within the package
from lesson_explainer import LessonExplainer

class ExplanationComponent:
    """
    Streamlit component for handling lesson explanations in the AI Tutor application.
    """
    
    def __init__(self, lesson_explainer: LessonExplainer):
        """
        Initialize the explanation component.
        
        Args:
            lesson_explainer: Instance of LessonExplainer to generate explanations
        """
        self.lesson_explainer = lesson_explainer
        
        # Create session state variables if they don't exist
        if 'content_to_explain' not in st.session_state:
            st.session_state.content_to_explain = None
        
        if 'current_explanation' not in st.session_state:
            st.session_state.current_explanation = None
        
        if 'explanation_history' not in st.session_state:
            st.session_state.explanation_history = []
    
    def render_explanation_section(self) -> None:
        """
        Render the explanation section in the Streamlit UI.
        """
        st.header("Lesson Explanations")
        
        # Show explanation options
        complexity_level = st.radio(
            "Explanation complexity:",
            options=["simple", "medium", "advanced"],
            index=1,  # Default to medium
            horizontal=True
        )
        
        # Check if there's content to explain from upload component
        if st.session_state.content_to_explain:
            with st.expander("Content to explain", expanded=True):
                st.write(f"**Source:** {st.session_state.content_to_explain['source']}")
                st.text_area(
                    "Content",
                    value=st.session_state.content_to_explain['text'],
                    height=200,
                    disabled=True
                )
            
            # Generate explanation button
            if st.button("Generate Explanation"):
                with st.spinner("Generating explanation..."):
                    explanation = self.lesson_explainer.generate_explanation(
                        st.session_state.content_to_explain['text'],
                        complexity_level
                    )
                    
                    # Store in session state
                    st.session_state.current_explanation = {
                        'text': explanation,
                        'source': st.session_state.content_to_explain['source'],
                        'complexity': complexity_level
                    }
                    
                    # Add to history
                    st.session_state.explanation_history.append(st.session_state.current_explanation)
                    
                    # Clear content to explain
                    st.session_state.content_to_explain = None
                    
                    # Rerun to update UI
                    st.experimental_rerun()
        
        # Display current explanation if available
        if st.session_state.current_explanation:
            st.subheader("Explanation")
            st.info(f"Explaining content from: {st.session_state.current_explanation['source']} (Complexity: {st.session_state.current_explanation['complexity']})")
            st.write(st.session_state.current_explanation['text'])
            
            # Text-to-speech button placeholder (will be implemented in TTS component)
            # st.button("Listen to Explanation", disabled=True, help="Text-to-speech feature will be implemented soon")
            # Note: TTS component will render its own button if needed
    
    def render_explanation_history(self) -> None:
        """
        Render the history of generated explanations.
        """
        if not st.session_state.explanation_history:
            return
        
        st.header("Explanation History")
        
        for idx, explanation in enumerate(reversed(st.session_state.explanation_history)):
            with st.expander(f"Explanation for {explanation['source']} ({explanation['complexity']})"):
                st.write(explanation['text'])
                
                # Button to set as current explanation
                if st.button(f"View Again", key=f"view_again_{idx}"):
                    st.session_state.current_explanation = explanation
                    st.experimental_rerun()
    
    def explain_content(self, text: str, source: str, complexity_level: str = "medium") -> None:
        """
        Set content to be explained.
        
        Args:
            text: Text content to explain
            source: Source of the content (e.g., filename)
            complexity_level: Desired complexity level
        """
        st.session_state.content_to_explain = {
            'text': text,
            'source': source
        }
    
    def get_current_explanation(self) -> Optional[Dict[str, Any]]:
        """
        Get the current explanation from session state.
        
        Returns:
            Dictionary containing explanation information or None
        """
        return st.session_state.current_explanation

