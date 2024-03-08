import logging
import os
from time import strftime

import mysql.connector
from ssl_monitoring_worker import expirationDate, daysLeft
import base64
from datetime import datetime, timedelta

from django.core.mail import get_connection, send_mail
from django.core.mail.message import EmailMessage
from django.conf import settings
settings.configure(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#from email.utils import COMMASPACE, formatdate
from properties import SMTP_USER, SMTP_PASS
import smtplib




SSL_DB_CRED = {
    'host': '10.168.13.212',
    'user': "{}".format(base64.b64decode("YXJndXNjcHVzZXI=").decode('utf-8')),
    'password': "{}".format(base64.b64decode("WVhKbmRYTmZZM0JoY21kMWMyTndkWE5sY2c9PQ==").decode('utf-8')),
    'database': "{}".format(base64.b64decode("YXJndXNfY3A=").decode('utf-8'))
}

#logging
logpath = f"/var/log/cp_argus/ssl_update"

if not os.path.exists(logpath):
    os.makedirs(logpath)

def setup_logging():
    appname = logpath
    filename = f"{appname}.log"
    logfile = os.path.join(logpath, filename)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=logfile,
        filemode='a'
    )

setup_logging()

def get_domains_from_db():
    conn = mysql.connector.connect(
        host=SSL_DB_CRED['host'],
        user=SSL_DB_CRED['user'],
        password=SSL_DB_CRED['password'],
        database=SSL_DB_CRED['database']
    )

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM ssl_monitoring_domainmodel")
    domains = [row[0] for row in cursor.fetchall()]
    conn.close()

    logging.info(f"domains from db: {domains}")
    return domains

def update_days_in_db(days_left, name):
    conn = mysql.connector.connect(
        host=SSL_DB_CRED['host'],
        user=SSL_DB_CRED['user'],
        password=SSL_DB_CRED['password'],
        database=SSL_DB_CRED['database']
    )

    cursor = conn.cursor()
    cursor.execute("UPDATE ssl_monitoring_domainmodel SET days_left = %s WHERE name = %s", (days_left, name))
    conn.commit()
    conn.close()

def compute_days(Domain):
    value = daysLeft(expirationDate(Domain))
    if isinstance(value, str):
        logging.info("The value is a string.")
        return value
    else:
        logging.info("The value is not a string.")
        return '0'


#attachments = {"filename":"content"};
domainname = get_domains_from_db()
def sendMail():

    domain_names = []

    domainname = get_domains_from_db()
    week_old = "14"  # timedelta(days=14)

    for domain_name in domainname:
        if int(days_left) <= int(week_old):
            (
                domain_names.append(domainname.domain + "\n")
            )


    # Once I have that, I compile the email:

    message = MIMEMultipart("alternative")
    message["Subject"] = "Domain Renewal Alert"
    message["From"] = "No reply OM"
    recipients = ["noreply-om@hotelstotsenberg.com"]
    message["To"] = "vhchong@snsoft.my"


    # creating the content of the email, first the plain content then the html content

    plain = """
    Domain Expired soon:
    """ + "\n".join(
        domain_names
    )

    html = """
    <h1><span style="color: #ff0000; background-color: #000000;"><strong>Domain Expired soon:</strong></span></h1>
    """ + "\n".join(
        domain_names
    )

    # now we compile both parts to prepare them to send

    part1 = MIMEText(plain, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    # Now send the email

    gmail_user = "bm9yZXBseS1vbUBob3RlbHN0b3RzZW5iZXJnLmNvbQ"
    gmail_pwd = "bW9vZWdobGFjcXNreW5yeQ"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_user, gmail_pwd)
    server.sendmail(message["From"], recipients, message.as_string())



if __name__ == '__main__':
    domains = get_domains_from_db()
    week_old = "14" #timedelta(days=14)

    logging.info(f"Retrieved {len(domains)} domains from the database")
    print(f"Retrieved {len(domains)} domains from the database")

    for domain in domains:
        days_left = compute_days(domain)
        logging.info(f"{domain}: {days_left} days left")
        print(f"{domain}: {days_left} days left")
        update_days_in_db(days_left, domain)

    sendMail()




