import base64
import zlib
import json

def state_to_base64(history: dict) -> str:
    return base64.b64encode(json.dumps(history).encode()).decode()

def state_from_base64(data: str) -> dict:
    json_str = base64.b64decode(data.encode()).decode()
    return json.loads(json_str)

def state_compress(history: dict) -> str:
    return base64.b64encode(zlib.compress(json.dumps(history).encode())).decode()

def state_decompress(data: str) -> dict:
    json_str = zlib.decompress(base64.b64decode(data.encode())).decode()
    return json.loads(json_str)