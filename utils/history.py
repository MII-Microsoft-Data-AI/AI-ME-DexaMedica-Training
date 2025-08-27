from semantic_kernel.contents.chat_history import ChatHistory

import base64
import zlib

def chat_history_to_file(history: ChatHistory, file_path: str):
    with open(file_path, "w") as f:
        f.write(history.serialize())

def chat_history_from_file(file_path: str) -> ChatHistory:
    with open(file_path, "r") as f:
        json_str = f.read()
        return ChatHistory.restore_chat_history(json_str)
    

def chat_history_to_base64(history: ChatHistory) -> str:
    return base64.b64encode(history.serialize().encode()).decode()

def chat_history_from_base64(data: str) -> ChatHistory:
    json_str = base64.b64decode(data.encode()).decode()
    return ChatHistory.restore_chat_history(json_str)


def chat_history_compress(history: ChatHistory) -> str:
    return base64.b64encode(zlib.compress(history.serialize().encode())).decode()

def chat_history_decompress(data: str) -> ChatHistory:
    json_str = zlib.decompress(base64.b64decode(data.encode())).decode()
    return ChatHistory.restore_chat_history(json_str)