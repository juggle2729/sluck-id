# -*- coding: utf-8 -*-
import os
import base64
import smtplib
import threading
import mimetypes
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from multiprocessing import Process


class MailSender(object):
    """Send mail class
    singleton and thread safe
    """
    __instance = {}
    __lock = threading.Lock()
    _SUFFIX_MIME_DCT = {
        'text': MIMEText,
        'image': MIMEImage,
        'audio': MIMEAudio,
    }

    def __init__(self):
        """disable init method
        """
        raise Exception('__init__ function of MailSender is not available!')

    def init_conf(self, mail_conf):
        self.mail_server = mail_conf['server']
        self.mail_user = mail_conf['user']
        self.mail_passwd = mail_conf['passwd']
        self.mail_from = mail_conf['from']
        # target can be specified when `send`
        self.mail_to = mail_conf.get('to', [])

    @staticmethod
    def getInstance(route_name='default'):
        """get instance object by mail route name which is used for grouping,
        if not specified, default route name will be `default`
        """
        MailSender.__lock.acquire()
        if route_name not in MailSender.__instance:
            instance = object.__new__(MailSender)
            MailSender.__instance[route_name] = instance
        MailSender.__lock.release()
        return MailSender.__instance[route_name]

    def _prepare_smtp(self):
        smtp = smtplib.SMTP(self.mail_server)
        # if you are using gmail, enable starttls here
        # smtp.starttls()
        smtp.login(self.mail_user, self.mail_passwd)

        return smtp

    @classmethod
    def _transfer_mime_file(cls, attachment):
        if os.path.isfile(attachment):
            ctype, encoding = mimetypes.guess_type(attachment)
            if ctype is None or encoding is None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            read_type = 'r' if maintype == 'text' else 'rb'

            fp = data = None
            with open(attachment, read_type) as source:
                fp = source.read()
            mime_class = cls._SUFFIX_MIME_DCT.get(maintype, None)
            if mime_class:
                data = mime_class(fp, _subtype=subtype)
            else:
                data = MIMEBase(maintype, subtype)
                data.set_payload(fp)
                encoders.encode_base64(data)
            return data
        else:
            print 'attachment %s is not a file!' % attachment

    def _prepare_msg(self, subject, body, mail_to, attachments, embeddeds):
        msg = MIMEMultipart()
        msg["From"] = self.mail_from
        msg["To"] = ";".join(mail_to)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))

        if isinstance(attachments, basestring):
            attachments = [attachments]
        if isinstance(embeddeds, tuple):
            embeddeds = [embeddeds]
        for attachment in attachments:
            data = MailSender._transfer_mime_file(attachment)
            if not data:
                continue
            data.add_header('Content-Disposition', 'attachment',
                            filename=os.path.basename(attachment))
            msg.attach(data)

        for content, _id, pictype, style in embeddeds:
            mime_type, _ = mimetypes.guess_type('a.' + pictype)
            if not mime_type.startswith('image'):
                continue
            data = None
            if style == 'path':
                data = MailSender._transfer_mime_file(content)
            elif style in ('binary', 'base64'):
                if style == 'base64':
                    content = base64.b64decode(content)
                data = MIMEImage(content)
            else:
                raise ValueError('embedded style not supported: %s' % style)

            data.add_header('Content-ID', '<' + _id + '>')
            msg.attach(data)

        return msg

    def send(self, subject, body, to_list=None, attachments=None,
             embeddeds=None, async=False):
        '''send email with specified data.
        * Email stype is fixed to html;
        * `attachments` should be file pathes;
        * `embeddeds` support image only, the list item format should be
          `(content, Content-ID, image-type, style)`
            - `style` contains 'path', 'binary' and 'base64' now;
            - `Content-ID` used to specified in your mail template;
        '''
        try:
            if async:
                t = Process(target=self.send,
                            args=(subject, body, to_list, False))
                t.daemon = False
                t.start()
            else:
                if not to_list:
                    to_list = self.mail_to
                msg = self._prepare_msg(subject, body, to_list,
                                        attachments or [],
                                        embeddeds or [])
                smtp = self._prepare_smtp()
                smtp.sendmail(self.mail_from, to_list, msg.as_string())
                smtp.quit()
                print "send email, subject[%s], tolist[%s]" % (
                    subject, to_list)
        except Exception as e:
            print e


def send_email(email_num, title, content):
    mail_sender = MailSender.getInstance()
    mail_sender.init_conf({
        'server': 'smtp.mxhichina.com:25',
        'user': 'service@yygzx.com',
        'passwd': 'WHzh@7floora',
        'from': u'LuckyShop',
        'to': [email_num]
    })
    mail_sender.send(title, content)


TOOL_MAIL_SENDER = MailSender.getInstance()
TOOL_MAIL_SENDER.init_conf({
    'server': 'smtp.mxhichina.com:25',
    'user': 'ops@zhuohan-tech.com',
    'passwd': 'madP@ssw0rd',
    'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
    'to': [
        'zhulei@zhuohan-tech.com',
        'xialu@zhuohan-tech.com',
        'mahongli@zhuohan-tech.com',
        'sstong@zhuohan-tech.com',
        'taocheng@zhuohan-tech.com',
        'lichang@zhuohan-tech.com',
        'xialu@zhuohan-tech.com',
        'caonianci@zhuohan-tech.com',
    ]
})

if __name__ == "__main__":
    html_str = '''<html><head></head><body><h1>测试 test mail</h1>
                <br /> <p>This is just a test</p></body></html>'''
    mail_sender = MailSender.getInstance()
    mail_sender.init_conf({
        'server': 'smtp.mxhichina.com:25',
        'user': 'ops@adsquare-tech.com',
        'passwd': 'madP@ssw0rd',
        'from': 'Adsquare Service Statistics<ops@adsquare-tech.com>',
        'to': ['shuxiang@adsquare-tech.com']
    })
    mail_sender.send("[subject] Test Email", html_str)
