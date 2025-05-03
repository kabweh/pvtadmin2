"""
PDF upload and text extraction module for AI Tutor application.
Handles PDF files and extracts text using PyPDF2 and poppler-utils.
"""
import os
import subprocess
import tempfile
from typing import Tuple, Optional
import PyPDF2

class PDFHandler:
    """Handles PDF uploads and text extraction."""
    
    def __init__(self, upload_folder: str = "uploads/pdfs"):
        """
        Initialize the PDF handler.
        
        Args:
            upload_folder: Directory to store uploaded PDFs
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_pdf(self, pdf_file, filename: str) -> str:
        """
        Save an uploaded PDF file to disk.
        
        Args:
            pdf_file: The uploaded PDF file object
            filename: Name to save the file as
            
        Returns:
            Path to the saved PDF file
        """
        file_path = os.path.join(self.upload_folder, filename)
        
        # Save the PDF file
        with open(file_path, 'wb') as f:
            f.write(pdf_file.read())
            
        return file_path
    
    def extract_text_with_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text from a PDF using PyPDF2.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check if the PDF is encrypted
                if reader.is_encrypted:
                    return "This PDF is encrypted and requires a password for text extraction."
                
                # Extract text from each page
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                    
            return text
        except Exception as e:
            return f"Error extracting text with PyPDF2: {str(e)}"
    
    def extract_text_with_pdftotext(self, pdf_path: str) -> str:
        """
        Extract text from a PDF using poppler-utils' pdftotext.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            # Create a temporary file to store the extracted text
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Run pdftotext command
            result = subprocess.run(
                ['pdftotext', '-layout', pdf_path, temp_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return f"Error using pdftotext: {result.stderr}"
            
            # Read the extracted text
            with open(temp_path, 'r') as f:
                text = f.read()
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return text
        except Exception as e:
            return f"Error extracting text with pdftotext: {str(e)}"
    
    def process_pdf(self, pdf_file, filename: str) -> Tuple[str, Optional[str]]:
        """
        Process an uploaded PDF: save it and extract text.
        
        Args:
            pdf_file: The uploaded PDF file object
            filename: Name to save the file as
            
        Returns:
            Tuple containing (file_path, extracted_text)
        """
        file_path = self.save_pdf(pdf_file, filename)
        
        # Try extracting text with poppler-utils first (preferred method)
        extracted_text = self.extract_text_with_pdftotext(file_path)
        
        # If poppler-utils fails or returns empty text, fall back to PyPDF2
        if not extracted_text or "Error" in extracted_text:
            extracted_text = self.extract_text_with_pypdf2(file_path)
        
        return file_path, extracted_text
