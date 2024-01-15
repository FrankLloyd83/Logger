import os

LOG_PATH = os.environ.get("LOG_PATH", "logs")
TENANT_ID = os.environ.get("TENANT_ID", "common")
CLIENT_ID = os.environ.get("CLIENT_ID", "1d1161d3-4327-4f4b-8493-99f430e69bc6")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
LOG_SCOPE = os.environ.get("LOG_SCOPE")
URL_ISSUER_BASE = os.environ.get("URL_ISSUER_BASE", "https://login.microsoftonline.com/")