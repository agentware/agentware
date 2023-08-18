import os
from dotenv import load_dotenv

load_dotenv()

endpoint = "http://localhost:8741"
openai_api_key = os.getenv("OPENAI_API_KEY")
api_key = os.getenv("API_KEY")

HELPER_AGENT_CONFIGS_DIR_NAME = "base_agent_configs"
EMBEDDING_DIM = 1536
KNOWLEDGE_BASE_IDENTIFIER_PREFIX = "knowledge_"
