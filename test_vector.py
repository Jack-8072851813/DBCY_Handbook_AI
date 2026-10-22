# test_vector.py

import os
from dotenv import load_dotenv
from databricks.vector_search.client import VectorSearchClient

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

client = VectorSearchClient(disable_notice=True)

index = client.get_index(
    endpoint_name=os.getenv("DATABRICKS_VECTOR_SEARCH_ENDPOINT", "aichatbot-vs-endpoint"),
    index_name="aichatbot.gold.handbook_vector_index_v2"
)

print("SUCCESS")