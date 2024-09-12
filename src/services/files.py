import logging


class FileService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def upload_files(self, file_paths: list[str]): ...
