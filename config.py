import os

LOG_PATH = os.environ.get("LOG_PATH", "logs")
TENANT_ID = os.environ.get("TENANT_ID", "3200bc23-08a5-4747-b66c-167d2263eb17")
CLIENT_ID = os.environ.get("CLIENT_ID", "5d2125be-3ffa-4035-ab3f-e835b9461bad")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
LOG_SCOPE = os.environ.get("LOG_SCOPE", "api://5d2125be-3ffa-4035-ab3f-e835b9461bad/.default")