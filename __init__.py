"""
__init__.py file for upload_handlers package.
Makes the package importable and exposes key classes.
"""
from upload_manager import UploadManager
from image_handler import ImageHandler
from pdf_handler import PDFHandler
from docx_handler import DOCXHandler

__all__ = ['UploadManager', 'ImageHandler', 'PDFHandler', 'DOCXHandler']
