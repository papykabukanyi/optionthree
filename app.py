import os
import uuid
import base64
from datetime import datetime
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
from database import init_db, insert_submission, get_submissions, delete_submission, generate_app_id

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
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
        delete_submission(submission_id)  # This will delete the submission from the database
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
    full_name = request.form['full_name']
    email = request.form['email']
    phone_number = request.form['phone_number']
    message = request.form['message']
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = "New Contact Form Submission"
    body = f"Name: {full_name}\nEmail: {email}\nPhone: {phone_number}\nMessage: {message}"
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()
        flash('Message sent successfully!')
    except Exception as e:
        logging.error(f"Failed to send contact email: {e}")
        flash('Failed to send message. Please try again later.')
    return redirect(url_for('email_sent'))


@app.route('/email_sent.html')
def email_sent():
    return render_template('email_sent.html')

@app.route('/congratulation')
def congratulation():
    return render_template('congratulation.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard')
def dashboard():
    try:
        submissions = get_submissions()
        return render_template('dashboard.html', submissions=submissions)
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash('Failed to load dashboard data.')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
