from celery import Celery
import logging
import os
import sys
import mysql.connector
from ssl_monitoring_worker import expirationDate, daysLeft
from lib.properties import SSL_DB_CRED, MAIN_DIR, CELERY_BROKER, CELERY_BACKEND

app = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)
logpath = f"/var/log/cp_argus/{MAIN_DIR}/ssl_update"

if not os.path.exists(logpath):
    os.makedirs(logpath)

def setup_logging():
    appname = MAIN_DIR
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
        print(f"{domain}: {days} days left")
        update_days_in_db(days, domain)