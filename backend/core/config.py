"""
Core configuration module for Jarvis backend.
Loads settings from .env and validates on startup.
Fails loudly (never silently) if required config is missing.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from loguru import logger


# Find project root (parent of backend/)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Jarvis backend settings loaded from .env file."""

    # === OpenAI ===
    openai_api_key: str = Field(..., description="OpenAI API key — REQUIRED")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )

    # === Model IDs (as defined in roadmap) ===
    model_reasoning_default: str = Field(
        default="gpt-5.6-luna",
        description="Default reasoning model"
    )
    model_reasoning_complex: str = Field(
        default="gpt-5.6-terra",
        description="Complex/fallback reasoning model"
    )
    model_stt: str = Field(
        default="gpt-live-transcribe",
        description="Speech-to-text model"
    )
    model_tts: str = Field(
        default="tts-1",
        description="Text-to-speech model"
    )
    tts_voice: str = Field(
        default="onyx",
        description="TTS voice (onyx sounds professional/Jarvis-like)"
    )

    # === Server ===
    backend_host: str = Field(default="127.0.0.1", description="Backend host")
    backend_port: int = Field(default=8765, description="Backend port")

    # === Rate limiting (Phase 3 guard) ===
    daily_request_limit: int = Field(
        default=500,
        description="Max AI API requests per day"
    )

    # === Logging ===
    log_level: str = Field(default="INFO", description="Log level")

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
        "protected_namespaces": ("settings_",)
    }

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v == "sk-xxxx" or len(v) < 20:
            raise ValueError(
                "❌ OPENAI_API_KEY is missing or invalid! "
                "Please set a valid key in your .env file. "
                "Jarvis cannot start without it."
            )
        return v


def load_settings() -> Settings:
    """
    Load and validate settings. Raises immediately with a clear error
    message if required config is missing — never silently fails.
    """
    try:
        settings = Settings()
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"   └─ Model (default): {settings.model_reasoning_default}")
        logger.info(f"   └─ Model (complex): {settings.model_reasoning_complex}")
        logger.info(f"   └─ Backend: {settings.backend_host}:{settings.backend_port}")
        return settings
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Failed to load configuration!\n"
            f"   Error: {e}\n"
            f"   Make sure your .env file exists at project root with OPENAI_API_KEY set."
        )
        raise SystemExit(1) from e


# Singleton instance — imported by other modules
settings: Settings = load_settings()
