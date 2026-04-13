import logging
from typing import Optional, Any
from fastapi import Request
from pythonjsonlogger import json as jsonlogger

class GCPLogFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        # Cloud Run / GCP logging automatically parses the 'severity' field
        log_record['severity'] = record.levelname
        
        # Clean up standard python levelname to avoid duplication
        if 'levelname' in log_record:
            del log_record['levelname']

def _setup_base_logger(name: str = "runrun") -> logging.Logger:
    base_logger = logging.getLogger(name)
    base_logger.setLevel(logging.DEBUG)
    
    if not base_logger.handlers:
        log_handler = logging.StreamHandler()
        formatter = GCPLogFormatter('%(message)s %(levelname)s %(name)s %(filename)s %(lineno)d')
        log_handler.setFormatter(formatter)
        base_logger.addHandler(log_handler)
        
    # Silence third-party verbose loggers we don't care about
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('authlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return base_logger

class AppLogger:
    """
    A unified logging wrapper to consistently format logs for GCP
    and automatically inject contextual info from FastAPI Requests.
    """
    def __init__(self, name: str = "runrun"):
        self._logger = _setup_base_logger(name)

    def _build_extra(self, request: Optional[Request] = None, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        merged_extra = extra.copy() if extra else {}
        if request:
            merged_extra.update({
                "request.path": request.url.path,
                "request.method": request.method,
            })
            if hasattr(request, "endpoint") and request.endpoint:
                merged_extra["request.endpoint"] = request.endpoint.__name__
        return merged_extra

    def info(self, msg: str, request: Optional[Request] = None, extra: Optional[dict[str, Any]] = None) -> None:
        self._logger.info(msg, extra=self._build_extra(request, extra))

    def error(self, msg: str, request: Optional[Request] = None, extra: Optional[dict[str, Any]] = None, exc_info: bool = False) -> None:
        self._logger.error(msg, extra=self._build_extra(request, extra), exc_info=exc_info)
        
    def debug(self, msg: str, request: Optional[Request] = None, extra: Optional[dict[str, Any]] = None) -> None:
        self._logger.debug(msg, extra=self._build_extra(request, extra))
        
    def warning(self, msg: str, request: Optional[Request] = None, extra: Optional[dict[str, Any]] = None) -> None:
        self._logger.warning(msg, extra=self._build_extra(request, extra))

logger = AppLogger()
