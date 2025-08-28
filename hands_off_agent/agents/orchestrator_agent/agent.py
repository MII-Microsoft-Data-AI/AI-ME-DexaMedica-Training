from hands_off_agent.common import COMMON_AGENT_SERVICE
from semantic_kernel.agents import ChatCompletionAgent

orchestrator_agent = ChatCompletionAgent(
    name="OrchestratorAgent",
    description="An assistant that helps user and also manage, analyze request, orchestrate and can also handoffs to another agent.",
    instructions="Handle general requests and do handover if there's an agent specialized in the task. If the user ask your name, tell them you're kaenova. When transfering to another agent, you don't need to send me any text!",
    service=COMMON_AGENT_SERVICE,
)