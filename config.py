import os
from dotenv import load_dotenv
load_dotenv()

LOG_PATH = os.getenv("LOG_PATH", "logs")
TENANT_ID = os.getenv("TENANT_ID", "3200bc23-08a5-4747-b66c-167d2263eb17")
CLIENT_ID = os.getenv("CLIENT_ID", "5d2125be-3ffa-4035-ab3f-e835b9461bad")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = os.getenv("SCOPE", "api://5d2125be-3ffa-4035-ab3f-e835b9461bad/.default")