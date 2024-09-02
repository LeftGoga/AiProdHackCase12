import logging
import os
from uuid import uuid4

from fastapi import APIRouter, Form, UploadFile, File
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.templating import Jinja2Templates

from src.core.config import FilesConfig
from src.core.dto.message import Message
from src.services.chat import ChatService

messages = []


class ChatRouter(APIRouter):
    def __init__(
        self,
        chat_service: ChatService,
        templates: Jinja2Templates,
        files_config: FilesConfig,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(prefix="/chat", tags=["chat"])
        self.chat_service = chat_service
        self.templates = templates
        self.files_config = files_config
        self.add_api_route("/", self.get_chat, methods=["GET"])
        self.add_api_route("/send", self.send_message, methods=["POST"])

    async def get_chat(self, request: Request):
        return self.templates.TemplateResponse(
            "chat.html", {"request": request, "messages": messages}
        )

    async def send_message(
        self, text: str = Form(...), files: list[UploadFile] = File(None)
    ):
        message = Message(username="User", text=text)
        self.logger.info(f"New message: {message.model_dump(mode='json')}")
        file_urls = []

        if files:
            for file in files:
                if not file.size:
                    continue
                file_extension = file.filename.split(".")[-1]
                unique_filename = f"{uuid4()}.{file_extension}"
                file_path = os.path.join(
                    self.files_config.uploads_path, unique_filename
                )

                with open(file_path, "wb") as f:
                    f.write(await file.read())

                file_url = f"/files/uploads/{unique_filename}"
                file_urls.append(file_url)

        if file_urls:
            message.file_urls = file_urls

        messages.append(message)
        return JSONResponse(message.model_dump(mode="json"))
