from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os



class MAIL_SERVER:
    def send_mail(self, receiver_mail, subject, message):
        try:
            mail_server = SMTP("smtp.gmail.com", 587)
            mail_server.starttls()
            # Use double quotes for outer strings to avoid nested quote issues
            sender = os.environ.get("SYS_MAIL")
            sender_pwd = os.environ.get("SYS_MAIL_PWD")
            mail_server.login(sender, sender_pwd)
            msg = f"Subject: {subject}\n\n{message}"

            mail_server.sendmail(msg=msg, from_addr=sender, to_addrs=str(receiver_mail))
            print("Email sent successful.")
            return True
        except Exception as e:
            print(f"[ERROR] Email was not sent due to: {e}")
            return False

    def send_html_email(self, receiver_mail, subject, message):
        try:

            # Email components
            from_email = os.environ.get("SYS_MAIL")
            to_email = str(receiver_mail)
            subject = subject

            # Create the email content
            html_content = f"""
            <html>
            <body>
                <h1 style=\"color:blue;\">{subject}!</h1>
                <div>
                    {message}
                </div>
            </body>
            </html>
            """

            # Construct email
            msg = MIMEMultipart("alternative")
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            # Attach HTML part
            msg.attach(MIMEText(html_content, "html"))

            # Send the email
            try:
                with SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()  # Secure the connection
                    sender_pwd = os.environ.get("SYS_MAIL_PWD")
                    server.login(from_email, sender_pwd)
                    server.sendmail(from_email, to_email, msg.as_string())
                    print("Email sent successfully!")
                    return True
            except Exception as e:
                print(f"[ERROR] Email was not sent due to: {e}")
                return False

        except Exception as e:
            print(f"[ERROR] Email was not sent due to: {e}")
            return False
