import logging
import os

from .history import HistorySingleton
from .plugins import LightPlugin, ChatHistoryPlugin
from .prompt import MAIN_AGENT_SYSTEM_PROMPT

from utils.singleton import singleton

from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents import ChatMessageContent

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)


@singleton
class AgentSingleton:
    def __init__(self):
        self.history = HistorySingleton()

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
        )
        kernel.add_service(chat_completion)

        # Add a plugin (the LightsPlugin class is defined below)
        kernel.add_plugin(
            LightPlugin(),
            plugin_name="Lights",
        )

        # Add a chat history plugin
        kernel.add_plugin(
            ChatHistoryPlugin(),
            plugin_name="ChatHistory"
        )

        execution_settings = AzureChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        kernel.add_function(
            prompt="{{system_message}}{{#each history}}<message role=\"{{role}}\">{{content}}</message>{{/each}}",
            function_name="chat",
            plugin_name="chat_plugin",
            template_format="handlebars",
            prompt_execution_settings=execution_settings,
        )

        self.kernel = kernel
        self.chat_completion = chat_completion


    async def chat(self, message: str) -> str:
        self.history.add_user_message(message)

        arguments = KernelArguments(
            system_message=MAIN_AGENT_SYSTEM_PROMPT,
        )

        execution_settings = AzureChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        response = (await self.chat_completion.get_chat_message_contents(
            chat_history=self.history,
            kernel=self.kernel,
            arguments=arguments,
            settings=execution_settings
        ))[0]

        self.history.add_message(ChatMessageContent(
            role=response.role,
            content=response.content
        ))

        return response.content