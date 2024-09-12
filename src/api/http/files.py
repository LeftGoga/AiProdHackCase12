import logging
import os
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.templating import Jinja2Templates

from src.core.config import FilesConfig
from src.services import FileService


class FileRouter(APIRouter):
    def __init__(
        self,
        file_service: FileService,
        templates: Jinja2Templates,
        files_config: FilesConfig,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(prefix="/files", tags=["files"])
        self.file_service = file_service
        self.templates = templates
        self.files_config = files_config
        self.add_api_route("/", self.get_upload_page, methods=["GET"])
        self.add_api_route("/upload/", self.upload, methods=["POST"])

    async def get_upload_page(self, request: Request):
        return self.templates.TemplateResponse("files.html", {"request": request})

    async def upload(self, files: list[UploadFile] = File(...)):
        file_urls = []
        file_paths = []
        try:
            for file in files:
                unique_filename = f"{uuid4()}_{file.filename}"
                file_path = os.path.join(
                    self.files_config.uploads_path, unique_filename
                )

                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                file_paths.append(file_path)
                file_urls.append(f"/files/uploads/{unique_filename}")

            self.file_service.upload_files(file_paths)

            return JSONResponse({"success": True, "file_urls": file_urls})

        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)})
