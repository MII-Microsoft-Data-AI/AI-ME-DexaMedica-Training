from semantic_kernel.agents import OrchestrationHandoffs
from semantic_kernel.agents import HandoffOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime

from utils.singleton import singleton
from multi_agent.agents import orchestrator_agent, document_search_agent, light_agent

from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory


import json

@singleton
class MultiAgent:

    # This is for buffering user input while waiting the 
    # agent halting for user input
    buffered_user_input: str | None = None

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
                    "DocumentSearchAgent": "Transfer to this agent if the issue is document search related",
                    "LightAgent": "Transfer to this agent if the issue is light control related",
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
            human_response_function=self._wait_for_user_input
        )

        self.runtime = InProcessRuntime()
        self.runtime.start()

    # Consuming buffered user input
    def _wait_for_user_input(self) -> ChatMessageContent:
        while self.buffered_user_input is None:
            pass  # Wait for user input
        
        # Get the buffered user input
        buffered_user_input = self.buffered_user_input
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
    def send_message(self, message):
        self.buffered_user_input = message

    def get_state(self):
        return self.runtime.get_state()
    
    def get_history(self):
        return self.chat_history.get_history()
    
    def set_state(self, state):
        self.runtime.load_state(state)

    def set_history(self, history: ChatHistory):
        self.chat_history = history