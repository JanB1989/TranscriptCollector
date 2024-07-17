import json
import logging
import os
from logging import LogRecord


def set_lambda_context(context):
    """Set the context attributes for the environment."""
    os.environ["AWS_REQUEST_ID"] = context.aws_request_id
    os.environ["FUNCTION_NAME"] = context.function_name
    os.environ["FUNCTION_VERSION"] = context.function_version
    os.environ["MEMORY_LIMIT"] = context.memory_limit_in_mb
    os.environ["LOG_GROUP_NAME"] = context.log_group_name
    os.environ["LOG_STREAM_NAME"] = context.log_stream_name


class MetadataFilter(logging.Filter):
    def filter(self, record):
        record.aws_request_id = os.getenv("AWS_REQUEST_ID", "UNKNOWN")
        record.function_name = os.getenv("FUNCTION_NAME", "UNKNOWN")
        record.function_version = os.getenv("FUNCTION_VERSION", "UNKNOWN")
        record.memory_limit = os.getenv("MEMORY_LIMIT", "UNKNOWN")
        record.log_group_name = os.getenv("LOG_GROUP_NAME", "UNKNOWN")
        record.log_stream_name = os.getenv("LOG_STREAM_NAME", "UNKNOWN")
        record.video_url = os.getenv("VIDEO_URL", "UNKNOWN")
        return True


def format_record(record):
    message = record.getMessage()
    if isinstance(message, dict):
        message = json.dumps(message)
    log_entry = (
        f"[{record.asctime}] "
        f"{record.levelname} - "
        f"{record.module}.{record.funcName} - "
        f"aws_request_id: {record.aws_request_id} - "
        f"function: {record.function_name}({record.function_version}) - "
        f"memory: {record.memory_limit} - "
        f"log_group: {record.log_group_name} - "
        f"log_stream: {record.log_stream_name} - "
        f"video_url: {record.video_url} - "
        f"Message: {message}"
    )
    return log_entry


class ExtendedLogRecord(LogRecord):
    aws_request_id: str
    function_name: str
    function_version: str
    memory_limit: str
    log_group_name: str
    log_stream_name: str
    video_url: str


class JsonFormatter(logging.Formatter):
    def format(self, record: ExtendedLogRecord) -> str:
        record.asctime = self.formatTime(record)
        return format_record(record)


def set_request_id(request_id: str):
    """Set the request_id for the environment."""
    os.environ["REQUEST_ID"] = request_id


def set_video_url(video_url: str):
    """Set the video_url for the environment."""
    os.environ["VIDEO_URL"] = video_url


def setup_logging():
    # Clear handlers for the root logger to prevent double logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []

    # Create or retrieve the "cloudwatch_logger"
    logger = logging.getLogger('cloudwatch_logger')
    logger.handlers = []
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    # Adding filter
    logger.addFilter(MetadataFilter())