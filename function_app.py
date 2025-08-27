import azure.functions as func
import logging
import json

from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent

from utils.history import chat_history_from_base64, chat_history_to_base64, chat_history_compress, chat_history_decompress
from utils.state import state_compress, state_decompress, state_to_base64, state_from_base64

from threading import Thread

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
agent = AgentSingleton()
multi_agent = MultiAgent()

@app.route(route="hello")
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.route(route="single/chat")
async def single_chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    chat = req.params.get('chat')
    if not chat:
        return func.HttpResponse("No chat message provided.", status_code=400)

    response = await agent.chat(chat)
    # return func.HttpResponse("Hello", status_code=200)
    return func.HttpResponse(response, status_code=200)


@app.route(route="single/history")
async def single_history(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()

    all_messages = []

    for message in history.messages:
        all_messages.append(f"{message.role}: {message.content}")

    if (len(all_messages) == 0):
        return func.HttpResponse("No chat history available.", status_code=200)

    return func.HttpResponse(str("\n".join(all_messages)), status_code=200)

@app.route(route="single/history/export")
async def single_history_export(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return func.HttpResponse(history_base64, status_code=200)

@app.route(route="single/history/import", methods=["POST"])
async def single_history_import(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    if (req.method != "POST"):
        return func.HttpResponse("Method not allowed.", status_code=405)

    base64_data = req.get_json().get('data')
    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    history = chat_history_from_base64(base64_data)
    if not history:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    agent.set_history(history)

    return func.HttpResponse("Successfully updating chat history.", status_code=200)


@app.route(route="single/history/export/compress")
async def single_history_export_compress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_compress(history)

    return func.HttpResponse(history_base64, status_code=200)

@app.route(route="single/history/import/compress", methods=["POST"])
async def single_history_import_decompress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    if (req.method != "POST"):
        return func.HttpResponse("Method not allowed.", status_code=405)

    base64_data = req.get_json().get('data')
    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    history = chat_history_decompress(base64_data)
    if not history:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    agent.set_history(history)

    return func.HttpResponse("Successfully updating chat history.", status_code=200)


@app.route(route="multi/chat/start", methods=["POST"])
async def multi_chat_start(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_chat.')

    try:
        req_body = req.get_json()
        chat_message = req_body.get('chat')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not chat_message:
        return func.HttpResponse("No chat message provided in the request body.", status_code=400)

    await multi_agent.start_agent(chat_message)
    return func.HttpResponse("Multi-agent started successfully.", status_code=202)


@app.route(route="multi/chat", methods=["POST"])
async def multi_chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_chat.')

    try:
        req_body = req.get_json()
        chat_message = req_body.get('chat')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not chat_message:
        return func.HttpResponse("No chat message provided in the request body.", status_code=400)

    try:
        multi_agent.send_message(chat_message)
    except Exception as e:
        logging.error(f"Error sending message to multi-agent: {e}")
        return func.HttpResponse("Error sending message to multi-agent. " + str(e), status_code=500)

    return func.HttpResponse("Message sent to multi-agent.", status_code=202)


@app.route(route="multi/history")
async def multi_history(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_history.')

    history = multi_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]

    if not all_messages:
        return func.HttpResponse("No chat history available.", status_code=200)

    return func.HttpResponse("\n".join(all_messages), status_code=200)


@app.route(route="multi/history/export")
async def multi_history_export(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_history_export.')

    history = multi_agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return func.HttpResponse(history_base64, status_code=200)


@app.route(route="multi/history/import", methods=["POST"])
async def multi_history_import(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_history_import.')

    try:
        req_body = req.get_json()
        base64_data = req_body.get('data')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    history = chat_history_from_base64(base64_data)
    if not history:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    multi_agent.set_history(history)

    return func.HttpResponse("Successfully updating chat history.", status_code=200)


@app.route(route="multi/history/export/compress")
async def multi_history_export_compress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_history_export_compress.')

    history = multi_agent.get_history()
    history_base64 = chat_history_compress(history)

    return func.HttpResponse(history_base64, status_code=200)


@app.route(route="multi/history/import/compress", methods=["POST"])
async def multi_history_import_decompress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_history_import_decompress.')

    try:
        req_body = req.get_json()
        base64_data = req_body.get('data')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    history = chat_history_decompress(base64_data)
    if not history:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    multi_agent.set_history(history)

    return func.HttpResponse("Successfully updating chat history.", status_code=200)


@app.route(route="multi/state/export")
async def multi_state_export(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_state_export.')

    state = await multi_agent.get_state()
    base64 = state_to_base64(state)

    return func.HttpResponse(base64, status_code=200)


@app.route(route="multi/state/import", methods=["POST"])
async def multi_state_import(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_state_import.')

    try:
        req_body = req.get_json()
        base64_data = req_body.get('data')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    state = state_from_base64(base64_data)
    if not state:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    multi_agent.set_state(state)

    return func.HttpResponse("Successfully updating agent state.", status_code=200)


@app.route(route="multi/state/export/compress")
async def multi_state_export_compress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_state_export_compress.')

    state_str = multi_agent.get_state()
    state_dict = json.loads(state_str)
    state_base64 = state_compress(state_dict)

    return func.HttpResponse(state_base64, status_code=200)


@app.route(route="multi/state/import/compress", methods=["POST"])
async def multi_state_import_compress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request for multi_state_import_compress.')

    try:
        req_body = req.get_json()
        base64_data = req_body.get('data')
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    if not base64_data:
        return func.HttpResponse("No base64 data provided.", status_code=400)

    state_dict = state_decompress(base64_data)
    if not state_dict:
        return func.HttpResponse("Invalid base64 data.", status_code=400)

    state_str = json.dumps(state_dict)
    multi_agent.set_state(state_str)

    return func.HttpResponse("Successfully updating agent state.", status_code=200)