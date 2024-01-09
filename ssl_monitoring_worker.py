from celery import Celery
from datetime import datetime
import ssl
import socket
import logging, os
from properties import MAIN_DIR, CELERY_BROKER, CELERY_BACKEND

app = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)
logpath = "/var/log/cp_argus/{}".format(MAIN_DIR)
if not os.path.exists(logpath):
    os.makedirs(logpath)

def setup_logging():
    appname = MAIN_DIR
    filename = "{}.log".format(appname)
    logfile = os.path.join(logpath, filename)
    logging.basicConfig(
        level=logging.DEBUG,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
        format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
        filename=logfile,  # Set the log file name
        filemode='a'  # Set the file mode ('w' for write, 'a' for append)
    )
    setup_logging()

@app.task()
def expirationDate(domain_text, port=443):
    logging.debug("#####" * 20)
    logging.info("WORKER: expirationDate")
    try:
        # Split my domain_text
        domains = domain_text.split('\n')
        logging.info(f"{domain_text}")

        results = []
        for domain in domains:
            domain = domain.strip()
            if domain:
                logging.info(f"Checking domain: {domain}")
                result = check_single_domain(domain, port)
                logging.info(f"Result for {domain}: {result}")
                if 'error' not in result:
                    results.append(result)

        logging.info(f"Results: {results}")
        return [result for result in results if 'error' not in result]
    except Exception as e:
        logging.info(f"Error in expirationDate: {str(e)}")
        return {
            'error': f"Error checking SSL certificates: {str(e)}"
        }
def check_single_domain(domain, port):
    try:
        # Connect to the server and obtain the SSL certificate
        context = ssl.create_default_context()
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

        # Extract expiration date from the certificate
        expiration_date_str = cert['notAfter']
        logging.info(f"Raw expiration date string for {domain}: {expiration_date_str}, type: {type(expiration_date_str)}")
        if isinstance(expiration_date_str, str):
            expiration_date = datetime.strptime(expiration_date_str, '%b %d %H:%M:%S %Y %Z')
            expiration_date_str = expiration_date.strftime('%Y-%m-%d')
        return expiration_date_str

    except Exception as e:
        return {
            'domain': domain,
            'error': f"Error checking SSL certificate for {domain}: {str(e)}"
        }


@app.task()
def daysLeft(expiration_dates):
    try:
        if not expiration_dates or not isinstance(expiration_dates, list):
            raise ValueError("Invalid expiration dates list")

        # Assuming you want to use the first expiration date from the list
        expiration_date_str = expiration_dates[0]

        logging.info(f"Received expiration date string: {expiration_date_str}")

        # List of possible date formats
        date_formats = ['%Y-%m-%d', '%b %d %H:%M:%S %Y %Z', 'other_format']

        # Try parsing the date with each format
        for format_str in date_formats:
            try:
                expiration_date = datetime.strptime(expiration_date_str, format_str)
                break  # If successful, exit the loop
            except ValueError:
                continue  # If unsuccessful, try the next format

        # Calculate the number of days left
        today = datetime.now()
        days_left = (expiration_date - today).days
        days_left_str = str(days_left)

        logging.info(f"Days left: {days_left_str}")
        return days_left_str
    except Exception as e:
        logging.info(f"Error in daysLeft: {str(e)}")
        return {
            'error': f"Error calculating days left: {str(e)}"
        }
