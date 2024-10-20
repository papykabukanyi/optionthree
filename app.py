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
import json
import logging
from database import init_db, insert_submission, get_submissions, get_submission_by_id, delete_submission, generate_app_id

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = os.getenv('SECRET_KEY')

# Initialize the database
init_db()

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_client_ip(request):
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.environ['REMOTE_ADDR']
    return ip


def get_location(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        return f"{data['city']}, {data['regionName']}, {data['country']}"
    except Exception:
        return "Unknown Location"


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d/%Y')
    except ValueError:
        return date_str


# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        logging.error(f"File not found: {file_path}")
        return "File not found", 404


# Function to create the PDF
def create_pdf(data, files, submission_time, browser, ip_address, unique_id, location, app_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.image('static/assets/img/Logo.png', 10, 8, 33)
    pdf.image('static/assets/img/clients/hil.png', 170, 8, 33)
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
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Borrower Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Date of Birth: {format_date(data.get('borrower_dob', ''))}", ln=True)
    pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('borrower_ownership', '')}", ln=True)
    pdf.cell(0, 5, txt=f"SSN: {data.get('borrower_ssn', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Phone: {data.get('borrower_phone', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Email: {data.get('borrower_email', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Preferred Method of Contact: {data.get('borrower_preferred_contact', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Address: {data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Co-Applicant Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Name: {data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Date of Birth: {format_date(data.get('coapplicant_dob', ''))}", ln=True)
    pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('coapplicant_ownership', '')}", ln=True)
    pdf.cell(0, 5, txt=f"SSN: {data.get('coapplicant_ssn', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Phone: {data.get('coapplicant_phone', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Email: {data.get('coapplicant_email', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Preferred Method of Contact: {data.get('coapplicant_preferred_contact', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Address: {data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Loan Request Information", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Amount of Equipments: {data.get('loan_amount', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Max Down Payments: {data.get('max_down_payment', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Equipment & Seller Info: {data.get('equipment_seller_info', '')}", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Signature", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, txt=f"Borrower Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 5, txt=f"Submission Time: {submission_time}", ln=True)
    pdf.cell(0, 5, txt=f"Browser: {browser}", ln=True)
    pdf.cell(0, 5, txt=f"IP Address: {ip_address}", ln=True)
    pdf.cell(0, 5, txt=f"Unique ID: {unique_id}", ln=True)
    pdf.cell(0, 5, txt=f"Location: {location}", ln=True)

    # Decode and save signature
    signature_data = data.get('signature', '').split(',')[1]
    signature_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}_signature.png")
    with open(signature_path, "wb") as fh:
        fh.write(base64.b64decode(signature_data))
    
    pdf.image(signature_path, 10, pdf.get_y() + 10, 60)  # Adjust as needed
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Attached Files", ln=True)
    pdf.set_font("Arial", size=10)
    for file in files:
        pdf.cell(0, 6, txt=f"File: {os.path.basename(file)}", ln=True)
    pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}.pdf")
    pdf.output(pdf_filename)

    if os.path.exists(pdf_filename) and os.path.getsize(pdf_filename) > 0:
        logging.info(f"PDF {pdf_filename} generated successfully.")
        return pdf_filename
    else:
        logging.error(f"Failed to generate PDF {pdf_filename}. File is missing or empty.")
        raise ValueError("Generated PDF is empty or not created.")


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
                file.save(file_path)  # Save the file in uploads folder
                uploaded_files.append(file_path)

        submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        browser = request.user_agent.string
        ip_address = get_client_ip(request)
        unique_id = str(uuid.uuid4())
        location = get_location(ip_address)
        app_id = generate_app_id()

        # Create a PDF for the submission
        pdf_filename = create_pdf(form_data, uploaded_files, submission_time, browser, ip_address, unique_id, location, app_id)

        form_data['uploaded_files'] = [os.path.basename(file) for file in uploaded_files]
        form_data['pdf_filename'] = os.path.basename(pdf_filename)
        form_data['app_id'] = app_id
        form_data['submission_time'] = submission_time
        form_data['browser'] = browser
        form_data['ip_address'] = ip_address
        form_data['unique_id'] = unique_id
        form_data['location'] = location

        insert_submission(app_id, form_data, submission_time)

    except Exception as e:
        logging.error(f"Error during form submission: {e}")
        flash('An error occurred while processing your submission.')
        return redirect(url_for('form'))

    return render_template('congratulation.html')


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/form')
@app.route('/form.html')
def form():
    return render_template('form.html')


@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    submissions = get_submissions()
    return render_template('dashboard.html', submissions=submissions)


# API route to get all submissions
@app.route('/api/submissions', methods=['GET'])
def api_submissions():
    submissions = get_submissions()
    return jsonify({'submissions': [{'id': s[0], 'app_id': s[1], 'data': s[2], 'submission_time': s[3]} for s in submissions]})


# API route to get a single submission by ID
@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
def api_submission(submission_id):
    submission = get_submission_by_id(submission_id)
    if submission:
        data = json.loads(submission[2])
        return jsonify({
            'id': submission[0], 
            'app_id': submission[1], 
            'data': submission[2], 
            'submission_time': submission[3]
        })
    else:
        return jsonify({'error': 'Submission not found'}), 404


# API route to delete a submission by ID
@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
def api_delete_submission(submission_id):
    delete_submission(submission_id)
    return jsonify({'message': 'Submission deleted successfully'})


if __name__ == "__main__":
    app.run(debug=True)
