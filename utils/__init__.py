"""Utilities package - Helper functions, validators, security, file operations"""

from .security import hash_ip, set_security_headers, log_security_event
from .validation import (
    validate_password,
    validate_voice,
    sanitize_display_name,
    sanitize_html,
    validate_text_length,
    validate_speed
)
from .file_utils import (
    verify_file_ownership,
    secure_save_filename,
    ensure_directory_exists,
    get_file_size,
    delete_file_safe,
    list_audio_files,
    migrate_existing_files_ownership
)
from .helpers import (
    get_openai_client,
    get_agent_system,
    calculate_cost,
    estimate_audio_duration,
    format_timestamp,
    format_file_size,
    truncate_text,
    get_voice_description,
    parse_bool_env,
    chunk_text
)

__all__ = [
    # Security
    'hash_ip',
    'set_security_headers',
    'log_security_event',
    # Validation
    'validate_password',
    'validate_voice',
    'sanitize_display_name',
    'sanitize_html',
    'validate_text_length',
    'validate_speed',
    # File utilities
    'verify_file_ownership',
    'secure_save_filename',
    'ensure_directory_exists',
    'get_file_size',
    'delete_file_safe',
    'list_audio_files',
    'migrate_existing_files_ownership',
    # Helpers
    'get_openai_client',
    'get_agent_system',
    'calculate_cost',
    'estimate_audio_duration',
    'format_timestamp',
    'format_file_size',
    'truncate_text',
    'get_voice_description',
    'parse_bool_env',
    'chunk_text'
]
