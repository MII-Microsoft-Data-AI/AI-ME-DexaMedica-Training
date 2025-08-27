from multi_agent.common import COMMON_AGENT_SERVICE
from multi_agent.agents.light_agent.plugins.light import LightPlugin
from semantic_kernel.agents import ChatCompletionAgent

light_agent = ChatCompletionAgent(
    name="LightAgent",
    description="A home assistant that mainly handles light control",
    instructions="Handle light control requests.",
    service=COMMON_AGENT_SERVICE,
    plugins=[LightPlugin()]
)   