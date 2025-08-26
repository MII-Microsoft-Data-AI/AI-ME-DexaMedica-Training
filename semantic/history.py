from utils.singleton import singleton

from semantic_kernel.contents.chat_history import ChatHistory

@singleton
class HistorySingleton(ChatHistory):
    def __init__(self):
        super().__init__()