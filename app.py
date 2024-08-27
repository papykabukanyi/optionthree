# import os
# import sqlite3
# import uuid
# import base64
# from datetime import datetime
# from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_from_directory
# from werkzeug.security import generate_password_hash, check_password_hash
# from werkzeug.utils import secure_filename
# from fpdf import FPDF
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# from dotenv import load_dotenv
# import requests
# import json
# import logging
# from database import init_db, insert_submission, get_submissions, get_submission_by_id, delete_submission, insert_user, get_user_by_email, generate_app_id

# # Setup logging
# logging.basicConfig(level=logging.DEBUG)

# load_dotenv()  # Load environment variables from .env file

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
# app.secret_key = os.getenv('SECRET_KEY')

# init_db()  # Initialize the database

# if not os.path.exists(app.config['UPLOAD_FOLDER']):
#     os.makedirs(app.config['UPLOAD_FOLDER'])

# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# def get_client_ip(request):
#     if request.environ.get('HTTP_X_FORWARDED_FOR'):
#         ip = request.environ['HTTP_X_FORWARDED_FOR']
#     else:
#         ip = request.environ['REMOTE_ADDR']
#     return ip

# def get_location(ip):
#     try:
#         response = requests.get(f'http://ip-api.com/json/{ip}')
#         data = response.json()
#         return f"{data['city']}, {data['regionName']}, {data['country']}"
#     except:
#         return "Unknown Location"

# def format_date(date_str):
#     try:
#         date_obj = datetime.strptime(date_str, '%Y-%m-%d')
#         return date_obj.strftime('%m/%d/%Y')
#     except ValueError:
#         return date_str

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
#         return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#     else:
#         logging.error(f"File {filename} not found or is empty.")
#         flash('The requested file is either missing or empty.')
#         return redirect(url_for('form'))

# def create_pdf(data, files, submission_time, browser, ip_address, unique_id, location, app_id):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
#     pdf.image('static/assets/img/Logo.png', 10, 8, 33)
#     pdf.image('static/assets/img/clients/hil.png', 170, 8, 33)
#     pdf.ln(15)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Business Information", ln=True)
#     pdf.set_font("Arial", size=10)
#     pdf.cell(0, 5, txt=f"Company Name: {data.get('company_name', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Time in Business: {data.get('time_in_business', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Address: {data.get('address_line_1', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip_code', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Company Email: {data.get('company_email', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Company Phone: {data.get('company_phone', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"EIN / TAX ID Number: {data.get('ein', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Type of Business: {data.get('business_type', '')}", ln=True)
#     pdf.ln(2)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Borrower Information", ln=True)
#     pdf.set_font("Arial", size=10)
#     pdf.cell(0, 5, txt=f"Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Date of Birth: {format_date(data.get('borrower_dob', ''))}", ln=True)
#     pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('borrower_ownership', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"SSN: {data.get('borrower_ssn', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Phone: {data.get('borrower_phone', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Email: {data.get('borrower_email', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Preferred Method of Contact: {data.get('borrower_preferred_contact', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Address: {data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}", ln=True)
#     pdf.ln(2)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Co-Applicant Information", ln=True)
#     pdf.set_font("Arial", size=10)
#     pdf.cell(0, 5, txt=f"Name: {data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Date of Birth: {format_date(data.get('coapplicant_dob', ''))}", ln=True)
#     pdf.cell(0, 5, txt=f"Percent Ownership: {data.get('coapplicant_ownership', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"SSN: {data.get('coapplicant_ssn', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Phone: {data.get('coapplicant_phone', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Email: {data.get('coapplicant_email', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Preferred Method of Contact: {data.get('coapplicant_preferred_contact', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Address: {data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}", ln=True)
#     pdf.ln(2)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Loan Request Information", ln=True)
#     pdf.set_font("Arial", size=10)
#     pdf.cell(0, 5, txt=f"Amount of Equipments: {data.get('loan_amount', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Max Down Payments: {data.get('max_down_payment', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Equipment & Seller Info: {data.get('equipment_seller_info', '')}", ln=True)
#     pdf.ln(2)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Signature", ln=True)
#     pdf.set_font("Arial", size=10)
#     pdf.cell(0, 5, txt=f"Borrower Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
#     pdf.cell(0, 5, txt=f"Submission Time: {submission_time}", ln=True)
#     pdf.cell(0, 5, txt=f"Browser: {browser}", ln=True)
#     pdf.cell(0, 5, txt=f"IP Address: {ip_address}", ln=True)
#     pdf.cell(0, 5, txt=f"Unique ID: {unique_id}", ln=True)
#     pdf.cell(0, 5, txt=f"Location: {location}", ln=True)
#     pdf.cell(0, 5, txt=f"Application ID: {app_id}", ln=True)

#     # Decode and save signature
#     signature_data = data.get('signature', '').split(',')[1]
#     signature_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}_signature.png")
#     with open(signature_path, "wb") as fh:
#         fh.write(base64.b64decode(signature_data))
    
#     pdf.image(signature_path, 10, pdf.get_y() + 10, 60)  # Adjust as needed
#     pdf.ln(20)
    
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, txt="Attached Files", ln=True)
#     pdf.set_font("Arial", size=10)
#     for file in files:
#         pdf.cell(0, 6, txt=f"File: {os.path.basename(file)}", ln=True)
#     pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"{app_id}.pdf")
#     pdf.output(pdf_filename)

#     if os.path.exists(pdf_filename) and os.path.getsize(pdf_filename) > 0:
#         logging.info(f"PDF {pdf_filename} generated successfully.")
#         return pdf_filename
#     else:
#         logging.error(f"Failed to generate PDF {pdf_filename}. File is missing or empty.")
#         raise ValueError("Generated PDF is empty or not created.")

# @app.route('/submit_form', methods=['POST'])
# def submit_form():
#     form_data = request.form.to_dict()
#     files = request.files.getlist('files')
#     uploaded_files = []

#     try:
#         for file in files:
#             if file and allowed_file(file.filename):
#                 file.seek(0, os.SEEK_END)  # Move the cursor to the end of the file
#                 file_length = file.tell()  # Get the current cursor position which is the size of the file
#                 file.seek(0, os.SEEK_SET)  # Move the cursor back to the start of the file

#                 if file_length > 0:
#                     filename = secure_filename(file.filename)
#                     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                     file.save(file_path)
#                     uploaded_files.append(file_path)
#                 else:
#                     logging.warning(f"Uploaded file {file.filename} is empty (size: {file_length} bytes).")
#                     flash('One of the uploaded files is empty. Please ensure the file is not empty before uploading.')
#                     return redirect(url_for('form'))
#             else:
#                 logging.warning(f"File {file.filename} is not allowed or was not uploaded correctly.")

#         # Continue processing if file uploads are successful
#         submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         browser = request.user_agent.string
#         ip_address = get_client_ip(request)
#         unique_id = str(uuid.uuid4())
#         location = get_location(ip_address)
#         app_id = generate_app_id()

#         pdf_filename = create_pdf(form_data, uploaded_files, submission_time, browser, ip_address, unique_id, location, app_id)
        
#         form_data['uploaded_files'] = [os.path.basename(file) for file in uploaded_files]
#         form_data['pdf_filename'] = os.path.basename(pdf_filename)
#         form_data['app_id'] = app_id
#         form_data['submission_time'] = submission_time
#         form_data['browser'] = browser
#         form_data['ip_address'] = ip_address
#         form_data['unique_id'] = unique_id
#         form_data['location'] = location

#         insert_submission(app_id, form_data, submission_time)

#         borrower_email = form_data.get('borrower_email')
#         borrower_name = f"{form_data.get('borrower_first_name', '')} {form_data.get('borrower_last_name', '')}"
#         email_template = render_template('borrower_email_template.html', borrower_name=borrower_name, app_id=app_id, business_type=form_data.get('business_type', ''))

#         send_borrower_email(borrower_email, "Application Submitted", email_template)

#         sender_email = os.getenv('SENDER_EMAIL')
#         receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
#         password = os.getenv('SENDER_PASSWORD')
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = ", ".join(receiver_emails)
#         msg['Subject'] = "You Have a New Application!"
#         body = "Please find the attached form submission and supporting documents."
#         msg.attach(MIMEText(body, 'plain'))

#         # Attach the generated PDF
#         with open(pdf_filename, "rb") as attachment:
#             part = MIMEBase('application', 'octet-stream')
#             part.set_payload(attachment.read())
#             encoders.encode_base64(part)
#             part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_filename)}")
#             msg.attach(part)

#         # Attach uploaded files
#         for file_path in uploaded_files:
#             with open(file_path, "rb") as attachment:
#                 part = MIMEBase('application', 'octet-stream')
#                 part.set_payload(attachment.read())
#                 encoders.encode_base64(part)
#                 part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
#                 msg.attach(part)

#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_emails, msg.as_string())
#         server.quit()

#     except Exception as e:
#         logging.error(f"Error occurred during form submission: {e}")
#         flash('An error occurred while processing your submission. Please try again.')
#         return redirect(url_for('form'))

#     return render_template('congratulation.html')

# def send_borrower_email(to_email, subject, html_content):
#     sender_email = os.getenv('SENDER_EMAIL')
#     sender_password = os.getenv('SENDER_PASSWORD')
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = to_email
#     msg['Subject'] = subject
#     msg.attach(MIMEText(html_content, 'html'))
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, to_email, msg.as_string())
#         server.quit()
#     except Exception as e:
#         logging.error(f"Failed to send email to {to_email}: {e}")

# @app.route('/')
# @app.route('/index')
# @app.route('/index.html')
# def index():
#     return render_template('index.html')

# @app.route('/form')
# @app.route('/form.html')
# def form():
#     return render_template('form.html')

# @app.route('/congratulation.html')
# def congratulation():
#     return render_template('congratulation.html')

# @app.route("/contact")
# @app.route("/contact.html")
# def contact():
#     return render_template("contact.html")

# @app.route("/question")
# @app.route("/question.html")
# def questions():
#     return render_template("question.html")

# @app.route("/about")
# @app.route("/about.html")
# def about():
#     return render_template("about.html")

# @app.route('/send_email', methods=['POST'])
# def send_email():
#     full_name = request.form['full_name']
#     email = request.form['email']
#     phone_number = request.form['phone_number']
#     message = request.form['message']
#     sender_email = os.getenv('SENDER_EMAIL')
#     sender_password = os.getenv('SENDER_PASSWORD')
#     receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = ", ".join(receiver_emails)
#     msg['Subject'] = "New Contact Form Submission"
#     body = f"Name: {full_name}\nEmail: {email}\nPhone: {phone_number}\nMessage: {message}"
#     msg.attach(MIMEText(body, 'plain'))
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, receiver_emails, msg.as_string())
#         server.quit()
#         flash('Message sent successfully!')
#     except Exception as e:
#         logging.error(f"Failed to send contact email: {e}")
#         flash('Failed to send message. Please try again later.')
#     return redirect(url_for('email_sent'))

# @app.route('/email_sent.html')
# def email_sent():
#     return render_template('email_sent.html')

# # User Authentication
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == ['POST']:
#         email = request.form['email']
#         password = request.form['password']
#         user = get_user_by_email(email)
#         if user and check_password_hash(user[3], password):  # user[3] is the password field in the users table
#             session['user_id'] = user[0]  # user[0] is the user id
#             flash('Login successful!')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid email or password!')
#     return render_template('login.html')

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == ['POST']:
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']
#         hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
#         try:
#             insert_user(username, email, hashed_password)
#             flash('Signup successful! Please log in.')
#             return redirect(url_for('login'))
#         except sqlite3.IntegrityError:
#             flash('Email or username already exists!')
#     return render_template('signup.html')

# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     flash('Logged out successfully!')
#     return redirect(url_for('login'))

# @app.route('/dashboard.html')
# @app.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#     return render_template('dashboard.html')

# @app.route('/api/submissions', methods=['GET'])
# def api_submissions():
#     submissions = get_submissions()
#     return jsonify({'submissions': [{'id': s[0], 'app_id': s[1], 'data': s[2], 'submission_time': s[3]} for s in submissions]})

# @app.route('/api/submissions/<int:submission_id>', methods=['GET'])
# def api_submission(submission_id):
#     submission = get_submission_by_id(submission_id)
#     if submission:
#         data = json.loads(submission[2])
#         return jsonify({'id': submission[0], 
#                         'app_id': submission[1], 
#                         'business_type': data.get('business_type'),  
#                         'signature': data.get('signature'),  # Include the signature data
#                         'data': submission[2], 
#                         'submission_time': submission[3]})
#     else:
#         return jsonify({'error': 'Submission not found'}), 404

# @app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
# def api_delete_submission(submission_id):
#     delete_submission(submission_id)
#     return jsonify({'message': 'Submission deleted successfully'})

# if __name__ == "__main__":
#     app.run(debug=True)

import os
import uuid
import base64
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import requests
import json
import logging
from database import init_db, insert_submission, get_submissions, get_submission_by_id, delete_submission, insert_user, get_user_by_email, generate_app_id

# Setup logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = os.getenv('SECRET_KEY')

init_db()  # Initialize the database

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
    except:
        return "Unknown Location"

def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d/%Y')
    except ValueError:
        return date_str

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        logging.error(f"File {filename} not found or is empty.")
        flash('The requested file is either missing or empty.')
        return redirect(url_for('form'))

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
    pdf.cell(0, 5, txt=f"Application ID: {app_id}", ln=True)

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
                file.seek(0, os.SEEK_END)  # Move the cursor to the end of the file
                file_length = file.tell()  # Get the current cursor position which is the size of the file
                file.seek(0, os.SEEK_SET)  # Move the cursor back to the start of the file

                if file_length > 0:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    uploaded_files.append(file_path)
                else:
                    logging.warning(f"Uploaded file {file.filename} is empty (size: {file_length} bytes).")
                    flash('One of the uploaded files is empty. Please ensure the file is not empty before uploading.')
                    return redirect(url_for('form'))
            else:
                logging.warning(f"File {file.filename} is not allowed or was not uploaded correctly.")

        # Continue processing if file uploads are successful
        submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        browser = request.user_agent.string
        ip_address = get_client_ip(request)
        unique_id = str(uuid.uuid4())
        location = get_location(ip_address)
        app_id = generate_app_id()

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

        borrower_email = form_data.get('borrower_email')
        borrower_name = f"{form_data.get('borrower_first_name', '')} {form_data.get('borrower_last_name', '')}"
        email_template = render_template('borrower_email_template.html', borrower_name=borrower_name, app_id=app_id, business_type=form_data.get('business_type', ''))

        send_borrower_email(borrower_email, "Application Submitted", email_template)

        sender_email = os.getenv('SENDER_EMAIL')
        receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
        password = os.getenv('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(receiver_emails)
        msg['Subject'] = "You Have a New Application!"
        body = "Please find the attached form submission and supporting documents."
        msg.attach(MIMEText(body, 'plain'))

        # Attach the generated PDF
        with open(pdf_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_filename)}")
            msg.attach(part)

        # Attach uploaded files
        for file_path in uploaded_files:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
                msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()

    except Exception as e:
        logging.error(f"Error occurred during form submission: {e}")
        flash('An error occurred while processing your submission. Please try again.')
        return redirect(url_for('form'))

    return render_template('congratulation.html')

def send_borrower_email(to_email, subject, html_content):
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/form')
@app.route('/form.html')
def form():
    return render_template('form.html')

@app.route('/congratulation.html')
def congratulation():
    return render_template('congratulation.html')

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
def send_email():
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

# User Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == ['POST']:
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and check_password_hash(user[3], password):  # user[3] is the password field in the users table
            session['user_id'] = user[0]  # user[0] is the user id
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == ['POST']:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            insert_user(username, email, hashed_password)
            flash('Signup successful! Please log in.')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            flash('Email or username already exists!')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/dashboard.html')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/submissions', methods=['GET'])
def api_submissions():
    submissions = get_submissions()
    return jsonify({'submissions': [{'id': s[0], 'app_id': s[1], 'data': s[2], 'submission_time': s[3]} for s in submissions]})

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
def api_submission(submission_id):
    submission = get_submission_by_id(submission_id)
    if submission:
        data = json.loads(submission[2])
        return jsonify({'id': submission[0], 
                        'app_id': submission[1], 
                        'business_type': data.get('business_type'),  
                        'signature': data.get('signature'),  # Include the signature data
                        'data': submission[2], 
                        'submission_time': submission[3]})
    else:
        return jsonify({'error': 'Submission not found'}), 404

@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
def api_delete_submission(submission_id):
    delete_submission(submission_id)
    return jsonify({'message': 'Submission deleted successfully'})

if __name__ == "__main__":
    app.run(debug=True)
