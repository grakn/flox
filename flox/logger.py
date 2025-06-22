import logging
import sys
import structlog
from typing import Callable, Optional
from pythonjsonlogger import jsonlogger
from .config import FloxConfig

# This will hold the callback if registered
_log_callback_handler: Optional[Callable[[dict], None]] = None

def register_log_callback(callback: Callable[[dict], None]):
    global _log_callback_handler
    _log_callback_handler = callback

def _callback_processor(logger, method_name, event_dict):
    if _log_callback_handler:
        try:
            _log_callback_handler(event_dict.copy())  # pass copy to avoid mutation
        except Exception as e:
            # Don't allow logging failures to crash the app
            logger.warning("log_callback_failed", error=str(e))
    return event_dict

def setup_logging(config: FloxConfig):
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(message)s')
    handler.setFormatter(formatter)

    logging.basicConfig(level=config.log_level, handlers=[handler])

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            _callback_processor,  # ← your callback processor here
            structlog.processors.EventRenamer("message"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
