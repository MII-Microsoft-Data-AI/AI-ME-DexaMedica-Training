from multi_agent.common import COMMON_AGENT_SERVICE
from semantic_kernel.agents import ChatCompletionAgent
from multi_agent.agents.document_agent.agent import  document_search_agent
from multi_agent.agents.light_agent.agent import  light_agent

orchestrator_agent = ChatCompletionAgent(
    name="OrchestratorAgent",
    description="An assistant that helps user and also manage, analyze request, orchestrate and can also handoffs to another agent.",
    instructions="Handle general requests and do handover if there's an agent specialized in the task. If the user ask your name, tell them you're kaenova.",
    service=COMMON_AGENT_SERVICE,
    plugins=[
        document_search_agent,
        light_agent
    ]
)