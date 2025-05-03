"""
Main upload handler module for AI Tutor application.
Integrates all file type handlers and provides a unified interface.
"""
import os
import uuid
from typing import Dict, Tuple, Optional
from image_handler import ImageHandler
from pdf_handler import PDFHandler
from docx_handler import DOCXHandler

class UploadManager:
    """
    Unified manager for handling various file uploads.
    Integrates image, PDF, and DOCX handlers.
    """
    
    def __init__(self, base_upload_folder: str = "uploads"):
        """
        Initialize the upload manager with handlers for each file type.
        
        Args:
            base_upload_folder: Base directory for all uploads
        """
        self.base_upload_folder = base_upload_folder
        os.makedirs(base_upload_folder, exist_ok=True)
        
        # Initialize handlers for each file type
        self.image_handler = ImageHandler(os.path.join(base_upload_folder, "images"))
        self.pdf_handler = PDFHandler(os.path.join(base_upload_folder, "pdfs"))
        self.docx_handler = DOCXHandler(os.path.join(base_upload_folder, "docx"))
    
    def process_upload(self, file, original_filename: str) -> Dict:
        """
        Process an uploaded file based on its extension.
        
        Args:
            file: The uploaded file object
            original_filename: Original name of the uploaded file
            
        Returns:
            Dictionary containing file information and extracted text
        """
        # Generate a unique filename to prevent collisions
        file_ext = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        file_info = {
            "original_filename": original_filename,
            "saved_filename": unique_filename,
            "file_type": file_ext.lstrip('.'),
            "file_path": None,
            "extracted_text": None,
            "success": False,
            "error": None
        }
        
        try:
            # Process based on file extension
            if file_ext.lower() in ['.jpg', '.jpeg', '.png']:
                file_path, extracted_text = self.image_handler.process_image(file, unique_filename)
                file_info["file_type"] = "image"
            
            elif file_ext.lower() == '.pdf':
                file_path, extracted_text = self.pdf_handler.process_pdf(file, unique_filename)
                file_info["file_type"] = "pdf"
            
            elif file_ext.lower() == '.docx':
                file_path, extracted_text = self.docx_handler.process_docx(file, unique_filename)
                file_info["file_type"] = "docx"
            
            else:
                file_info["error"] = f"Unsupported file type: {file_ext}"
                return file_info
            
            # Update file info with results
            file_info["file_path"] = file_path
            file_info["extracted_text"] = extracted_text
            file_info["success"] = True
            
        except Exception as e:
            file_info["error"] = str(e)
        
        return file_info
    
    def get_file_path(self, filename: str, file_type: str) -> Optional[str]:
        """
        Get the full path to a saved file.
        
        Args:
            filename: Name of the saved file
            file_type: Type of the file (image, pdf, docx)
            
        Returns:
            Full path to the file or None if invalid type
        """
        if file_type == "image":
            return os.path.join(self.image_handler.upload_folder, filename)
        elif file_type == "pdf":
            return os.path.join(self.pdf_handler.upload_folder, filename)
        elif file_type == "docx":
            return os.path.join(self.docx_handler.upload_folder, filename)
        return None
