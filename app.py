import os
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

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
