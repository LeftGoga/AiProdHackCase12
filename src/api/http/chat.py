import asyncio
import os
import base64
import logging
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.requests import Request
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
        self.add_api_websocket_route("/ws", self.websocket_endpoint)

    async def get_chat(self, request: Request):
        return self.templates.TemplateResponse(
            "chat.html", {"request": request, "messages": messages}
        )

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.logger.info("WebSocket accepted")

        try:
            while True:
                message_data = await websocket.receive_json()

                text = message_data.get("text", "")

                file_urls = []
                files = message_data.get("files", [])
                for file in files:
                    filename = file["filename"]
                    content_base64 = file["content"]
                    unique_filename = f"{uuid4()}_{filename}"
                    file_path = os.path.join(
                        self.files_config.uploads_path, unique_filename
                    )

                    file_content = base64.b64decode(content_base64)
                    with open(file_path, "wb") as f:
                        f.write(file_content)

                    file_urls.append(f"/files/uploads/{unique_filename}")

                message = Message(username="User", text=text, file_urls=file_urls)
                messages.append(message)

                await websocket.send_json(message.model_dump(mode="json"))

                await asyncio.sleep(1)
                ai_response = Message(username="AI", text="Hey there!")
                await websocket.send_json(ai_response.model_dump(mode="json"))

        except WebSocketDisconnect:
            self.logger.warning("WebSocket disconnected")
