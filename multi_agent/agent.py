from semantic_kernel.agents import OrchestrationHandoffs
from semantic_kernel.agents import HandoffOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime

from utils.singleton import singleton
from multi_agent.agents import orchestrator_agent, document_search_agent, light_agent

from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory

import asyncio

@singleton
class MultiAgent:

    # This is for buffering user input while waiting the 
    # agent halting for user input
    buffered_user_input: str | None = None
    main_tasks: None | str = None
    chat_history: ChatHistory = ChatHistory()

    def __init__(self):
        self.agents = [
            orchestrator_agent,
            document_search_agent,
            light_agent,
        ]

        self.handoffs = (
            OrchestrationHandoffs()
            .add_many(    # Use add_many to add multiple handoffs to the same source agent at once
                source_agent="OrchestratorAgent",
                target_agents={
                    "DocumentSearchAgent": "Transfer to this agent if there's a request on document search",
                    "LightAgent": "Transfer to this agent if there's a request on smart home light control",
                },
            )
            .add(    
                source_agent="DocumentSearchAgent",
                description="Transfer to general agent who orchestrate to another task",
                target_agent="OrchestratorAgent",
            )
            .add(
                source_agent="LightAgent",
                description="Transfer to general agent who orchestrate to another task",
                target_agent="OrchestratorAgent",
            )
        )

        self.handoff_orchestration = HandoffOrchestration(
            members=self.agents,
            handoffs=self.handoffs,
            human_response_function=self._wait_for_user_input,
            agent_response_callback= lambda x : self._on_agent_response(x)
        )

        self.runtime = InProcessRuntime()
        self.runtime.start()

    def _on_agent_response(self, response: ChatMessageContent):
        self.chat_history.add_message(response)

    # Consuming buffered user input
    async def _wait_for_user_input(self) -> ChatMessageContent:
        if self.buffered_user_input is None:
            await asyncio.sleep(1)
            return await self._wait_for_user_input()

        # Get the buffered user input
        buffered_user_input = str(self.buffered_user_input)
        self.buffered_user_input = None

        # Save the user input to chat history
        message_content = ChatMessageContent(
                role=AuthorRole.USER,
                content=buffered_user_input
        )

        self.chat_history.add_message(
            message_content
        )

        return message_content

    # Publishing user input
    async def start_agent(self, message):
        if self.main_tasks is not None:
            raise Exception("Multi-agent is already running.")

        self.main_tasks = message
        self.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=message
            )
        )

        orchestration_result = await self.handoff_orchestration.invoke(message, runtime=self.runtime)
        await orchestration_result.get()

    def send_message(self, message):
        if self.main_tasks is None:
            raise Exception("Multi-agent is not running. Please start the agent first.")
        
        self.buffered_user_input = message

    async def get_state(self):
        return await self.runtime.save_state()

    def get_history(self):
        return self.chat_history
    
    def set_state(self, state):
        self.runtime.load_state(state)

    def set_history(self, history: ChatHistory):
        self.chat_history = history