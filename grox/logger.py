import logging
import sys
import structlog
from typing import Callable, Optional
from colorama import init, Fore, Style

init(autoreset=True)

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

    #level = event_dict.get("level", "").lower()
    #if level == "error":
    #    event_dict["event"] = f"{Fore.RED}{event_dict['event']}{Style.RESET_ALL}"
    #elif level == "warning":
    #    event_dict["event"] = f"{Fore.YELLOW}{event_dict['event']}{Style.RESET_ALL}"
    #elif level == "info":
    #    event_dict["event"] = f"{Fore.GREEN}{event_dict['event']}{Style.RESET_ALL}"
    return event_dict


def setup_logging(log_level: str, log_format: str):
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format="%(message)s",  # Let structlog handle rendering
    )

    log_renderer = (
        structlog.dev.ConsoleRenderer(colors=True)
        if log_format == "console"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            _callback_processor,
            structlog.processors.EventRenamer("message"),
            structlog.processors.dict_tracebacks,
            log_renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
