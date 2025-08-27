# Azure App Function - Semantic Kernel

## To prepare it

1. Clone the repository
2. Create a virtual environment
3. Install the required packages
4. Set up your Azure OpenAI credentials from `.env.example` `.env` file

## To run it

```sh
$ func start
```

## To use it

### Hello (with name)
```sh
$ curl http://localhost:7071/api/hello?name=John
```
## Single Agent

### Chat with llm
I have integrate some of tools that you can use. Refer to `semantif/plugins.py` for the tools.
There's currently 2 tools:
- Lamp management
  - Model can turn on / off the lamp
  - Model can get an id of the lamp
  - Model can search for lamp detail by its name
- Chat history - Model can retrieve the chat history (I dunno why i do it lol)

```sh
$ curl --get --data-urlencode "chat=<your message>" http://localhost:7071/api/single/chat
```

### Check history
```sh
$ curl http://localhost:7071/api/single/history
```

### Export chat
```sh
$ curl http://localhost:7071/api/single/history/export
```

### Import chat
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/single/history/import
```

### Export chat (compressed)
```sh
$ curl http://localhost:7071/api/single/history/export/compress
```

### Import chat (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/single/history/import/compress
```

## Multi Agent

### Start the session
This will start a session to the multi-agent system.

```sh
$ curl -X POST -d '{"chat":"<your message>"}' http://localhost:7071/api/multi/chat/start
```

It will hang for waiting to return a response. But, it will not return until you finish the agent. You can open new terminal for contributing into the chat

### Send a message to the session
This will send a message to the multi-agent system.

```sh
$ curl -X POST -d '{"chat":"<your message>"}' http://localhost:7071/api/multi/chat
```

### Check history
```sh
$ curl http://localhost:7071/api/multi/history
```

### Export chat
```sh
$ curl http://localhost:7071/api/multi/history/export
```

### Import chat
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/history/import
```

### Export chat (compressed)
```sh
$ curl http://localhost:7071/api/multi/history/export/compress
```

### Import chat (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/history/import/compress
```

### Export state
```sh
$ curl http://localhost:7071/api/multi/state/export
```

### Import state
```sh
$ curl -X POST --header "Content-Type: application/json" -d '<your state data>' http://localhost:7071/api/multi/state/import
```

### Export state (compressed)
```sh
$ curl http://localhost:7071/api/multi/state/export/compress
```

### Import state (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/state/import/compress
```


## Todo
1. Setup chat history for multi agent thingy. Still don't know how to get around the state management and chat history lifecycle.