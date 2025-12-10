
import logging
import json
import sys

class JsonFormatter(logging.Formatter):
    """Formatter to dump logs as JSON for Cloud Logging compatibility."""
    def format(self, record):
        log_obj = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record, self.datefmt)
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def get_logger(name: str) -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist used to avoid duplicate logs in re-imports
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger
