import azure.functions as func
import logging

from semantic.agent import AgentSingleton

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


@app.route(route="chat")
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    chat = req.params.get('chat')
    if not chat:
        return func.HttpResponse("No chat message provided.", status_code=400)

    print('masuk')
    response = await agent.chat(chat)
    return func.HttpResponse(response, status_code=200)