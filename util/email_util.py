# coding:utf-8
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os
import re
import smtplib
import time


class EmailUtil():

    # mail_host = "123.125.50.138"  # 设置服务器
    # mail_host = "123.58.178.204"  # 设置服务器
    mail_host = "smtp.163.com"  # 设置服务器
    mail_user = "clockworkweb"  # 用户名
    mail_pass = "wlt2014"  # 口令
    mail_postfix = "163.com"  # 发件箱的后缀
    me = "ClockWork<%s@%s>" % (mail_user, mail_postfix)

    @staticmethod
    def send(to_list, sub, content, filenames = None, retry = None, seconds = None):
        if retry is None :
            return EmailUtil.__send(to_list, sub, content, filenames)
        else :
            if not seconds :
                seconds = 60
            count = 0
            while True :
                if count == retry :
                    return False
                if EmailUtil.__send(to_list, sub, content, filenames) :
                    return True
                else :
                    count += 1
                    time.sleep(seconds)

    @staticmethod
    def __send(to_list, sub, content, filenames = None):
        try:
            message = MIMEMultipart()
            message.attach(MIMEText(content, _subtype = 'html', _charset = 'UTF-8'))
            message["Subject"] = sub
            message["From"] = EmailUtil.me
            message["To"] = ";".join(to_list)
            if filenames is not None :
                for filename in filenames :
                    if os.path.exists(filename):
                        ctype, encoding = mimetypes.guess_type(filename)
                        if ctype is None or encoding is not None:
                            ctype = "application/octet-stream"
                        subtype = ctype.split("/", 1)
                        attachment = MIMEImage((lambda f: (f.read(), f.close()))(open(filename, "rb"))[0], _subtype = subtype)
                        attachment.add_header("Content-Disposition", "attachment", filename = re.findall('\/(\w+\.\w+)$', filename)[0])
                        message.attach(attachment)
            server = smtplib.SMTP()
            server.connect(EmailUtil.mail_host)
            server.login(EmailUtil.mail_user, EmailUtil.mail_pass)
            server.sendmail(EmailUtil.me, to_list, message.as_string())
            server.close()
            return True
        except Exception, e:
            print 'EmailUtil.__send error:', str(e)
        return False

if __name__ == '__main__':
    if EmailUtil.send(['25958235@qq.com'],
                 "你好",
                 "hello我哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈你你你 world!",
                 ["C:/Users/IBM/Desktop/ReportPublisher.zip", "C:/Users/IBM/Desktop/aaaaaaaaaaaaaa.xls"]
                 ):
        print "发送成功"
    else:
        print "发送失败"
