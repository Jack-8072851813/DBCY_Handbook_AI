import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

w = WorkspaceClient()

print("Connected")
print(w.current_user.me().user_name)