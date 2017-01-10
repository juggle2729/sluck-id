import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail
import requests

SENDGRID_API_KEY = "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"
MAILGUN_API_URL = "https://api.mailgun.net/v3/mail.lucky-gou.com/messages"
MAILGUN_API_KEY = "key-31a0e71d57f6b5e75891f787e8b9b0f5"


def send_via_mailgun(mail_to, mail_subject, mail_content):
    result = requests.post(MAILGUN_API_URL,
                           auth=("api", MAILGUN_API_KEY),
                           data={"from": "Lucky-gou <postmaster@mail.lucky-gou.com>",
                                 "to": [mail_to, ],
                                 "subject": mail_subject,
                                 "html": mail_content,
                                })
    print result.status_code, result.text


def send_via_sendgrid(mail_from, mail_to, mail_subject, mail_content):
    sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
    from_email = Email(mail_from)
    subject = mail_subject
    to_email = Email(mail_to)
    content = Content("text/plain", mail_content)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)


def send_mail(mail_to, mail_subject, mail_content):
    send_via_mailgun(mail_to, mail_subject, mail_content)


if __name__ == '__main__':
    send_via_mailgun("leechannl@icloud.com", "hello", "just a test")
    # send_via_sendgrid("test", "lichang@adsquare-tech.com", "hello", "just a test")
