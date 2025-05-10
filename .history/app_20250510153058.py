import os
import uuid
import base64
import requests
import imaplib
import email
# import re
from flask_socketio import SocketIO, emit 
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from email import policy
from email.parser import BytesParser
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import logging
from database import (
    init_db, insert_submission, get_submissions, delete_submission, generate_app_id,
    insert_note, insert_communication, get_submission_by_id, get_notes, insert_reply, get_replies,
    insert_mca_loan_application, get_mca_loan_applications, get_mca_loan_application_by_id
)
from spam_filter import SpamFilter
from slack_utils import SlackNotifier

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize global instances
spam_filter = SpamFilter()
slack_notifier = SlackNotifier()

# Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
# Load environment variables
load_dotenv()
# Flask app setup
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, async_mode='gevent')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = os.getenv('SECRET_KEY')
# Initialize the database
init_db()
# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# Allow any file type for uploads
def allowed_file(filename):
    return '.' in filename
# Initialize Slack notifier
slack_notifier = SlackNotifier()
# Helper function to send Slack notifications
def send_slack_notification(message):
    """Send a notification message to Slack with better error handling."""
    try:
        slack_notifier.send_notification(message, level='info', additional_data={'type': 'form_submission'})
        logging.info("Slack notification sent successfully")
    except Exception as e:
        logging.error(f"Failed to send Slack notification: {str(e)}")
        # The error is logged but won't stop the application flow
# Helper function to send emails
def send_email(to_email, subject, html_content, attachments=[]):
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    # Attach files
    for attachment in attachments:
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment)}")
            msg.attach(part)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
# Function to create the PDF
def create_pdf(data, files, submission_time, browser, ip_address, unique_id, location, app_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.image('static/assets/img/Logo.png', 10, 8, 33)
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Business Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Company Name: {data.get('company_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Time in Business: {data.get('time_in_business', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Address: {data.get('address_line_1', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip_code', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Company Email: {data.get('company_email', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Company Phone: {data.get('company_phone', '')}", ln=True)
    pdf.cell(0, 5, txt=f"EIN / TAX ID Number: {data.get('ein', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Type of Business: {data.get('business_type', '')}", ln=True)
    pdf.ln(2)
    # Borrower Information
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Borrower Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Borrower Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Date of Birth: {data.get('borrower_dob', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('borrower_ownership', '')}", ln=True)
    pdf.cell(0, 5, txt=f"SSN: {data.get('borrower_ssn', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Phone: {data.get('borrower_phone', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Email: {data.get('borrower_email', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Preferred Method of Contact: {data.get('borrower_preferred_contact', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Address: {data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}", ln=True)
    pdf.ln(2)
    # Co-Applicant Information
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Co-Applicant Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Name: {data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Date of Birth: {data.get('coapplicant_dob', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('coapplicant_ownership', '')}", ln=True)
    pdf.cell(0, 5, txt=f"SSN: {data.get('coapplicant_ssn', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Phone: {data.get('coapplicant_phone', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Email: {data.get('coapplicant_email', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Address: {data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}", ln=True)
    pdf.ln(2)
    # Loan Request Information
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Loan Request Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Loan Amount: {data.get('loan_amount', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Max Down Payment: {data.get('max_down_payment', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Equipment & Seller Info: {data.get('equipment_seller_info', '')}", ln=True)
    pdf.ln(2)
    # Additional Information (Browser, IP Address, etc.)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Additional Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Browser: {browser or 'N/A'}", ln=True)
    pdf.cell(0, 5, txt=f"IP Address: {ip_address or 'N/A'}", ln=True)
    pdf.cell(0, 5, txt=f"Unique ID: {unique_id or 'N/A'}", ln=True)
    pdf.cell(0, 5, txt=f"Location: {location or 'N/A'}", ln=True)
    pdf.ln(2)
    # Signature (if available)
    if 'signature' in data:
        signature_data = data.get('signature', '').split(',')[1]
        signature_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}_signature.png")
        with open(signature_path, "wb") as fh:
            fh.write(base64.b64decode(signature_data))
        pdf.cell(0, 10, txt="Signature:", ln=True)
        pdf.image(signature_path, 10, pdf.get_y() + 10, 60)
        pdf.ln(20)
    # Attached Files
    if files:
        pdf.cell(0, 10, txt="Uploaded Files:", ln=True)
        for file in files:
            pdf.cell(0, 5, txt=os.path.basename(file), ln=True)
    pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}.pdf")
    pdf.output(pdf_filename)
    if os.path.exists(pdf_filename) and os.path.getsize(pdf_filename) > 0:
        return pdf_filename
    else:
        logging.error(f"Failed to generate PDF {pdf_filename}")
        return None
# Function to create PDF for MCA loan application
def create_mca_pdf(data, files, submission_time, browser, ip_address, unique_id, location, app_id):
    try:
        # Create PDF with watermark
        class PDFWithWatermark(FPDF):
            def header(self):
                # Add company logo in the top-right corner to avoid obstructing text
                self.image('static/assets/img/Logo.png', 170, 8, 30)
                
                # Add watermark that doesn't obstruct text
                self.set_font('Arial', 'B', 50)
                self.set_text_color(240, 240, 240)  # Very light gray for subtle watermark
                
                # Save the current position
                x, y = self.get_x(), self.get_y()
                
                # Center watermark diagonally across page
                self.rotate(45, 105, 140)
                self.text(30, 190, 'HEMPIRE ENTERPRISE')
                
                # Restore position and text color
                self.rotate(0)
                self.set_xy(x, y)
                self.set_text_color(0, 0, 0)  # Reset text color to black
                self.ln(40)  # Add some space after the header
                
        # Create PDF
        pdf = PDFWithWatermark()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_fill_color(240, 240, 240)  # Light gray background for title
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(190, 15, "MCA LOAN APPLICATION", 1, 1, 'C', fill=True)
        pdf.ln(5)
        
        # Application ID and Date with better formatting
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(95, 10, f"Application ID: {app_id}", 0, 0, 'L')
        pdf.cell(95, 10, f"Date: {submission_time.strftime('%m/%d/%Y %H:%M')}", 0, 1, 'R')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Business Information section with styled heading
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(210, 210, 210)  # Darker gray for section headers
        pdf.cell(190, 10, "Business Information", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # Create a function for adding field-value pairs with consistent formatting
        def add_field(field_name, value, height=8):
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, height, field_name, 0, 0)
            pdf.set_font("Arial", '', 11)
            # Handle potential None values or empty strings
            display_value = value if value else "N/A"
            # Replace any unicode characters with ASCII equivalents
            display_value = str(display_value).replace('\u2022', '-')
            pdf.multi_cell(130, height, display_value, 0, 'L')
        
        # Business Information fields
        add_field("Company Name:", data.get('company_name', ''))
        add_field("Time in Business:", data.get('time_in_business', ''))
        add_field("Business Industry:", data.get('business_industry', ''))
        add_field("Business Type:", data.get('business_type', ''))
        add_field("EIN/TAX ID:", data.get('ein', ''))
        
        # Address with better formatting
        business_address = f"{data.get('address_line_1', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip_code', '')}"
        add_field("Address:", business_address)
        
        add_field("Company Email:", data.get('company_email', ''))
        add_field("Company Phone:", data.get('company_phone', ''))
        
        # Borrower Information section
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(210, 210, 210)
        pdf.cell(190, 10, "Borrower Information", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # Borrower Information fields
        borrower_name = f"{data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}"
        add_field("Name:", borrower_name)
        add_field("Date of Birth:", data.get('borrower_dob', ''))
        add_field("Percent Ownership:", data.get('borrower_ownership', ''))
        add_field("SSN:", data.get('borrower_ssn', ''))
        add_field("Email:", data.get('borrower_email', ''))
        add_field("Phone:", data.get('borrower_phone', ''))
        add_field("Preferred Contact:", data.get('borrower_preferred_contact', ''))
        
        # Borrower address
        borrower_address = f"{data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}"
        add_field("Address:", borrower_address)
        
        # Co-Applicant Information (if provided)
        if data.get('coapplicant_first_name') or data.get('coapplicant_last_name'):
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 16)
            pdf.set_fill_color(210, 210, 210)
            pdf.cell(190, 10, "Co-Applicant Information", 0, 1, 'L', fill=True)
            pdf.ln(2)
            
            # Co-Applicant fields
            coapplicant_name = f"{data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}"
            add_field("Name:", coapplicant_name)
            add_field("Date of Birth:", data.get('coapplicant_dob', ''))
            add_field("Percent Ownership:", data.get('coapplicant_ownership', ''))
            add_field("SSN:", data.get('coapplicant_ssn', ''))
            add_field("Email:", data.get('coapplicant_email', ''))
            add_field("Phone:", data.get('coapplicant_phone', ''))
            add_field("Preferred Contact:", data.get('coapplicant_preferred_contact', ''))
            
            # Co-applicant address
            coapplicant_address = f"{data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}"
            add_field("Address:", coapplicant_address)
        
        # Loan Request Information section
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(210, 210, 210)
        pdf.cell(190, 10, "Loan Request Information", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # Loan information fields
        add_field("Amount Requested:", data.get('amount_requested', ''))
        add_field("Term Length:", data.get('term_length', ''))
        add_field("Credit Score Range:", data.get('credit_score_range', ''))
        
        # Uploaded Files section
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(210, 210, 210)
        pdf.cell(190, 10, "Uploaded Files", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # List uploaded files
        if files:
            for file in files:
                filename = os.path.basename(file)
                pdf.set_font("Arial", '', 10)
                pdf.cell(190, 8, "- " + filename, 0, 1)
        else:
            pdf.set_font("Arial", 'I', 11)
            pdf.cell(190, 8, "No files uploaded", 0, 1)
        
        # Submission Information section
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(210, 210, 210)
        pdf.cell(190, 10, "Submission Information", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # Submission details
        add_field("Browser:", browser)
        add_field("IP Address:", ip_address)
        add_field("Location:", location)
        
        # Handle signature if present
        if 'signature' in data and data.get('signature'):
            try:
                signature_data = data.get('signature', '').split(',')[1]
                signature_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}_signature.png")
                
                with open(signature_path, "wb") as fh:
                    fh.write(base64.b64decode(signature_data))
                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 16)
                pdf.set_fill_color(210, 210, 210)
                pdf.cell(190, 10, "Signature", 0, 1, 'L', fill=True)
                pdf.ln(5)
                pdf.image(signature_path, 10, pdf.get_y(), 60)
                pdf.ln(30)  # Space for the signature
            except Exception as e:
                logging.error(f"Error processing signature: {e}")
        
        # Add footer with page numbers
        pdf.set_y(-15)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, f'Page {pdf.page_no()}', 0, 0, 'C')
        
        # Save PDF
        pdf_folder = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
            
        pdf_filename = os.path.join(pdf_folder, f"MCA_Loan_Application_{unique_id}.pdf")
        pdf.output(pdf_filename)
        
        # Verify the PDF was created successfully
        if os.path.exists(pdf_filename) and os.path.getsize(pdf_filename) > 0:
            logging.info(f"PDF created successfully: {pdf_filename}")
            return pdf_filename
        else:
            logging.error(f"PDF file was not created or is empty: {pdf_filename}")
            return None
        
    except Exception as e:
        logging.error(f"Error creating PDF: {str(e)}")
        # Create a simple fallback PDF with minimal text content
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"MCA Loan Application - {app_id}", 0, 1)
            pdf.cell(0, 10, f"Application Date: {submission_time.strftime('%m/%d/%Y %H:%M')}", 0, 1)
            pdf.cell(0, 10, f"Business: {data.get('company_name', 'N/A')}", 0, 1)
            pdf.cell(0, 10, f"Applicant: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", 0, 1)
            pdf.cell(0, 10, f"Email: {data.get('borrower_email', 'N/A')}", 0, 1)
            pdf.cell(0, 10, f"Amount: {data.get('amount_requested', 'N/A')}", 0, 1)
            
            pdf_folder = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
            if not os.path.exists(pdf_folder):
                os.makedirs(pdf_folder)
                
            pdf_filename = os.path.join(pdf_folder, f"MCA_Loan_Application_{unique_id}.pdf")
            pdf.output(pdf_filename)
            return pdf_filename
        except Exception as inner_e:
            logging.error(f"Error creating fallback PDF: {str(inner_e)}")
            return None
# Route to delete a submission from the database
@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
def api_delete_submission(submission_id):
    try:
        delete_submission(submission_id)
        return jsonify({'message': 'Submission deleted successfully'}), 200
    except Exception as e:
        logging.error(f"Error deleting submission: {e}")
        return jsonify({'error': 'Failed to delete submission'}), 500
# Form submission route
@app.route('/submit_form', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    files = request.files.getlist('files')
    uploaded_files = []
    try:
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_files.append(file_path)
        submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        browser = request.user_agent.string
        ip_address = request.remote_addr
        app_id = generate_app_id()
        # Create PDF
        pdf_filename = create_pdf(form_data, uploaded_files, submission_time, browser, ip_address, str(uuid.uuid4()), 'Unknown', app_id)
        form_data['uploaded_files'] = [os.path.basename(file) for file in uploaded_files]
        form_data['pdf_filename'] = os.path.basename(pdf_filename)
        form_data['app_id'] = app_id
        # Save to database
        insert_submission(app_id, form_data, submission_time)
        # Send email to borrower
        borrower_email = form_data.get('borrower_email')
        if borrower_email:
            borrower_email_template = render_template('borrower_email_template.html', borrower_name=form_data.get('borrower_first_name'), app_id=app_id)
            send_email(borrower_email, "Application Submitted", borrower_email_template)
        # Send email to admin with attachments
        admin_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
        for admin_email in admin_emails:
            send_email(admin_email, "New Application Submitted", "A new application has been submitted.", [pdf_filename] + uploaded_files)
        # Send Slack notification
        slack_message = f"📩 New application submitted by {form_data.get('borrower_first_name', '')} {form_data.get('borrower_last_name', '')}. Application ID: {app_id}"
        send_slack_notification(slack_message)
        flash('Form submitted successfully!')
        return redirect(url_for('congratulation'))
    except Exception as e:
        logging.error(f"Error during form submission: {e}")
        flash('An error occurred while processing your submission.')
        return redirect(url_for('form'))
# PNW Form submission route - mirroring submit_form
@app.route('/submit_pnwform', methods=['POST'])
def submit_pnwform():
    form_data = request.form.to_dict()
    files = request.files.getlist('files')
    uploaded_files = []
    try:
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_files.append(file_path)
        submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        browser = request.user_agent.string
        ip_address = request.remote_addr
        app_id = generate_app_id()
        # Create PDF
        pdf_filename = create_pdf(form_data, uploaded_files, submission_time, browser, ip_address, str(uuid.uuid4()), 'PNW Vendor', app_id)
        form_data['uploaded_files'] = [os.path.basename(file) for file in uploaded_files]
        form_data['pdf_filename'] = os.path.basename(pdf_filename)
        form_data['app_id'] = app_id
        # Save to database
        insert_submission(app_id, form_data, submission_time)
        # Send email to borrower
        borrower_email = form_data.get('borrower_email')
        if borrower_email:
            borrower_email_template = render_template('borrower_email_template.html', borrower_name=form_data.get('borrower_first_name'), app_id=app_id)
            send_email(borrower_email, "Application Submitted", borrower_email_template)
        # Send email to admin with attachments
        admin_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
        for admin_email in admin_emails:
            send_email(admin_email, "New Application Submitted", "A new application has been submitted.", [pdf_filename] + uploaded_files)
        # Send Slack notification
        slack_message = f"📩 New PNW application submitted by {form_data.get('borrower_first_name', '')} {form_data.get('borrower_last_name', '')}. Application ID: {app_id}"
        send_slack_notification(slack_message)
        flash('Form submitted successfully!')
        return redirect(url_for('congratulation'))
    except Exception as e:
        logging.error(f"Error during form submission: {e}")
        flash('An error occurred while processing your submission.')
        return redirect(url_for('pnwform'))
@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')
@app.route('/form')
@app.route('/form.html')
def form():
    return render_template('form.html')
@app.route('/pnwform')
@app.route('/pnwform.html')
def pnwform():
    return render_template('pnwform.html')
@app.route("/contact")
@app.route("/contact.html")
def contact():
    return render_template("contact.html")
@app.route("/question")
@app.route("/question.html")
def questions():
    return render_template("question.html")
@app.route("/about")
@app.route("/about.html")
def about():
    return render_template("about.html")
@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:
        # Collect form data
        form_data = {
            'full_name': request.form.get('full_name'),
            'email': request.form.get('email'),
            'phone_number': request.form.get('phone_number'),
            'message': request.form.get('message')
        }

        # Log the incoming request
        logging.info(f"Processing contact form submission from {form_data['email']}")

        # Check for spam
        is_spam, spam_reasons = spam_filter.check_message(form_data)
        if is_spam:
            logging.warning(f"Spam detected from {form_data['email']}: {spam_reasons}")
            flash('Message sent successfully!')
            return redirect(url_for('email_sent'))

        # Prepare and send email
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(receiver_emails)
        msg['Subject'] = f"New Contact Form Submission from {form_data['full_name']}"

        html_body = f"""
        <html>
            <body>
                <h2>New Contact Form Submission</h2>
                <p><strong>Name:</strong> {form_data['full_name']}</p>
                <p><strong>Email:</strong> {form_data['email']}</p>
                <p><strong>Phone:</strong> {form_data['phone_number']}</p>
                <h3>Message:</h3>
                <p>{form_data['message']}</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logging.info(f"Email sent successfully to {receiver_emails}")

        # Send Slack notification with retries
        slack_message = (
            "<!channel> 🔔 *New Contact Form Submission*\n"
            f"*From:* {form_data['full_name']}\n"
            f"*Email:* {form_data['email']}\n"
            f"*Phone:* {form_data['phone_number']}\n"

            f"*Message:* {form_data['message']}\n\n"
            "@naisha @martha Please review this submission."
        )

        # Attempt to send Slack notification with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = slack_notifier.send_notification(
                    slack_message,
                    level='info',
                    additional_data={
                        'type': 'contact_form',
                        'name': form_data['full_name'],
                        'email': form_data['email']
                    }
                )
                if success:
                    logging.info("Slack notification sent successfully")
                    break
                else:
                    logging.warning(f"Slack notification failed on attempt {attempt + 1}")
            except Exception as e:
                logging.error(f"Slack error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logging.error("All Slack notification attempts failed")

        flash('Message sent successfully!')
        return redirect(url_for('email_sent'))

    except Exception as e:
        logging.error(f"Failed to process contact form: {e}")
        flash('Failed to send message. Please try again later.')
        return redirect(url_for('contact'))
@app.route('/email_sent.html')
def email_sent():
    return render_template('email_sent.html')
@app.route('/congratulation')
def congratulation():
    return render_template('congratulation.html')
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/api/submissions/<int:submission_id>/notes', methods=['GET'])
def get_notes_api(submission_id):
    notes = get_notes(submission_id)
    return jsonify(notes)
# Update status route to ensure correct handling
@app.route('/api/submissions/<int:submission_id>/status', methods=['POST'])
def update_status(submission_id):
    status = request.json.get('status')
    email_content = render_email_content(submission_id, status)
    # Retrieve submission details
    submission = get_submission_by_id(submission_id)
    if submission:
        borrower_email = submission['data'].get("borrower_email")
        if borrower_email:
            send_email(borrower_email, f"Status Update: {status}", email_content)
            insert_communication(submission_id, status, email_sent=True)
            logging.info(f"Status update email sent to {borrower_email}")
            return jsonify({'message': 'Status updated and email sent'}), 200
    return jsonify({'error': 'Failed to send email'}), 500
# Helper function to render email content
def render_email_content(submission_id, status):
    """Renders the email content based on status with HTML template files."""
    status_template_map = {
        'In Review': 'borrower_email_review.html',
        'Approved': 'borrower_email_approved.html',
        'Rejected': 'borrower_email_rejected.html'
    }
    template_name = status_template_map.get(status, 'borrower_email_review.html')  # Default template if status not found
    submission = get_submission_by_id(submission_id)
    if not submission:
        return "<p>Application information not available.</p>"
    borrower_name = f"{submission['data'].get('borrower_first_name', '')} {submission['data'].get('borrower_last_name', '')}"
    return render_template(template_name, borrower_name=borrower_name, app_id=submission['app_id'])
@app.route('/dashboard')
def dashboard():
    try:
        submissions = get_submissions()
        return render_template('dashboard.html', submissions=submissions)
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash('Failed to load dashboard data.')
        return redirect(url_for('index'))
# Fetch and save replies as notes
def fetch_replies():
    email_user = os.getenv("SENDER_EMAIL")
    email_pass = os.getenv("SENDER_PASSWORD")
    imap_server = "imap.gmail.com"
    logging.info("Connecting to email server...")

    try:
        with imaplib.IMAP4_SSL(imap_server) as mail:
            mail.login(email_user, email_pass)
            mail.select("inbox")
            logging.info("Connected and inbox selected.")

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                logging.error("Failed to search inbox for unseen emails.")
                return
            email_ids = messages[0].split()
            logging.info(f"Found {len(email_ids)} unread emails.")

            for num in email_ids:
                # Fetch each email
                _, data = mail.fetch(num, "(RFC822)")
                msg = BytesParser(policy=policy.default).parsebytes(data[0][1])

                # Extract subject
                subject = msg['subject']
                logging.info(f"Email subject: {subject}")

                # Extract Application ID from subject
                app_id = parse_app_id_from_subject(subject)
                if not app_id:
                    logging.info("No Application ID found in subject; skipping email.")
                    continue

                # Retrieve submission by app_id
                submission = get_submission_by_id(app_id)  # Use app_id as a string
                if not submission:
                    logging.info(f"No matching application found for ID: {app_id}.")
                    continue

                # Log email sender
                sender = msg["from"]
                logging.info(f"Processing email from {sender}")

                # Extract email body content
                body = msg.get_body(preferencelist=('plain'))
                body_content = body.get_content() if body else "[No body content found]"
                logging.info(f"Email body content: {body_content}")

                # Process attachments
                attachments = []
                for part in msg.iter_attachments():
                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        attachments.append(filename)
                        logging.info(f"Attachment saved: {filename}")

                # Log content and attachments in the note format
                note_content = f"Email from {sender}:\n\n{body_content}\n\n"
                if attachments:
                    note_content += "Attachments:\n" + "\n".join([f"<a href='/uploads/{a}'>{a}</a>" for a in attachments])

                # Insert note into the database
                insert_note(submission['id'], note_content)
                logging.info(f"Note added to database for Application ID: {app_id}")
    except Exception as e:
        logging.error(f"Error fetching email replies: {e}")
def parse_app_id_from_subject(subject):
    logging.debug(f"Parsing app_id from subject: {subject}")
    if "HE-" in subject:
        start_idx = subject.index("HE-")
        app_id = subject[start_idx:].split()[0].strip()
        logging.debug(f"Parsed app_id: {app_id}")
        return app_id
    logging.debug("No app_id found in subject.")
    return None
# Schedule email fetching every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_replies, trigger=IntervalTrigger(minutes=60))
scheduler.start()
# Route to fetch email replies
@app.route('/fetch_replies')
def fetch_replies_route():
    try:
        fetch_replies()
        return jsonify({"status": "success", "message": "Fetched and stored replies."}), 200
    except Exception as e:
        logging.error(f"Error fetching email replies: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
# Route to save notes and send email if @email is in the note
@app.route('/api/submissions/<int:submission_id>/note', methods=['POST'])
def add_note_with_notification(submission_id):
    data = request.get_json()
    note = data.get('note')
    send_email_flag = '@email' in note
    if not note:
        return jsonify({'error': 'Note content required'}), 400
    note_cleaned = note.replace('@email', '').strip()
    insert_note(submission_id, note_cleaned)
    logging.info(f"Note added for submission ID {submission_id}: {note_cleaned}")
    # Send the update through WebSocket to update the dashboard in real-time
    socketio.emit('note_update', {'submissionId': submission_id, 'note': note_cleaned})
    submission = get_submission_by_id(submission_id)
    if submission:
        borrower_email = submission['data'].get("borrower_email")
        app_id = submission['app_id']
        if send_email_flag and borrower_email:
            email_subject = f"Update on Your Application ID: {app_id}"
            logging.debug(f"Sending email to {borrower_email} with subject: '{email_subject}'")
            send_email(borrower_email, email_subject, note_cleaned)
    return jsonify({'message': 'Note added and email sent if applicable.'}), 201
@app.route('/mcaloanapplication')
@app.route('/mcaloanapplication.html')
def mcaloanapplication():
    return render_template('mcaloanapplication.html')
# MCA Loan submission route
@app.route('/submit_mcaloan', methods=['POST'])
def submit_mcaloan():
    if request.method == 'POST':
        try:
            # Generate a unique application ID
            app_id = generate_app_id()
            
            # Get form data
            form_data = request.form.to_dict()
            
            # Extract key fields needed for database
            company_name = form_data.get('company_name')
            business_industry = form_data.get('business_industry')
            borrower_first_name = form_data.get('borrower_first_name')
            borrower_last_name = form_data.get('borrower_last_name')
            borrower_email = form_data.get('borrower_email')
            borrower_phone = form_data.get('borrower_phone')
            borrower_address_line_1 = form_data.get('borrower_address_line_1')
            borrower_city = form_data.get('borrower_city')
            borrower_state = form_data.get('borrower_state')
            borrower_zip_code = form_data.get('borrower_zip_code')
            amount_requested = form_data.get('amount_requested')
            term_length = form_data.get('term_length')
            credit_score_range = form_data.get('credit_score_range')
            
            # Get current time
            submission_time = datetime.now()
            
            # Get user's browser and IP information for tracking
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr
            location = "Unknown"
            
            # Process file uploads
            uploaded_files = []
            files = request.files.getlist('files')
            
            if files:
                file_folder = os.path.join(app.config['UPLOAD_FOLDER'], app_id)
                if not os.path.exists(file_folder):
                    os.makedirs(file_folder)
                
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            filename = secure_filename(file.filename)
                            file_path = os.path.join(file_folder, filename)
                            file.save(file_path)
                            uploaded_files.append(file_path)
                            logging.info(f"Saved file: {file_path}")
                        except Exception as e:
                            logging.error(f"Error saving file {file.filename}: {e}")
            
            # Save to database
            submission_id = insert_mca_loan_application(
                app_id, company_name, business_industry, borrower_first_name, '', borrower_last_name,
                borrower_email, borrower_phone, borrower_address_line_1, borrower_city, borrower_state, borrower_zip_code,
                amount_requested, term_length, credit_score_range, form_data, submission_time
            )
            
            # Create PDF of application
            pdf_path = create_mca_pdf(form_data, uploaded_files, submission_time, user_agent, ip_address, app_id, location, app_id)
            
            # Send email notifications with PDF and all uploaded documents
            if pdf_path:
                send_mca_application_emails(app_id, form_data, pdf_path, uploaded_files)
            
            # Create comprehensive Slack notification with all fields
            slack_message = f"""🔔 *New MCA Loan Application*
*Application ID:* {app_id}

*BUSINESS INFORMATION*
• Company Name: {company_name}
• Business Type: {form_data.get('business_type', 'N/A')}
• Business Industry: {business_industry}
• Time in Business: {form_data.get('time_in_business', 'N/A')}
• Address: {borrower_address_line_1}, {borrower_city}, {borrower_state} {borrower_zip_code}
• Company Email: {form_data.get('company_email', 'N/A')}
• Company Phone: {form_data.get('company_phone', 'N/A')}
• EIN/TAX ID: {form_data.get('ein', 'N/A')}

*BORROWER INFORMATION*
• Name: {borrower_first_name} {borrower_last_name}
• Email: {borrower_email}
• Phone: {borrower_phone}
• DOB: {form_data.get('borrower_dob', 'N/A')}
• SSN: {form_data.get('borrower_ssn', 'N/A')} (last 4)
• Ownership: {form_data.get('borrower_ownership', 'N/A')}

*LOAN DETAILS*
• Amount Requested: {amount_requested}
• Term Length: {term_length}
• Credit Score Range: {credit_score_range}

*ATTACHMENTS*
• Files Uploaded: {len(uploaded_files)}"""

            # Send Slack notification
            send_slack_notification(slack_message)
            
            # Redirect to success page
            return redirect(url_for('congratulation'))
            
        except Exception as e:
            logging.error(f"Error processing MCA loan application: {str(e)}")
            flash("An error occurred while processing your application. Please try again or contact support.")
            return redirect(url_for('mcaloanapplication'))
    
    # If not POST, redirect to the form
    return redirect(url_for('mcaloanapplication'))
# Function to send MCA application emails
def send_mca_application_emails(app_id, data, pdf_path, uploaded_files=[]):
    # Get sender info from environment variables
    sender_email = os.getenv('SENDER_EMAIL')
    receiver_email_1 = os.getenv('RECEIVER_EMAIL_1')
    receiver_email_2 = os.getenv('RECEIVER_EMAIL_2')
    
    # Email subject
    subject = f"New MCA Loan Application - {app_id}"
    
    # Render admin email template with all form fields
    try:
        html_content = render_template('mca_admin_email_template.html', 
                                      app_id=app_id, 
                                      **data)
    except Exception as e:
        logging.error(f"Error rendering email template: {str(e)}")
        html_content = f"""
        <html>
        <body>
            <h2>New MCA Loan Application</h2>
            <p>A new MCA loan application has been submitted with ID: {app_id}</p>
            <p>Please see the attached files for all details.</p>
        </body>
        </html>
        """
    
    # Combine PDF and uploaded files into one list of attachments
    attachments = []
    
    # Add the PDF if it exists
    if pdf_path and os.path.exists(pdf_path):
        attachments.append(pdf_path)
        
    # Add uploaded files if they exist
    if uploaded_files:
        for file_path in uploaded_files:
            if os.path.exists(file_path):
                attachments.append(file_path)
    
    # Count valid attachment count for logging
    valid_attachment_count = len(attachments)
    
    # Send to first recipient
    try:
        send_email(receiver_email_1, subject, html_content, attachments)
        logging.info(f"MCA application email sent to {receiver_email_1} with {valid_attachment_count} attachments")
    except Exception as e:
        logging.error(f"Failed to send email to {receiver_email_1}: {e}")
    
    # Send to second recipient
    try:
        send_email(receiver_email_2, subject, html_content, attachments)
        logging.info(f"MCA application email sent to {receiver_email_2} with {valid_attachment_count} attachments")
    except Exception as e:
        logging.error(f"Failed to send email to {receiver_email_2}: {e}")
    
    # Send confirmation to applicant
    applicant_subject = f"Your MCA Loan Application - {app_id}"
    try:
        applicant_html = render_template('mca_applicant_email_template.html',
                                        app_id=app_id,
                                        borrower_first_name=data.get('borrower_first_name', ''))
                                        
        send_email(data.get('borrower_email'), applicant_subject, applicant_html)
        logging.info(f"Confirmation email sent to applicant {data.get('borrower_email')}")
    except Exception as e:
        logging.error(f"Failed to send confirmation email to {data.get('borrower_email')}: {e}")
@socketio.on('connect')
def handle_connect():
    logging.info("Client connected to WebSocket.")
@socketio.on('disconnect')
def handle_disconnect():
    logging.info("Client disconnected from WebSocket.")
if __name__ == "__main__":
    app.run(debug=True)