from hands_off_agent.common import COMMON_AGENT_SERVICE
from semantic_kernel.agents import ChatCompletionAgent

document_search_agent = ChatCompletionAgent(
    name="DocumentSearchAgent",
    description="An assistant to help users find or search documents and summarize them.",
    instructions="Handle document search requests, but not currently available. Do immediate handsoff and also tell that it's not currently available!. If the user ask your name, tell them you're auditama. When transfering to another agent, you don't need to send me any text!",
    service=COMMON_AGENT_SERVICE,
    plugins=[]
)