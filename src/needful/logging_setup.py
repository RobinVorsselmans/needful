import logging
import os

FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s"

def setup_logging() -> None:
    """
    Sets up logging for the application.

    The log level is determined by the LOG_LEVEL environment variable.
    If LOG_LEVEL is not set, the default log level is INFO.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    #libraries like uvicorn, httpx, ... only from WARNING and above,  our own code from the env variable
    logging.basicConfig(level=logging.WARNING, format=FORMAT)
    logging.getLogger("needful").setLevel(log_level_str)