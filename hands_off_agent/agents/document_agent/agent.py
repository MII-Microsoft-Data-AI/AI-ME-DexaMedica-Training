from hands_off_agent.common import COMMON_AGENT_SERVICE
from semantic_kernel.agents import ChatCompletionAgent
from hands_off_agent.agents.document_agent.plugins.ai_search import search_plugin

import logging
from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

logging.debug("Initializing DocumentSearchAgent")

document_search_agent = ChatCompletionAgent(
    name="DocumentSearchAgent",
    description="An assistant to help users find or search documents and summarize them.",
    instructions="Handle document search requests using ai search plugin. If the user ask your name, tell them you're auditama. When using any tools, plugins, or transferring to other agents, let me know what you're doing explicitly.",
    service=COMMON_AGENT_SERVICE,
    plugins=[search_plugin]
)