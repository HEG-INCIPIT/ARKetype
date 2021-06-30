from common import *

DEPLOYMENT_LEVEL = "hegenv"

STANDALONE = True
RELOAD_TEMPLATES = True
DAEMON_THREADS_ENABLED = False

ALLOWED_HOSTS = ["*","37.187.98.23","localhost","127.0.0.1","86.119.28.138"]
injectSecrets(DEPLOYMENT_LEVEL)
