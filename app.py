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
    insert_note, insert_communication, get_submission_by_id, get_notes, insert_reply, get_replies
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
app = Flask(__name__)
socketio = SocketIO(app)
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
    """Send a notification message to Slack."""
    slack_notifier.send_notification(message, level='info', additional_data={'type': 'form_submission'})
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
        slack_notifier.send_notification(slack_message, level='info', additional_data={'type': 'form_submission'})
        flash('Form submitted successfully!')
        return redirect(url_for('congratulation'))
    except Exception as e:
        logging.error(f"Error during form submission: {e}")
        flash('An error occurred while processing your submission.')
        return redirect(url_for('form'))
@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')
@app.route('/form')
@app.route('/form.html')
def form():
    return render_template('form.html')
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
@socketio.on('connect')
def handle_connect():
    logging.info("Client connected to WebSocket.")
@socketio.on('disconnect')
def handle_disconnect():
    logging.info("Client disconnected from WebSocket.")
if __name__ == "__main__":
    app.run(debug=True)