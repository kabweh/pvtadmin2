"""
Image upload and processing module for AI Tutor application.
Handles JPG/PNG files and extracts text using Tesseract OCR.
"""
import os
import tempfile
from typing import Tuple, Optional
from PIL import Image
import pytesseract

class ImageHandler:
    """Handles image uploads and text extraction using OCR."""
    
    def __init__(self, upload_folder: str = "uploads/images"):
        """
        Initialize the image handler.
        
        Args:
            upload_folder: Directory to store uploaded images
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_image(self, image_file, filename: str) -> str:
        """
        Save an uploaded image file to disk.
        
        Args:
            image_file: The uploaded image file object
            filename: Name to save the file as
            
        Returns:
            Path to the saved image file
        """
        file_path = os.path.join(self.upload_folder, filename)
        
        # Save the image using Pillow to ensure it's a valid image
        with Image.open(image_file) as img:
            img.save(file_path)
            
        return file_path
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        try:
            with Image.open(image_path) as img:
                # Convert image to RGB if it's in RGBA mode (e.g., PNG with transparency)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Use pytesseract to extract text
                text = pytesseract.image_to_string(img)
                return text
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def process_image(self, image_file, filename: str) -> Tuple[str, Optional[str]]:
        """
        Process an uploaded image: save it and extract text if possible.
        
        Args:
            image_file: The uploaded image file object
            filename: Name to save the file as
            
        Returns:
            Tuple containing (file_path, extracted_text)
        """
        file_path = self.save_image(image_file, filename)
        extracted_text = self.extract_text(file_path)
        
        return file_path, extracted_text
