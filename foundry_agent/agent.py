from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageDeltaChunk
import queue
import os

class FoundryAgent:

    def __init__(self):
        endpoint = os.getenv("FOUNDRY_ENDPOINT")
        agent_id = os.getenv("FOUNDRY_AGENT_ID")

        if not endpoint or not agent_id:
            raise ValueError("FOUNDRY_ENDPOINT and FOUNDRY_AGENT_ID environment variables must be set")

        self.project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=endpoint
        )
        self.agent = self.project.agents.get_agent(agent_id)
        self.thread = self.project.agents.threads.create()
        print(f"Created thread, ID: {self.thread.id}")

    def stream_chat(self, input_text: str, on_response=None):
        self.project.agents.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=input_text
        )

        run_stream = self.project.agents.runs.stream(
            thread_id=self.thread.id,
            agent_id=self.agent.id,
            content_type='application/json'
        )

        print("Agent > ", end='', flush=True)
        for response in run_stream.event_handler:
            data = response[1]
            if not isinstance(data, MessageDeltaChunk):
                continue
            stream_content = data.delta.content[0].text.value
            print(stream_content, end='', flush=True)
            if on_response:
                on_response(stream_content)
        print("\n")
        if on_response:
            on_response("[[DONE]]")

    def stream_chat_async(self, input_text: str, chunk_queue: queue.Queue):
        """Async version that puts chunks into a queue for real-time streaming"""
        try:
            self.project.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=input_text
            )

            run_stream = self.project.agents.runs.stream(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                content_type='application/json'
            )

            for response in run_stream.event_handler:
                data = response[1]
                if not isinstance(data, MessageDeltaChunk):
                    continue
                stream_content = data.delta.content[0].text.value
                # Put chunk into queue for real-time streaming
                chunk_queue.put(stream_content)
            
            # Signal completion
            chunk_queue.put("[[DONE]]")
            
        except Exception as e:
            chunk_queue.put(f"ERROR: {str(e)}")
            chunk_queue.put("[[DONE]]")

    def new_chat(self):
        self.thread = self.project.agents.threads.create()
        print(f"Created new thread, ID: {self.thread.id}")