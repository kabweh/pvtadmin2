"""
Progress report generation module for AI Tutor application.
Generates PDF and HTML reports based on quiz results.
"""
import os
import datetime
from typing import Dict, List, Any, Optional
import jinja2
import weasyprint

class ReportGenerator:
    """
    Generates progress reports for the AI Tutor application.
    """
    
    def __init__(self, report_folder: str = "static/reports", template_folder: str = "templates"):
        """
        Initialize the report generator.
        
        Args:
            report_folder: Directory to store generated reports
            template_folder: Directory containing report templates
        """
        self.report_folder = report_folder
        self.template_folder = template_folder
        
        # Create folders if they don't exist
        os.makedirs(report_folder, exist_ok=True)
        os.makedirs(template_folder, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_folder),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self) -> None:
        """Create default HTML templates for reports if they don't exist."""
        # HTML report template
        html_template_path = os.path.join(self.template_folder, "progress_report.html")
        if not os.path.exists(html_template_path):
            with open(html_template_path, 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #2980b9;
            margin-top: 30px;
        }
        .summary {
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }
        .quiz-result {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 5px;
        }
        .quiz-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .score {
            font-size: 1.2em;
            font-weight: bold;
        }
        .high-score {
            color: #27ae60;
        }
        .medium-score {
            color: #f39c12;
        }
        .low-score {
            color: #e74c3c;
        }
        .improvement-areas {
            background-color: #fff8e1;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin-top: 20px;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 0.9em;
            color: #7f8c8d;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .chart-container {
            margin: 30px 0;
            height: 300px;
        }
    </style>
</head>
<body>
    <h1>{{ report_title }}</h1>
    
    <div class="summary">
        <p><strong>Student:</strong> {{ student_name }}</p>
        <p><strong>Report Period:</strong> {{ report_period }}</p>
        <p><strong>Generated On:</strong> {{ generation_date }}</p>
        <p><strong>Overall Progress:</strong> {{ overall_progress }}</p>
    </div>
    
    <h2>Quiz Performance Summary</h2>
    <p>Total Quizzes Taken: {{ total_quizzes }}</p>
    <p>Average Score: {{ average_score }}%</p>
    
    {% if quiz_results %}
    <h2>Recent Quiz Results</h2>
    {% for quiz in quiz_results %}
    <div class="quiz-result">
        <div class="quiz-header">
            <h3>{{ quiz.title }}</h3>
            <div class="score {% if quiz.score_percentage >= 80 %}high-score{% elif quiz.score_percentage >= 60 %}medium-score{% else %}low-score{% endif %}">
                Score: {{ quiz.score }}/{{ quiz.max_score }} ({{ quiz.score_percentage }}%)
            </div>
        </div>
        <p><strong>Date:</strong> {{ quiz.date }}</p>
        <p><strong>Topics:</strong> {{ quiz.topics }}</p>
        
        {% if quiz.questions %}
        <h4>Question Performance</h4>
        <table>
            <tr>
                <th>Question</th>
                <th>Your Answer</th>
                <th>Correct</th>
            </tr>
            {% for question in quiz.questions %}
            <tr>
                <td>{{ question.text }}</td>
                <td>{{ question.user_answer }}</td>
                <td>{% if question.is_correct %}✓{% else %}✗{% endif %}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}
    
    {% if improvement_areas %}
    <h2>Areas for Improvement</h2>
    <div class="improvement-areas">
        <ul>
        {% for area in improvement_areas %}
            <li>{{ area }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <h2>Progress Over Time</h2>
    <p>Your scores have {{ trend_description }} over the past {{ trend_period }}.</p>
    
    <div class="footer">
        <p>This report was automatically generated by AI Tutor.</p>
        <p>© {{ current_year }} AI Tutor. All rights reserved.</p>
    </div>
</body>
</html>""")
    
    def generate_html_report(self, report_data: Dict) -> str:
        """
        Generate an HTML progress report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Path to the generated HTML report
        """
        # Ensure report data has all required fields
        report_data.setdefault('report_title', 'Student Progress Report')
        report_data.setdefault('student_name', 'Student')
        report_data.setdefault('report_period', 'Last 30 days')
        report_data.setdefault('generation_date', datetime.datetime.now().strftime('%B %d, %Y'))
        report_data.setdefault('overall_progress', 'Good')
        report_data.setdefault('total_quizzes', 0)
        report_data.setdefault('average_score', 0)
        report_data.setdefault('quiz_results', [])
        report_data.setdefault('improvement_areas', [])
        report_data.setdefault('trend_description', 'remained consistent')
        report_data.setdefault('trend_period', 'month')
        report_data.setdefault('current_year', datetime.datetime.now().year)
        
        # Load template
        template = self.jinja_env.get_template('progress_report.html')
        
        # Render HTML
        html_content = template.render(**report_data)
        
        # Generate a unique filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"progress_report_{report_data['student_name'].replace(' ', '_').lower()}_{timestamp}.html"
        file_path = os.path.join(self.report_folder, filename)
        
        # Write HTML to file
        with open(file_path, 'w') as f:
            f.write(html_content)
        
        return file_path
    
    def generate_pdf_report(self, report_data: Dict) -> str:
        """
        Generate a PDF progress report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Path to the generated PDF report
        """
        # First generate HTML report
        html_path = self.generate_html_report(report_data)
        
        # Generate PDF filename
        pdf_path = html_path.replace('.html', '.pdf')
        
        # Convert HTML to PDF using WeasyPrint
        html = weasyprint.HTML(filename=html_path)
        html.write_pdf(pdf_path)
        
        return pdf_path
    
    def prepare_report_data(self, user_data: Dict, quiz_attempts: List[Dict], 
                           questions_data: Optional[Dict] = None) -> Dict:
        """
        Prepare data for a progress report.
        
        Args:
            user_data: Dictionary containing user information
            quiz_attempts: List of dictionaries containing quiz attempt information
            questions_data: Optional dictionary mapping attempt IDs to question responses
            
        Returns:
            Dictionary containing formatted report data
        """
        # Initialize report data
        report_data = {
            'report_title': f"Progress Report for {user_data.get('username', 'Student')}",
            'student_name': user_data.get('username', 'Student'),
            'report_period': 'Last 30 days',
            'generation_date': datetime.datetime.now().strftime('%B %d, %Y'),
            'total_quizzes': len(quiz_attempts),
            'current_year': datetime.datetime.now().year,
            'quiz_results': [],
            'improvement_areas': []
        }
        
        # Calculate average score
        if quiz_attempts:
            total_score_percentage = sum(
                attempt.get('score', 0) / attempt.get('max_score', 1) * 100 
                for attempt in quiz_attempts if attempt.get('max_score', 0) > 0
            )
            report_data['average_score'] = round(total_score_percentage / len(quiz_attempts), 1)
        else:
            report_data['average_score'] = 0
        
        # Determine overall progress based on average score
        if report_data['average_score'] >= 80:
            report_data['overall_progress'] = 'Excellent'
        elif report_data['average_score'] >= 70:
            report_data['overall_progress'] = 'Good'
        elif report_data['average_score'] >= 60:
            report_data['overall_progress'] = 'Satisfactory'
        else:
            report_data['overall_progress'] = 'Needs Improvement'
        
        # Format quiz results
        for attempt in quiz_attempts:
            score = attempt.get('score', 0)
            max_score = attempt.get('max_score', 1)
            score_percentage = round((score / max_score) * 100, 1) if max_score > 0 else 0
            
            quiz_result = {
                'title': attempt.get('quiz_title', 'Unnamed Quiz'),
                'date': datetime.datetime.fromisoformat(attempt.get('completed_at', '')).strftime('%B %d, %Y') if attempt.get('completed_at') else 'Incomplete',
                'score': score,
                'max_score': max_score,
                'score_percentage': score_percentage,
                'topics': 'General Knowledge',  # Placeholder, would be extracted from quiz content
                'questions': []
            }
            
            # Add question details if available
            if questions_data and attempt.get('id') in questions_data:
                quiz_result['questions'] = questions_data[attempt['id']]
            
            report_data['quiz_results'].append(quiz_result)
        
        # Sort quiz results by date (most recent first)
        report_data['quiz_results'].sort(
            key=lambda x: datetime.datetime.fromisoformat(x.get('date', '1970-01-01')) 
            if x.get('date') != 'Incomplete' else datetime.datetime.min,
            reverse=True
        )
        
        # Identify improvement areas
        low_scoring_topics = set()
        for quiz in report_data['quiz_results']:
            if quiz['score_percentage'] < 70:
                low_scoring_topics.add(quiz['topics'])
        
        if low_scoring_topics:
            for topic in low_scoring_topics:
                report_data['improvement_areas'].append(
                    f"Focus on improving understanding of {topic} concepts."
                )
        
        if report_data['average_score'] < 60:
            report_data['improvement_areas'].append(
                "Consider reviewing basic concepts across all topics."
            )
        
        if not report_data['improvement_areas']:
            report_data['improvement_areas'].append(
                "Continue practicing to maintain your excellent progress."
            )
        
        # Determine trend
        if len(quiz_attempts) >= 2:
            # Sort by date
            sorted_attempts = sorted(
                quiz_attempts,
                key=lambda x: datetime.datetime.fromisoformat(x.get('completed_at', '1970-01-01')) 
                if x.get('completed_at') else datetime.datetime.min
            )
            
            # Calculate scores for first and second half
            midpoint = len(sorted_attempts) // 2
            first_half = sorted_attempts[:midpoint]
            second_half = sorted_attempts[midpoint:]
            
            first_half_avg = sum(
                attempt.get('score', 0) / attempt.get('max_score', 1) * 100 
                for attempt in first_half if attempt.get('max_score', 0) > 0
            ) / len(first_half) if first_half else 0
            
            second_half_avg = sum(
                attempt.get('score', 0) / attempt.get('max_score', 1) * 100 
                for attempt in second_half if attempt.get('max_score', 0) > 0
            ) / len(second_half) if second_half else 0
            
            # Determine trend
            if second_half_avg > first_half_avg + 5:
                report_data['trend_description'] = 'improved significantly'
            elif second_half_avg > first_half_avg:
                report_data['trend_description'] = 'shown improvement'
            elif second_half_avg < first_half_avg - 5:
                report_data['trend_description'] = 'declined'
            else:
                report_data['trend_description'] = 'remained consistent'
        else:
            report_data['trend_description'] = 'not shown a clear trend yet due to limited data'
        
        return report_data
    
    def email_report(self, report_path: str, recipient_email: str, subject: str = None) -> Dict:
        """
        Email a progress report.
        
        Args:
            report_path: Path to the report file
            recipient_email: Email address to send the report to
            subject: Email subject (optional)
            
        Returns:
            Dictionary containing email status information
        """
        # This is a placeholder for email functionality
        # In a real implementation, this would use an email library like smtplib
        
        if not subject:
            subject = f"AI Tutor Progress Report - {datetime.datetime.now().strftime('%B %d, %Y')}"
        
        # Placeholder for email sending logic
        return {
            "success": True,
            "recipient": recipient_email,
            "subject": subject,
            "report_path": report_path,
            "sent_at": datetime.datetime.now().isoformat(),
            "message": f"Email would be sent to {recipient_email} with report {report_path}"
        }
