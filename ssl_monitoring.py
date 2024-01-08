from celery import Celery
from datetime import datetime, timedelta
import ssl
import socket
from celery import shared_task
from main_properties import CELERY_SERVER, CELERY_PORT



CELERY_BROKER = 'redis://{}:{}'.format(CELERY_SERVER, CELERY_PORT)
CELERY_BACKEND = CELERY_BROKER
CELERY_QUEUE = "sslMonitoringQueue"
CELERY_CONCURRENCY = 6
CELERY_HOSTNAME = "sslMonitoringHostname"
app = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)


@app.task()
def expirationDate(domain_text, port=443):
    try:
        # Split my domain_text
        domains = domain_text.split('\n')
        print(f"{domain_text}")

        results = []
        for domain in domains:
            domain = domain.strip()
            if domain:
                print(f"Checking domain: {domain}")
                result = check_single_domain(domain, port)
                print(f"Result for {domain}: {result}")
                if 'error' not in result:
                    results.append(result)

        print(f"Results: {results}")
        return results
    except Exception as e:
        print(f"Error in expirationDate: {str(e)}")
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

        print(f"Received expiration date string: {expiration_date_str}")

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

        print(f"Days left: {days_left_str}")
        return days_left_str
    except Exception as e:
        print(f"Error in daysLeft: {str(e)}")
        return {
            'error': f"Error calculating days left: {str(e)}"
        }
