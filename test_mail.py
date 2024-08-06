from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'papykabukanyi@gmail.com'
app.config['MAIL_PASSWORD'] = 'snwucxupdkadlfef'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

@app.route('/')
def index():
    msg = Message('Test Email', sender='papykabukanyi@gmail.com', recipients=['papykabukanyi@gmail.com'])
    msg.body = 'This is a test email sent from Flask-Mail.'
    mail.send(msg)
    return 'Email sent!'

if __name__ == '__main__':
    app.run(debug=True)




import os
import datetime
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.secret_key = os.getenv('SECRET_KEY')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
creds = None

creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID and range of the spreadsheet.
SAMPLE_SPREADSHEET_ID = os.getenv('SAMPLE_SPREADSHEET_ID')

service = build('sheets', 'v4', credentials=creds)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_pdf(data, files):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.image('static/assets/img/Logo.png', 10, 8, 33)
    pdf.image('static/assets/img/clients/hil.png', 170, 8, 33)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Business Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 6, txt=f"Company Name: {data.get('company_name', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Time in Business: {data.get('time_in_business', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Address: {data.get('address_line_1', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip_code', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Company Email: {data.get('company_email', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Company Phone: {data.get('company_phone', '')}", ln=True)
    pdf.cell(0, 6, txt=f"EIN / TAX ID Number: {data.get('ein', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Type of Business: {data.get('business_type', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Borrower Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 6, txt=f"Name: {data.get('borrower_first_name', '')} {data.get('borrower_last_name', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Percent Ownership: {data.get('borrower_ownership', '')}", ln=True)
    pdf.cell(0, 6, txt=f"SSN: {data.get('borrower_ssn', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Phone: {data.get('borrower_phone', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Email: {data.get('borrower_email', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Address: {data.get('borrower_address_line_1', '')}, {data.get('borrower_city', '')}, {data.get('borrower_state', '')} {data.get('borrower_zip_code', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Co-Applicant Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 6, txt=f"Name: {data.get('coapplicant_first_name', '')} {data.get('coapplicant_last_name', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Percent Ownership: {data.get('coapplicant_ownership', '')}", ln=True)
    pdf.cell(0, 6, txt=f"SSN: {data.get('coapplicant_ssn', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Phone: {data.get('coapplicant_phone', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Email: {data.get('coapplicant_email', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Address: {data.get('coapplicant_address_line_1', '')}, {data.get('coapplicant_city', '')}, {data.get('coapplicant_state', '')} {data.get('coapplicant_zip_code', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Loan Request Information", ln=True)
    pdf.set_font("Arial", size=6)
    pdf.cell(0, 6, txt=f"Amount of Equipments: {data.get('loan_amount', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Max Down Payments: {data.get('max_down_payment', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Equipment & Seller Info: {data.get('equipment_seller_info', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Agreements", ln=True)
    pdf.set_font("Arial", size=2)
    pdf.multi_cell(0, 6, txt="Additional information may be required based upon time in business, current credit standing, and application amount. Each individual signing below certifies that the information provided in this credit application is accurate and complete. Each individual signing below authorizes you or any lender or funding source which may be utilized (collectively referred to as 'Lenders') to obtain information from the references listed above and obtain a consumer credit report that will be ongoing and relate not only to the evaluation and/or extension of the business credit requested, but also for purposes of reviewing the account, increasing the credit line on the account (if applicable), taking collection action on the account, and for any other legitimate purpose associated with the account as may be needed from time to time. Each individual signing below further waives any right or claim which such individual would otherwise have under the Fair Credit Reporting Act in the absence of this continuing consent.")
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 8, txt="Attached Files", ln=True)
    pdf.set_font("Arial", size=6)
    for file in files:
        pdf.cell(0, 6, txt=f"File: {os.path.basename(file)}", ln=True)
    pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], "application.pdf")
    pdf.output(pdf_filename)
    return pdf_filename

def update_google_sheet(data):
    values = [
        [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(data.values())
    ]
    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Applications!A1",
        valueInputOption="RAW", body=body).execute()

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
    pdf_filename = create_pdf(form_data, uploaded_files)

    # Update Google Sheet
    update_google_sheet(form_data)

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




{
    "type": "service_account",
    "project_id": "hempireonlineappmanager",
    "private_key_id": "64f4ff516f321b6f45682a04a64a69220ae52e87",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDOXMOCPpMjk4+7\n57DpbqL8DUnTlOM/d2QTk2WuhkMv4UM2P2abprCVHR8OI/4zgJzIIsE368+3SjqD\nC/EQqQGqoEV4z8kYJwdlxIQli9U0DSSY+USilY2M32ZR1FxafURAJdeVlv2WyLoO\n2vV4wsWLjmp4s0tc/Ut6SaRyt7QxmkGAiThPvhNmMp8OwwqJHUwBm3fJpoK2QCu9\n4lmCucbebbGo7ImauZei62FiRuA8AQIteGdjGWeAy6RCbi20YxWUtuLooDCOsXKQ\noPY9xZhX0T30Pfw1rtwORGopCkacShlPD5clI2T6fdBiNz5kZ0iKPGOD9eYFM3Ol\nkLQfZrNLAgMBAAECggEAEbkUz3BJWcJYE1bEMmAenlAT2ZiNZct+rFG552G/jnKl\nv5h1WwPXYY8VNjUwJUMz89pMRt25QrAc01lotDoXmwxVuxj5V9ouP/a/NKxMPMKu\nNHcgBmiathEPrBJ1dg4RGQNG/yFvGQ6XMCRs9Zigt6odCc24OL3GSDPf7DxLvQCv\naZE7pFCxP/JqkUAeXRvOkpaxBeRLNQUoDlnrwkUPQSWAI8rUYK8q0TJ5gdJXcW7w\nRgnY5zj0HU4fryKWTgb2vGSTYE1lmE7HcOPz7slCNJEjxfb11yX2fw+a4qatDAa1\njhafj6Z3NOsBDZTu+hFK4r8J85oQ9L64PI5zCPchaQKBgQD44IkS/1X57G5pR6zM\naP3iURmRn9p2v7GGi9AclEa6kT1W7s9uNU9km10cxe/JAze6z3+OzJx0zEfw1/z+\ndzwzYks/dU3syRb1vsUv7xlNr82WHE21u3a9N03jrLLOaZX06DaKkLgZVDPbYwBI\nO1C/Wi0P3bBEyqdACCro3AsEkwKBgQDURLuSJvq13KlImZh6PlDGtOJuZzrccSmO\naIm3Yp7qRWCB9yFaF/SgTuHbKwbTAgHw4e9XwS4iPuKUFs9EuWvkS7HaCQ+jGDS7\nMRTi57bGmtqjLUDyq59cIG+UjQ3HQr9ZmmT+MdtNrciyOWkai/SVyOKy+Z5Rkvsi\nkaeUqjXBaQKBgQDZerStwiyqUf4Fx9lrYpABFaeHRq4MOOTz0vdQEg5geAynC9Z9\n0t4G53ENdLZd7I7lku8/pPNPaTewcb2lzCHyMQHaeTJYKT0ED+mWQpTU+zxm4WLS\n3Pccz9gjjUVO9JtSwRzwJxiJIbiTDMcxV4vvOujHxYyEAKb4YGrGw4ppOwKBgQCp\n2GFZnXToBasyWywlTC1oAZ5YhqMTdjyxJTZklTXg8Cg7ddmq9BYaG2Qe8TuhpS6W\nZsITLpDSeAzmP6YTMGaDIoopkyx+7MRsr+YtdQjLu2aMQI6CXg7CMXX2oDLRKLhh\nYufCeXQnoJFBAiz2P9wx6a5zVMZ4MSpfS7qSeutOWQKBgGLGcNzsBmBhYyqqQwCF\nJ4M7C1zrA5C4xYa/ea/CxMtvH2w5t8IaXUjoAEAfq9nazOgsAWqXRmFkpDH1LMWr\nUUjqvoki+J5JtiQefWthGRRSuV+K2X9jW+fYPbITagaZAuI881pv9XZvVYD9Xn+z\nU9mV7qkTjQxfpqggjLLOw1OK\n-----END PRIVATE KEY-----\n",
    "client_email": "hempire-app-manager@hempireonlineappmanager.iam.gserviceaccount.com",
    "client_id": "117664640308946109291",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/hempire-app-manager%40hempireonlineappmanager.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
  }
  