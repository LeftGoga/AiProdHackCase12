import logging

from src.core.dto.message import Message


class ChatService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_message(self, message: Message): ...
