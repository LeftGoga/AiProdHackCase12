import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.api.http import Routers
from src.core.config import Config
from src.services import Services


class App(FastAPI):
    def __init__(self, config: Config, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config.app
        super().__init__(*args, **kwargs, title=self.config.title)
        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.mount(
            f"/{config.files.static_path}",
            StaticFiles(directory=config.files.static_path),
            name="static",
        )
        self.mount(
            f"/{config.files.uploads_path}",
            StaticFiles(directory=config.files.uploads_path),
            name="uploads",
        )
        services = Services()
        routers = Routers(services, config.files)
        for router in routers.v1:
            self.include_router(router)

    def run(self):
        uvicorn.run(self, host=self.config.host, port=self.config.port)
