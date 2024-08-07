import os
import uuid
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import requests

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.secret_key = os.getenv('SECRET_KEY')

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

def create_pdf(data, files, submission_time, browser, ip_address, unique_id, location):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.image('static/assets/img/Logo.png', 10, 8, 33)
    pdf.image('static/assets/img/clients/hil.png', 170, 8, 33)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Business Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 12, txt=f"Company Name: {data.get('company_name', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Time in Business: {data.get('time_in_business', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Address: {data.get('address_line_1', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip_code', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Company Email: {data.get('company_email', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Company Phone: {data.get('company_phone', '')}", ln=True)
    pdf.cell(0, 12, txt=f"EIN / TAX ID Number: {data.get('ein', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Type of Business: {data.get('business_type', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Borrower Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 12, txt=f"Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Date of Birth: {format_date(data.get('borrower_dob', ''))}", ln=True)
    pdf.cell(0, 12, txt=f"Percent Ownership: {data.get('borrower_ownership', '')}", ln=True)
    pdf.cell(0, 12, txt=f"SSN: {data.get('borrower_ssn', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Phone: {data.get('borrower_phone', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Email: {data.get('borrower_email', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Preferred Method of Contact: {data.get('borrower_preferred_contact', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Address: {data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Co-Applicant Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 12, txt=f"Name: {data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Date of Birth: {format_date(data.get('coapplicant_dob', ''))}", ln=True)
    pdf.cell(0, 12, txt=f"Percent Ownership: {data.get('coapplicant_ownership', '')}", ln=True)
    pdf.cell(0, 12, txt=f"SSN: {data.get('coapplicant_ssn', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Phone: {data.get('coapplicant_phone', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Email: {data.get('coapplicant_email', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Preferred Method of Contact: {data.get('coapplicant_preferred_contact', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Address: {data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Loan Request Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 12, txt=f"Amount of Equipments: {data.get('loan_amount', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Max Down Payments: {data.get('max_down_payment', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Equipment & Seller Info: {data.get('equipment_seller_info', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Signature", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 12, txt=f"Borrower Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 12, txt=f"Submission Time: {submission_time}", ln=True)
    pdf.cell(0, 12, txt=f"Browser: {browser}", ln=True)
    pdf.cell(0, 12, txt=f"IP Address: {ip_address}", ln=True)
    pdf.cell(0, 12, txt=f"Unique ID: {unique_id}", ln=True)
    pdf.cell(0, 12, txt=f"Location: {location}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 16, txt="Attached Files", ln=True)
    pdf.set_font("Arial", size=6)
    for file in files:
        pdf.cell(0, 16, txt=f"File: {os.path.basename(file)}", ln=True)
    pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], "application.pdf")
    pdf.output(pdf_filename)
    return pdf_filename

@app.route('/form')
@app.route('/form.html')
def form():
    return render_template('form.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    files = request.files.getlist('files')
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_files.append(file_path)

    submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    browser = request.user_agent.string
    ip_address = get_client_ip(request)
    unique_id = str(uuid.uuid4())
    location = get_location(ip_address)

    pdf_filename = create_pdf(form_data, uploaded_files, submission_time, browser, ip_address, unique_id, location)

    sender_email = os.getenv('SENDER_EMAIL')
    receiver_emails = [os.getenv('RECEIVER_EMAIL_1'), os.getenv('RECEIVER_EMAIL_2')]
    password = os.getenv('SENDER_PASSWORD')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = "You Have a New Application!"
    body = "Please find the attached form submission and supporting documents. \nApplication sent from https://hempire-enterprise.com/"
    msg.attach(MIMEText(body, 'plain'))
    with open(pdf_filename, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_filename)}")
        msg.attach(part)
    for file in uploaded_files:
        with open(file, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file)}")
            msg.attach(part)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_emails, text)
    server.quit()
    for file in uploaded_files:
        os.remove(file)
    os.remove(pdf_filename)
    return render_template('congratulation.html')

@app.route('/congratulation.html')
def congratulation():
    return render_template('congratulation.html')

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

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
        text = msg.as_string()
        server.sendmail(sender_email, receiver_emails, text)
        server.quit()
        flash('Message sent successfully!')
    except Exception as e:
        flash('Failed to send message. Please try again later.')
    return redirect(url_for('email_sent'))

@app.route('/email_sent.html')
def email_sent():
    return render_template('email_sent.html')

if __name__ == "__main__":
    app.run(debug=True)
