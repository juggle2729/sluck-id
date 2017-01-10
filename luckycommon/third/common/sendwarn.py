
from common import *
import datetime
import smtplib,sys
from email.mime.text import MIMEText
import json

class SendWarn:
    def __init__(self, logger, mailBox = None, smsBox = None):
        self.logger = logger
        self.mailBox = mailBox
        self.smsBox = smsBox
        self.http = HttpApi(logger)
        
    def send_mail(self, subject, content, mailto_list):
        me = "%s<%s@%s>" %(self.mailBox["user"], self.mailBox["user"], self.mailBox["postfix"])
        msg = MIMEText(content, _charset='UTF-8')
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = ";".join(mailto_list)
        try:
            smtp = smtplib.SMTP()
            smtp.connect(self.mailBox["host"])
            smtp.login(self.mailBox["user"], self.mailBox["pwd"])
            smtp.sendmail(me, mailto_list, msg.as_string())
            smtp.close() 
        except Exception, e:
            self.logger.error("Cannot send mail: host[%s], user[%s], reason[%s]"
                %(self.mailBox["host"], self.mailBox["user"], str(e)));

    def send_sms(self, subject, content, msisdn_list):
        now = datetime.datetime.now()
        seqId = "%04d%02d%02d%02d%02d%02d%03d" %(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
        body = {"userId": "iapppay", "userPwd":"123456", "smsType":"1", 
                "smsTextMessage": "[%s]%s" %(subject, content), "receiveMobile":",".join(msisdn_list),
                "seqId": seqId}
        info, response = self.http.httpPostCall(self.smsBox["url"], json.dumps(body, ensure_ascii=False), False)
        if None == response:
            self.logger.error("Cannot send sms: url[%s]" %(self.smsBox["url"]))
        
    def send_warn(self, subject, content, mailto_list, msisdn_list):
        if None != self.mailBox:
            self.send_mail(subject, content, mailto_list)
            
        if None != self.smsBox:
            self.send_sms(subject, content, msisdn_list)