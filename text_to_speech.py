"""
Text-to-speech module for AI Tutor application.
Provides functionality to convert text to speech using gTTS.
"""
import os
import uuid
import tempfile
from typing import Dict, Optional
from gtts import gTTS

class TextToSpeech:
    """
    Handles text-to-speech conversion for the AI Tutor application.
    Uses Google Text-to-Speech (gTTS) library.
    """
    
    def __init__(self, audio_folder: str = "static/audio"):
        """
        Initialize the text-to-speech handler.
        
        Args:
            audio_folder: Directory to store generated audio files
        """
        self.audio_folder = audio_folder
        os.makedirs(audio_folder, exist_ok=True)
    
    def generate_speech(self, text: str, lang: str = 'en', slow: bool = False) -> Dict:
        """
        Convert text to speech and save as an audio file.
        
        Args:
            text: Text content to convert to speech
            lang: Language code (default: 'en' for English)
            slow: Whether to speak slowly (default: False)
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(self.audio_folder, filename)
            
            # Create gTTS object and save to file
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "filename": filename,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "file_path": None,
                "filename": None,
                "error": str(e)
            }
    
    def generate_speech_for_explanation(self, explanation_text: str) -> Dict:
        """
        Generate speech specifically for lesson explanations.
        
        Args:
            explanation_text: The explanation text to convert
            
        Returns:
            Dictionary containing file information
        """
        # For explanations, we want to ensure the text is properly formatted
        # and not too long for gTTS to handle
        
        # Split text into manageable chunks if it's very long
        if len(explanation_text) > 5000:
            # Find a good breaking point (end of sentence) around the 5000 character mark
            split_point = explanation_text[:5000].rfind('.')
            if split_point == -1:  # No period found, try other punctuation
                split_point = explanation_text[:5000].rfind('!')
            if split_point == -1:
                split_point = explanation_text[:5000].rfind('?')
            if split_point == -1:  # Still no good break point, just use 5000
                split_point = 5000
            
            # Generate speech for first chunk
            first_chunk = explanation_text[:split_point+1]
            result = self.generate_speech(first_chunk)
            
            # If there's more text, recursively process it and combine results
            if split_point+1 < len(explanation_text):
                remaining_text = explanation_text[split_point+1:]
                remaining_result = self.generate_speech_for_explanation(remaining_text)
                
                # If both succeeded, return the first chunk's info
                if result["success"] and remaining_result["success"]:
                    return result
                # If first chunk failed but second succeeded, return second
                elif remaining_result["success"]:
                    return remaining_result
            
            return result
        else:
            # Text is a manageable size, process normally
            return self.generate_speech(explanation_text)
    
    def get_audio_url(self, filename: Optional[str]) -> Optional[str]:
        """
        Get the URL for an audio file.
        
        Args:
            filename: Name of the audio file
            
        Returns:
            URL path to the audio file or None if filename is None
        """
        if not filename:
            return None
        
        return f"/{self.audio_folder}/{filename}"
