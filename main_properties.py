DEBUG = False

if DEBUG:
    CELERY_SERVER = '172.17.15.111'
else:
    CELERY_SERVER = '10.168.13.212'

#git config
GIT_USER = 'om'
GIT_EMAIL = 'om@sinonet.ph'
GIT_PASS = 'c1BDSi0wMTU='
GIT_URL = 'gitlab.neweb.me'

#ssh info
SSH_PORT = 28032
SSH_USER = 'root'
SSH_PRIVKEY = '/root/.ssh/id_rsa'

#db cred
DB_NAME = 'YXJndXNfY3A='
DB_USER = 'YXJndXNjcHVzZXI='
DB_PASS = 'WVhKbmRYTmZZM0JoY21kMWMyTndkWE5sY2c9PQ=='
DB_SERVER = CELERY_SERVER
