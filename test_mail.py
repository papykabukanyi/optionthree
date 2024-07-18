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
