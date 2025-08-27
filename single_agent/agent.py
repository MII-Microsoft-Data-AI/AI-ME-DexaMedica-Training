import logging
import os

from .plugins.lights import LightPlugin
from .prompt import MAIN_AGENT_SYSTEM_PROMPT

from utils.singleton import singleton

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)


@singleton
class AgentSingleton:
    def __init__(self):
        self.history = ChatHistory()

        OPENAI_KEY = os.getenv("OPENAI_KEY")
        OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

        # Initialize the kernel
        kernel = Kernel()

        # Add Azure OpenAI chat completion
        chat_completion = AzureChatCompletion(
            deployment_name="main-gpt-4",
            api_key=OPENAI_KEY,
            endpoint=OPENAI_ENDPOINT,
            api_version="2025-01-01-preview",
            service_id="SChat",
        )
        kernel.add_service(chat_completion)

        # Add a plugin (the LightsPlugin class is defined below)
        kernel.add_plugin(
            LightPlugin(),
            plugin_name="PLights",
        )

        execution_settings = AzureChatPromptExecutionSettings(service_id=chat_completion.service_id)
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        kernel.add_function(
            plugin_name="PChat",
            function_name="FChat",
            template_format="handlebars",
            prompt="{{system_message}}{{#each history}}<message role=\"{{role}}\">{{content}}</message>{{/each}}",
            prompt_execution_settings=execution_settings,
        )

        self.kernel = kernel

    async def chat(self, message: str) -> str:
        self.history.add_user_message(message)

        # Change history to a list like [{"role": "user", "content": message}, ...]
        history_list = [{"role": msg.role.name.lower(), "content": msg.content} for msg in self.history.messages]

        arguments = KernelArguments(
            system_message=MAIN_AGENT_SYSTEM_PROMPT,
            history=history_list,
        ) 
        function = self.kernel.get_function(function_name="FChat", plugin_name="PChat")
        

        response = await self.kernel.invoke(
            function=function,
            arguments=arguments,
        );

        if response is None:
            logging.error("No response from the kernel.")
            return "I'm sorry, I couldn't process your request at this time."
        
        self.history.add_message(ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=str(response),
        ))

        return str(response)
    
    def clear_history(self):
        self.history.clear()

    def get_history(self):
        return self.history

    def set_history(self, history: ChatHistory):
        self.history = history
    