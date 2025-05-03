"""
Streamlit component for progress reports in the AI Tutor application.
Provides UI elements for viewing and generating reports.
"""
import streamlit as st
import os
from typing import Dict, List, Any, Optional

# Use relative imports within the package
from report_generator import ReportGenerator
from database import Database

class ReportComponent:
    """
    Streamlit component for handling progress reports in the AI Tutor application.
    """
    
    def __init__(self, report_generator: ReportGenerator, database: Database):
        """
        Initialize the report component.
        
        Args:
            report_generator: Instance of ReportGenerator to generate reports
            database: Instance of Database to retrieve quiz data
        """
        self.report_generator = report_generator
        self.database = database
    
    def render_report_section(self) -> None:
        """
        Render the progress report section in the Streamlit UI.
        """
        st.title("Progress Reports")
        
        # Check if user is logged in
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to view and generate progress reports.")
            # Optionally render login form here if needed
            # st.session_state.auth_component.render_auth_forms()
            return
        
        user = st.session_state.user
        
        # Get user's quiz history
        quiz_history = self.database.get_user_quiz_history(user['id'])
        
        # Get user's existing reports
        existing_reports = self.database.get_user_progress_reports(user['id'])
        
        # Display existing reports
        st.header("Your Reports")
        if existing_reports:
            for report in existing_reports:
                # Use report ID in keys to ensure uniqueness
                report_key_base = f"report_{report['id']}"
                with st.expander(f"{report['title']} - {report['generated_at']}"):
                    st.write(f"**Generated:** {report['generated_at']}")
                    
                    report_path = report['report_path']
                    if os.path.exists(report_path):
                        # Provide download button for PDF
                        if report_path.endswith('.pdf'):
                            try:
                                with open(report_path, "rb") as pdf_file:
                                    st.download_button(
                                        label="Download PDF Report",
                                        data=pdf_file,
                                        file_name=os.path.basename(report_path),
                                        mime="application/pdf",
                                        key=f"download_{report_key_base}"
                                    )
                            except Exception as e:
                                st.error(f"Error reading PDF file: {e}")
                        # Provide link for HTML (assuming served or accessible)
                        elif report_path.endswith('.html'):
                             # Note: Direct linking might not work in all deployment scenarios
                             # Consider serving static files or providing download
                             st.markdown(f"[View HTML Report]({report_path})", unsafe_allow_html=True)
                    else:
                        st.error("Report file not found. It might have been moved or deleted.")
                    
                    # Email status and functionality
                    st.markdown("--- E-mail Report ---")
                    if report['emailed_to']:
                        st.write(f"**Emailed to:** {report['emailed_to']} on {report['emailed_at']}")
                    else:
                        email_col1, email_col2 = st.columns([3, 1])
                        with email_col1:
                            email = st.text_input("Email address:", key=f"email_{report_key_base}")
                        with email_col2:
                            # Add space to align button vertically
                            st.write("&nbsp;", unsafe_allow_html=True) 
                            if st.button("Send", key=f"send_{report_key_base}"):
                                if email:
                                    with st.spinner("Sending report..."):
                                        # Send email
                                        email_result = self.report_generator.email_report(
                                            report_path,
                                            email,
                                            f"AI Tutor Progress Report - {report['title']}"
                                        )
                                        
                                        if email_result['success']:
                                            # Update database
                                            self.database.update_report_email_status(
                                                report['id'],
                                                email
                                            )
                                            st.success(f"Report sent to {email}")
                                            st.experimental_rerun() # Refresh to show status
                                        else:
                                            st.error(f"Failed to send email: {email_result.get('message', 'Unknown error')}")
                                else:
                                    st.warning("Please enter an email address.")
        else:
            st.info("No reports generated yet.")

        # Generate new report section
        st.header("Generate New Report")
        
        if not quiz_history:
            st.info("You haven't taken any quizzes yet. Complete some quizzes to generate a progress report.")
            return
        
        # Report options form
        with st.form(key="generate_report_form"):
            report_title = st.text_input("Report Title:", value=f"{user['username']}'s Progress Report")
            
            report_format = st.radio(
                "Report Format:",
                options=["HTML", "PDF"],
                index=1, # Default to PDF
                horizontal=True
            )
            
            include_email = st.checkbox("Email report when generated")
            email_address = ""
            if include_email:
                email_address = st.text_input("Email Address:")
            
            submitted = st.form_submit_button("Generate Report")
            if submitted:
                if include_email and not email_address:
                    st.warning("Please enter an email address if you want the report emailed.")
                else:
                    with st.spinner("Generating progress report..."):
                        # Prepare report data
                        report_data = self.report_generator.prepare_report_data(
                            user_data=user,
                            quiz_attempts=quiz_history
                        )
                        
                        # Generate report based on selected format
                        report_path = None
                        try:
                            if report_format == "HTML":
                                report_path = self.report_generator.generate_html_report(report_data)
                            else:  # PDF
                                report_path = self.report_generator.generate_pdf_report(report_data)
                        except Exception as e:
                            st.error(f"Error generating report file: {e}")
                        
                        if report_path:
                            # Add to database
                            report_id = self.database.add_progress_report(
                                user['id'],
                                report_title,
                                report_path
                            )
                            
                            st.success(f"Progress report generated successfully!")
                            
                            # Email if requested
                            if include_email and email_address:
                                email_result = self.report_generator.email_report(
                                    report_path,
                                    email_address,
                                    f"AI Tutor Progress Report - {report_title}"
                                )
                                
                                if email_result['success']:
                                    self.database.update_report_email_status(
                                        report_id,
                                        email_address
                                    )
                                    st.info(f"Report also sent to {email_address}")
                                else:
                                     st.warning(f"Report generated, but failed to send email: {email_result.get('message', 'Unknown error')}")
                            
                            # Refresh the page to show the new report in the list
                            st.experimental_rerun()
    
    def get_user_reports(self, user_id: int) -> List[Dict]:
        """
        Get progress reports for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of dictionaries containing progress report information
        """
        return self.database.get_user_progress_reports(user_id)

