import os
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

COMMON_AGENT_SERVICE = AzureChatCompletion(
                            deployment_name="main-gpt-4",
                            api_key=OPENAI_KEY,
                            endpoint=OPENAI_ENDPOINT,
                            api_version="2025-01-01-preview",
                            service_id="SChat",
                        )