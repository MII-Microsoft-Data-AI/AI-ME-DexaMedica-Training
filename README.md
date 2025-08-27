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