from semantic_kernel.agents import OrchestrationHandoffs
from semantic_kernel.agents import HandoffOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime

from utils.singleton import singleton
from hands_off_agent.agents import orchestrator_agent, document_search_agent, light_agent

from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory


import asyncio

import queue
import threading

import logging
from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

@singleton
class HandsoffAgent:
    queue_input = queue.Queue()
    queue_output = queue.Queue()

    chat_history = ChatHistory()

    main_session: None | threading.Thread = None

    output_buffer = []

    def __init__(self):

        self.chat_history = ChatHistory()

        self.runtime = InProcessRuntime()

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
                    "DocumentSearchAgent": "Transfer to this agent if there's a request that are need some searching for knowledge. This will search an internal document.",
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
            human_response_function=self.__user_input__,
            agent_response_callback= lambda x : self._on_agent_response_(x),
        )

        self.counter = 0

    def _on_agent_response_(self, response: ChatMessageContent):
        self.chat_history.add_message(response)

        self.counter += 1

        if response.content is not None and response.content.strip() != "":
           self._return_output_debounce_(response.content)

    def _return_output_debounce_(self, text: str):
        self.output_buffer.append(text)

        def return_output(memory_buffer:list[str], current_buffer: list[str]):
            if "".join(memory_buffer) != "".join(current_buffer):
                return
            self.queue_output.put("\n\n".join(self.output_buffer))
            self.output_buffer = [] 

        # After 2 seconds run the return_output function and compare the copied buffers and and active buffers
        current_output_buffer = self.output_buffer[:]
        timer = threading.Timer(5, return_output, (self.output_buffer, current_output_buffer))
        timer.start()

    async def __user_input__(self) -> ChatMessageContent:
        # Get user input
        user_input = self.queue_input.get()
        message_content = ChatMessageContent(
                role=AuthorRole.USER,
                content=user_input
        )
        return message_content

    def chat(self, message: str) -> str:
        # Add to ChatHistory
        self.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=message
            )
        )

        # Place message to process by model
        self.queue_input.put(message)

        # Start the model (if not started)
        if self.main_session is None:
            self.start_agent()


        # wait for the output when done processing
        output = str(self.queue_output.get())

        return output

    # Consuming buffered user input
    def start_agent(self):
        """Start the multi-agent system in a background thread (non-blocking)"""

        if self.main_session is not None:
            raise Exception("Multi-agent is already running.")

        # Running the chat session on the thread
        self.main_session = threading.Thread(target=self.__loop_executor__)
        self.main_session.start()


    async def chat_loop(self, orchestrator: HandoffOrchestration, runtime: InProcessRuntime, queue_input: queue.Queue, agent_response_callback: callable):
        runtime.start()
        while True:
            initial_message = queue_input.get()
            orchestration_result = await orchestrator.invoke(initial_message, runtime)
            result = await orchestration_result.get()

            # Check if the results is a list
            if isinstance(result, list):
                agent_response_callback(result[-1])
                return
            agent_response_callback(result)

    def __loop_executor__(self):
        # Running loop executor
        asyncio.new_event_loop().run_until_complete(self.chat_loop(self.handoff_orchestration, self.runtime, self.queue_input, self._on_agent_response_))

    def stop_agent(self):
        if self.coroutine is not None:
            self.coroutine.cancel()
            self.coroutine = None

    def is_running(self) -> bool:
        return self.coroutine is not None and not self.coroutine.done()

    async def get_state(self):
        return await self.runtime.save_state()

    def get_history(self):
        return self.chat_history
    
    def set_state(self, state):
        self.runtime.load_state(state)

    def set_history(self, history: ChatHistory):
        self.chat_history = history