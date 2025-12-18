"""
Logging and Monitoring Utilities
Provides structured logging with file rotation and error tracking
"""

import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import traceback
import json


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        return json.dumps(log_data)


def setup_logging(app):
    """Set up application logging"""

    log_folder = Path(app.config.get('LOG_FOLDER', 'logs'))
    log_folder.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))

    # Remove default handlers
    app.logger.handlers = []

    # Console Handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    app.logger.addHandler(console_handler)

    # File Handler - Application Log (with rotation)
    app_log_file = log_folder / 'app.log'
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(console_formatter)
    app.logger.addHandler(app_handler)

    # File Handler - Error Log (JSON format)
    error_log_file = log_folder / 'error.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    app.logger.addHandler(error_handler)

    # File Handler - Access Log
    access_log_file = log_folder / 'access.log'
    access_handler = TimedRotatingFileHandler(
        access_log_file,
        when='midnight',
        interval=1,
        backupCount=30
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(console_formatter)

    # Create access logger
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)

    app.logger.setLevel(log_level)
    app.logger.info('Logging configured successfully')


def log_request(request, response, user_id=None):
    """Log HTTP request"""
    access_logger = logging.getLogger('access')

    log_data = {
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'user_id': user_id
    }

    access_logger.info(json.dumps(log_data))


def log_error(app, error, user_id=None, request=None):
    """Log application error"""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'user_id': user_id
    }

    if request:
        error_data.update({
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr
        })

    app.logger.error(f"Application error: {json.dumps(error_data)}", exc_info=True)


def log_security_event(event_type, details, user_id=None):
    """Log security-related events"""
    security_logger = logging.getLogger('security')

    event_data = {
        'event_type': event_type,
        'details': details,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }

    security_logger.warning(json.dumps(event_data))


class RequestLogger:
    """Middleware for logging requests"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Log response status
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
