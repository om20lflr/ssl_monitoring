import logging
import os

import mysql.connector
from ssl_monitoring_worker import expirationDate, daysLeft
import base64
from datetime import datetime
from django.core.mail import get_connection, send_mail
from django.core.mail.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from django.conf import settings
settings.configure(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')





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


def sendMail():
    today = datetime.today()

    me = "noreply-cpom@hotelstotsenberg"
    you = "vhchong@snsoft.my"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "SSL Expiration Notice&nbsp;" + str(today.strftime("%d/%m/%y"))
    msg['From'] = me
    msg['To'] = you

    html_body = """\
            <html>
                <head></head>
                    <body>
                        <p>Hi Team,<br><br>
                        
                        Please check the SSL of the following domain(s):<br><br>
                          
            """
    html_close = """\
                        <br>
                        <p>Regards,<br>
                        OM</p>
                    </body>
            </html>
    """

    domains = get_domains_from_db()

    for domain in domains:
        d = []
        week_old = 14
        days_left = compute_days(domain)
        if int(days_left) <= int(week_old):
            d.append("{0} is expiring in {1} days.<br>".format(domain, days_left))
            print(d)
            html1 = (''.join(d))
            html_body = html_body + html1
            print(html_body)

    html = html_body + html_close

    part2 = MIMEText(html, 'html')
    msg.attach(part2)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login('noreply-cpom@hotelstotsenberg.com', 'zfuq egca fewo dwul')
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




