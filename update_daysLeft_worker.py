import logging
import os
import mysql.connector
from ssl_monitoring_worker import expirationDate, daysLeft
import base64
import smtplib
from email.mime.text import MIMEText

# email settings
SMTP_USER="bm9yZXBseS1vbUBob3RlbHN0b3RzZW5iZXJnLmNvbQ=="
SMTP_PASS="bW9vZWdobGFjcXNreW5yeQ=="
EMAIL_RECIPIENT = ["om20_os@hotelstotsenberg.com"]

def send_email_alert(domain, days_left):
    subject = f"SSL Certificate Expiry Alert for {domain}"
    body = f"The SSL certificate for {domain} will expire in {days_left} days."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(EMAIL_RECIPIENT)

    #  SMTP - to send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Update with your SMTP server details
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_RECIPIENT, msg.as_string())
        logging.info(f"Email notification sent for {domain}")
    except Exception as e:
        logging.error(f"Failed to send email notification for {domain}: {e}")
    finally:
        server.quit()


SSL_DB_CRED = {
    'host': '10.168.13.212',
    'user': "{}".format(base64.b64decode("YXJndXNjcHVzZXI=").decode('utf-8')),
    'password': "{}".format(base64.b64decode("WVhKbmRYTmZZM0JoY21kMWMyTndkWE5sY2c9PQ==").decode('utf-8')),
    'database': "{}".format(base64.b64decode("YXJndXNfY3A=").decode('utf-8'))
}

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
        logging.info("The value is an integer.")
        return int(value)
    else:
        logging.info("The value is not an integer.")
        return 0

if __name__ == '__main__':
    domains = get_domains_from_db()

    logging.info(f"Retrieved {len(domains)} domains from the database")
    print(f"Retrieved {len(domains)} domains from the database")

    for domain in domains:
        days = compute_days(domain)
        logging.info(f"{domain}: {days} days left")
        print(f"{domain}: {days} days left")
        update_days_in_db(days, domain)