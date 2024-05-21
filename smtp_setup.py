import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def save_smtp_credentials(smtp_server, smtp_port, username, password, email_from, email_to, email_subject):
    with open('secrets.py', 'w') as f:
        f.write(f"# SMTP Credentials\nSMTP_SERVER = '{smtp_server}'\nSMTP_PORT = {smtp_port}\nUSERNAME = '{username}'\nPASSWORD = '{password}'\nEMAIL_FROM = '{email_from}'\nEMAIL_TO = '{email_to}'\nEMAIL_SUBJECT = '{email_subject}'")

    # Set file permissions to be readable and writable only by the owner
    os.chmod('secrets.py', 0o600)

def send_email(message):
    try:
        from secrets import SMTP_SERVER, SMTP_PORT, USERNAME, PASSWORD, EMAIL_FROM, EMAIL_TO, EMAIL_SUBJECT

        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = EMAIL_SUBJECT

        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(USERNAME, PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    smtp_server = input("Enter SMTP server: ")
    smtp_port = int(input("Enter SMTP port: "))
    username = input("Enter username: ")
    password = input("Enter password: ")
    email_from = input("Enter sender email address: ")
    email_to = input("Enter recipient email address: ")
    email_subject = input("Enter email subject: ")

    save_smtp_credentials(smtp_server, smtp_port, username, password, email_from, email_to, email_subject)

    print("SMTP credentials saved successfully!")
