import logging

from src.app import App
from src.core.config import Config


def main():
    logging.basicConfig(level=logging.INFO)
    config = Config()
    application = App(config)
    application.run()


if __name__ == "__main__":
    main()
