from hands_off_agent.common import COMMON_AGENT_SERVICE
from hands_off_agent.agents.light_agent.plugins.light import LightPlugin
from semantic_kernel.agents import ChatCompletionAgent

light_agent = ChatCompletionAgent(
    name="LightAgent",
    description="A home assistant that mainly handles light control",
    instructions="Handle light control requests. If the user ask your name, tell them you're mahendra. When transfering to another agent, you don't need to send me any text!",
    service=COMMON_AGENT_SERVICE,
    plugins=[LightPlugin()]
)   