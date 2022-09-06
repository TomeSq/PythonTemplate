import logging
import logging.config

LOGGING = {
    "version": 1,
    "formatters": {
        "default": {"format": "%(asctime)s [%(levelname)s] %(message)s [%(module)s, %(lineno)d]"},
        "uvicorn_format": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": "%(levelprefix)s %(asctime)s | %(message)s [%(module)s, %(lineno)d]",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        }
    },
    "root": {"level": "DEBUG", "handlers": ["default"]},
    "disable_existing_loggers": False,
}

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
