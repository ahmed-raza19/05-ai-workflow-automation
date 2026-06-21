import logging
import os

LOG_DIRECTORY = "logs"
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, "workflow.log")


def configure_logger() -> logging.Logger:
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    logger = logging.getLogger("workflow_automation")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


logger = configure_logger()
