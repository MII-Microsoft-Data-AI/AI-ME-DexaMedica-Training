import azure.functions as func
import logging

from semantic.agent import AgentSingleton
from utils.history import chat_history_from_base64, chat_history_to_base64, chat_history_compress, chat_history_decompress

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
agent = AgentSingleton()

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
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    chat = req.params.get('chat')
    if not chat:
        return func.HttpResponse("No chat message provided.", status_code=400)

    response = await agent.chat(chat)
    # return func.HttpResponse("Hello", status_code=200)
    return func.HttpResponse(response, status_code=200)


@app.route(route="single/history")
async def history(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()

    all_messages = []

    for message in history.messages:
        all_messages.append(f"{message.role}: {message.content}")

    if (len(all_messages) == 0):
        return func.HttpResponse("No chat history available.", status_code=200)

    return func.HttpResponse(str("\n".join(all_messages)), status_code=200)

@app.route(route="single/history/export")
async def history_export(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return func.HttpResponse(history_base64, status_code=200)

@app.route(route="single/history/import", methods=["POST"])
async def history_import(req: func.HttpRequest) -> func.HttpResponse:
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
async def history_export_compress(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_compress(history)

    return func.HttpResponse(history_base64, status_code=200)

@app.route(route="single/history/import/compress", methods=["POST"])
async def history_import_decompress(req: func.HttpRequest) -> func.HttpResponse:
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