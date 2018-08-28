from flask import render_template,url_for
from flask_mail import Message,Mail
from encrypt_decrypt import URL_HASH

class EMAIL_MANAGER:
    def __init__(self,app):
        self.app = app
        with self.app.app_context():
            self.mail = Mail(app)
            self.url_hash = URL_HASH()
            self.msg = Message(subject='email-verification')

    def send_mail(self,to):
        with self.app.app_context(), self.app.test_request_context():
            token = self.url_hash.getSerializedURL(to)
            print('token: ',token)
            home_url = url_for('home',_external=True)
            verify_url = url_for('email_verification',token=token,_external=True)
            html_msg = render_template('email-confirmation.html',home_url=home_url,
                                        url_to_verify=verify_url)
            self.msg.recipients = [to]
            self.msg.html = html_msg
            self.mail.send(self.msg)


