from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageDeltaChunk
import json

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://kaenova-aifoundary-testing.services.ai.azure.com/api/projects/kaenova-testing-project"
)

agent = project.agents.get_agent("asst_ArD5EUpmoaJJDxr9R7GtKlQy")

thread = project.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

while True:
    input_text = input("User > ")
    if input_text.lower() in ['exit', 'quit']:
        break
    message = project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=input_text
    )

    run_stream = project.agents.runs.stream(
        thread_id=thread.id,
        agent_id=agent.id,
        content_type='application/json'
    )

    print("Agent > ", end='', flush=True)
    for response in run_stream.event_handler:
        data = response[1]
        if not isinstance(data, MessageDeltaChunk):
            continue
        stream_content = data.delta.content[0].text.value
        print(stream_content, end='', flush=True)
    print("\n")