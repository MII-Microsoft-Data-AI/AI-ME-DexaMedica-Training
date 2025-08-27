from multi_agent.common import COMMON_AGENT_SERVICE
from semantic_kernel.agents import ChatCompletionAgent

orchestrator_agent = ChatCompletionAgent(
    name="OrchestratorAgent",
    description="An assistant that helps user and also manage, analyze request, orchestrate and can also handoffs to another agent.",
    instructions="Handle general requests.",
    service=COMMON_AGENT_SERVICE,
    plugins=[]
)