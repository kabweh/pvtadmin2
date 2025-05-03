"""
Streamlit component for file upload functionality in the AI Tutor application.
Provides UI elements for uploading and displaying files.
"""
import os
import streamlit as st
from typing import Dict, Any, List

# Use relative import within the package
from upload_manager import UploadManager

class UploadComponent:
    """
    Streamlit component for handling file uploads in the AI Tutor application.
    """
    
    def __init__(self, upload_manager: UploadManager):
        """
        Initialize the upload component.
        
        Args:
            upload_manager: Instance of UploadManager to handle file processing
        """
        self.upload_manager = upload_manager
        
        # Create session state variables if they don't exist
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
    
    def render_upload_section(self) -> None:
        """
        Render the file upload section in the Streamlit UI.
        """
        st.header("Upload Learning Materials")
        
        # File uploader widget
        st.write("Upload images (JPG/PNG), PDF, or DOCX files:")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["jpg", "jpeg", "png", "pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        # Process uploaded files when the upload button is clicked
        if uploaded_files and st.button("Process Uploads"):
            with st.spinner("Processing files..."):
                for uploaded_file in uploaded_files:
                    # Skip if file was already processed
                    if any(f['original_filename'] == uploaded_file.name for f in st.session_state.uploaded_files):
                        continue
                    
                    # Process the file
                    file_info = self.upload_manager.process_upload(uploaded_file, uploaded_file.name)
                    
                    # Add to session state if successful
                    if file_info["success"]:
                        st.session_state.uploaded_files.append(file_info)
                        st.success(f"Successfully processed: {uploaded_file.name}")
                    else:
                        st.error(f"Failed to process {uploaded_file.name}: {file_info['error']}")
    
    def render_uploaded_files(self) -> None:
        """
        Render the list of uploaded files with options to view content.
        """
        if not st.session_state.uploaded_files:
            st.info("No files have been uploaded yet.")
            return
        
        st.header("Uploaded Materials")
        
        for idx, file_info in enumerate(st.session_state.uploaded_files):
            with st.expander(f"{file_info['original_filename']} ({file_info['file_type'].upper()})"):
                # Display file information
                st.write(f"**File Type:** {file_info['file_type'].upper()}")
                
                # Display file preview based on type
                if file_info['file_type'] == 'image':
                    st.image(file_info['file_path'], caption=file_info['original_filename'])
                
                # Display extracted text if available
                if file_info['extracted_text']:
                    st.subheader("Extracted Text")
                    st.write(file_info['extracted_text'])
                    
                    # Add "Explain" button for this content
                    if st.button(f"Explain this content", key=f"explain_{idx}"):
                        st.session_state.content_to_explain = {
                            'text': file_info['extracted_text'],
                            'source': file_info['original_filename']
                        }
                        # This will trigger the explanation in the lesson system
                        # We might need a rerun here if the explanation component is separate
                        # st.experimental_rerun() # Consider if needed
                else:
                    st.write("No text could be extracted from this file.")
                
                # Option to remove file
                if st.button(f"Remove", key=f"remove_{idx}"):
                    # Remove file from session state
                    removed_file = st.session_state.uploaded_files.pop(idx)
                    # Optionally, remove the actual file from disk
                    # try:
                    #     if removed_file.get('file_path') and os.path.exists(removed_file['file_path']):
                    #         os.remove(removed_file['file_path'])
                    # except OSError as e:
                    #     st.warning(f"Could not remove file from disk: {e}")
                    st.experimental_rerun()
    
    def get_uploaded_files(self) -> List[Dict[str, Any]]:
        """
        Get the list of uploaded files from session state.
        
        Returns:
            List of dictionaries containing file information
        """
        return st.session_state.uploaded_files

