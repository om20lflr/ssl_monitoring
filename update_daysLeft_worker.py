import logging
import os

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

def get_daysleft_in_db():
    conn = mysql.connector.connect(
        host=SSL_DB_CRED['host'],
        user=SSL_DB_CRED['user'],
        password=SSL_DB_CRED['password'],
        database=SSL_DB_CRED['database']
    )

    cursor = conn.cursor()
    cursor.execute("SELECT name, days_left FROM ssl_monitoring_domainmodel WHERE days_left < '14' ")
    #domains = [row[0] for row in cursor.fetchall()]
    daysleft = [row[0] for row in cursor.fetchall()]
    conn.close()

    logging.info(f"days left from db: {daysleft}")
    return daysleft


def compute_days(Domain):
    value = daysLeft(expirationDate(Domain))
    if isinstance(value, str):
        logging.info("The value is a string.")
        return value
    else:
        logging.info("The value is not a string.")
        return '0'


def sendMail():

    me = "vhchong@snsoft.my"
    you = "josephcvh@gmail.com"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Domain Expiry Notice"
    msg['From'] = me
    msg['To'] = you

    html1 = """\
            <html>
                <head></head>
                    <body>
                        <p>Hi Team,<br><br>
                        Reminder:<br>
                        Please check if Domain listed below need to be renewed.<br><br>
                        {0}

                        </p>
                    </body>
            </html>
            """
    html = "hello, <br>{0}"

    domains = get_domains_from_db()
    week_old = 14
    d = []

    for domain in domains:

        days_left = compute_days(domain)
        if int(days_left) <= int(week_old):

            d.append("{0} is expiring in {1} days.<br>".format(domain, days_left))
            print(d)

            html = ('\n'.join(d))

            print(html)
    html = html[2:]
    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login('vhchong@snsoft.my', 'yzlw qeoy flvl zazd')
    mail.sendmail(me, you, msg.as_string())
    mail.quit()






if __name__ == '__main__':
    domains = get_domains_from_db()

    logging.info(f"Retrieved {len(domains)} domains from the database")
    print(f"Retrieved {len(domains)} domains from the database")

    for domain in domains:
        days_left = compute_days(domain)
        logging.info(f"{domain}: {days_left} days left")
        print(f"{domain}: {days_left} days left")
        update_days_in_db(days_left, domain)

    sendMail()




