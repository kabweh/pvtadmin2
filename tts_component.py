"""
Streamlit component for text-to-speech functionality in the AI Tutor application.
Provides UI elements for audio playback of explanations.
"""
import os
import streamlit as st
from typing import Dict, Any, Optional

# Use relative import within the package
from text_to_speech import TextToSpeech

class TTSComponent:
    """
    Streamlit component for handling text-to-speech in the AI Tutor application.
    """
    
    def __init__(self, tts_handler: TextToSpeech):
        """
        Initialize the TTS component.
        
        Args:
            tts_handler: Instance of TextToSpeech to handle audio generation
        """
        self.tts_handler = tts_handler
        
        # Create session state variables if they don't exist
        if 'current_audio' not in st.session_state:
            st.session_state.current_audio = None
    
    def render_audio_player(self, text: Optional[str] = None, source: Optional[str] = None) -> None:
        """
        Render the audio player for text-to-speech playback.
        
        Args:
            text: Text to convert to speech (if None, uses current explanation)
            source: Source of the text (for display purposes)
        """
        st.subheader("Text-to-Speech")
        
        # Get text from current explanation if not provided
        if text is None and 'current_explanation' in st.session_state:
            if st.session_state.current_explanation:
                text = st.session_state.current_explanation['text']
                source = st.session_state.current_explanation['source']
        
        if not text:
            st.info("No content available for text-to-speech. Generate an explanation first.")
            return
        
        # Generate speech button
        if st.button("Generate Audio"):
            with st.spinner("Converting text to speech..."):
                result = self.tts_handler.generate_speech_for_explanation(text)
                
                if result["success"]:
                    st.session_state.current_audio = result
                    st.success("Audio generated successfully!")
                else:
                    st.error(f"Failed to generate audio: {result['error']}")
        
        # Display audio player if audio is available
        if st.session_state.current_audio and st.session_state.current_audio["success"]:
            audio_path = st.session_state.current_audio["file_path"]
            
            if os.path.exists(audio_path):
                # Display audio controls
                st.write(f"**Audio for:** {source if source else 'Current explanation'}")
                
                # Use Streamlit's audio player
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                except Exception as e:
                    st.error(f"Error loading audio file: {e}")
                    # Attempt to delete potentially corrupted file
                    try:
                        os.remove(audio_path)
                        st.session_state.current_audio = None
                        st.warning("Removed potentially corrupted audio file. Please try generating again.")
                        st.experimental_rerun()
                    except Exception as del_e:
                        st.error(f"Could not remove corrupted audio file: {del_e}")
                    return

                # Custom controls for volume (Note: Streamlit's audio player has its own volume)
                # st.slider(
                #     "Volume", 
                #     min_value=0.0, 
                #     max_value=1.0, 
                #     value=0.5, 
                #     step=0.1,
                #     help="Adjust the volume of the audio playback"
                # )
                
                # Additional options
                # st.checkbox("Auto-play next explanation", value=False)
                
                # Option to delete audio
                if st.button("Clear Audio"):
                    if os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except Exception as e:
                            st.error(f"Failed to delete audio file: {str(e)}")
                    
                    st.session_state.current_audio = None
                    st.experimental_rerun()
            else:
                # If file path exists in state but not on disk, clear state
                st.warning("Audio file not found. It might have been cleared. Please generate again.")
                st.session_state.current_audio = None
                st.experimental_rerun()

    
    def generate_audio_for_text(self, text: str) -> Dict:
        """
        Generate audio for the given text.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Dictionary containing audio file information
        """
        return self.tts_handler.generate_speech_for_explanation(text)

