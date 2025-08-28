import queue
import asyncio
import threading

from utils.singleton import singleton
from multi_agent.agents import orchestrator_agent

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread


@singleton
class MultiAgent:

    # This is for buffering user input while waiting the 
    # agent halting for user input
    thread: ChatHistoryAgentThread = ChatHistoryAgentThread()

    queue_input = queue.Queue()
    queue_output = queue.Queue()

    main_session: threading.Thread | None = None

    def __init__(self):
        self.agent = orchestrator_agent

    def chat(self, message):
        if self.main_session is None:
            return str(self.start_agent(message))
        else:
            self.queue_input.put(message)
            return str(self.queue_output.get())

    # Publishing user input
    def start_agent(self, message):
        self.queue_input.put(message)
        
        # Run the model chat loop in the background
        self.main_session = threading.Thread(target=self.__loop_executor__, name='main-thread')
        self.main_session.start()

        return self.queue_output.get()

    def __loop_executor__(self):
        print("starting, loop")
        asyncio.new_event_loop().run_until_complete(self.chat_loop(self.agent, self.queue_input, self.queue_output, self.thread))

    async def chat_loop(self, agent: ChatCompletionAgent, queue_input: queue.Queue, queue_output: queue.Queue, thread: ChatHistoryAgentThread):
        while True:
            print("loop running")
            user_input = queue_input.get()

            print(user_input)
            if user_input == "\\q":
                break
            
            print("Getting response")
            response = await agent.get_response(
                messages=user_input,
                thread=thread,
            )

            print("Response gotten", response)
            queue_output.put(response)

    def get_history(self):
        return self.thread._chat_history

    def set_history(self, history: ChatHistory):
        self.thread = ChatHistoryAgentThread(
            chat_history=history
        )