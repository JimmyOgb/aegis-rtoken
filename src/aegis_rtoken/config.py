"""Configuration settings for Aegis-rToken."""

import os
from pathlib import Path
import tomllib
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure environment variables from .env are loaded into os.environ for CLI subprocesses
load_dotenv(Path(".env"), override=False)


def _load_toml_config(config_path: Path = Path("config.toml")) -> Dict[str, Any]:
    """Loads configuration from config.toml if present."""
    if config_path.is_file():
        try:
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}
    return {}


_TOML_DATA = _load_toml_config()
_DEFAULT_PROVIDER = _TOML_DATA.get("model_provider", "bitget-qwen")
_PROVIDERS = _TOML_DATA.get("model_providers", {})
_PROVIDER_INFO = _PROVIDERS.get(_DEFAULT_PROVIDER, {})

_DEFAULT_MODEL = _TOML_DATA.get("model", "qwen3.8-max")
_DEFAULT_BASE_URL = _PROVIDER_INFO.get("base_url", "https://hackathon.bitgetops.com/v1")
_DEFAULT_WIRE_API = _PROVIDER_INFO.get("wire_api", "responses")
_DEFAULT_ENV_KEY = _PROVIDER_INFO.get("env_key", "BITGET_QWEN_API_KEY")
_DEFAULT_PROVIDER_NAME = _PROVIDER_INFO.get("name", "Bitget Qwen")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Asset & Execution Mode
    target_asset: str = Field(default="RAAPLUSDT", validation_alias="TARGET_ASSET")
    category: str = Field(default="SPOT", validation_alias="CATEGORY")
    market_data_source: str = Field(default="Bitget-UTA-v3", validation_alias="MARKET_DATA_SOURCE")
    execution_category: str = Field(default="SPOT", validation_alias="EXECUTION_CATEGORY")
    trading_mode: str = Field(default="demo", validation_alias="TRADING_MODE")  # Strictly 'demo' | 'paper' | 'dry_run'
    enable_demo_order: bool = Field(default=False, validation_alias="ENABLE_DEMO_ORDER")
    enable_real_demo_order: bool = Field(default=False, validation_alias="ENABLE_REAL_DEMO_ORDER")

    @field_validator("trading_mode")
    @classmethod
    def validate_trading_mode(cls, v: str) -> str:
        mode = v.lower().strip()
        if mode in ("live", "mainnet", "prod", "production"):
            raise ValueError(
                "LIVE TRADING STRICTLY PROHIBITED: Aegis-rToken is exclusively configured for "
                "Bitget Demo/Paper Trading. Live mainnet orders cannot be submitted."
            )
        if mode not in ("demo", "paper", "dry_run"):
            return "demo"
        return mode

    # LLM / Model Provider Configuration (Bitget Qwen Hackathon Provider)
    model: str = Field(default=_DEFAULT_MODEL, validation_alias="LLM_MODEL")
    llm_model: str = Field(default=_DEFAULT_MODEL, validation_alias="LLM_MODEL")
    model_provider: str = Field(default=_DEFAULT_PROVIDER, validation_alias="MODEL_PROVIDER")
    model_provider_name: str = Field(default=_DEFAULT_PROVIDER_NAME, validation_alias="MODEL_PROVIDER_NAME")
    llm_base_url: str = Field(default=_DEFAULT_BASE_URL, validation_alias="LLM_BASE_URL")
    wire_api: str = Field(default=_DEFAULT_WIRE_API, validation_alias="WIRE_API")

    # API Keys: Primary is BITGET_QWEN_API_KEY, fallback to LLM_API_KEY
    bitget_qwen_api_key: str = Field(default="", validation_alias="BITGET_QWEN_API_KEY")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")

    @model_validator(mode="after")
    def sync_model_and_keys(self):
        # Sync model names
        if self.model and not self.llm_model:
            self.llm_model = self.model
        elif self.llm_model and not self.model:
            self.model = self.llm_model

        # Sync API keys: prefer BITGET_QWEN_API_KEY, fallback to LLM_API_KEY
        if not self.bitget_qwen_api_key and self.llm_api_key:
            self.bitget_qwen_api_key = self.llm_api_key
        elif self.bitget_qwen_api_key and not self.llm_api_key:
            self.llm_api_key = self.bitget_qwen_api_key

        return self

    @property
    def effective_llm_key(self) -> str:
        """Returns the active LLM API key without exposing it in logs."""
        return (self.bitget_qwen_api_key or self.llm_api_key).strip()

    # Risk Engine Limits (Deterministic)
    max_spread_percent: float = Field(default=0.8, validation_alias="MAX_SPREAD_PERCENT")
    min_confidence_score: float = Field(default=0.75, validation_alias="MIN_CONFIDENCE_SCORE")
    max_allocation_usd: float = Field(default=500.0, validation_alias="MAX_ALLOCATION_USD")
    stale_data_timeout_seconds: float = Field(default=10.0, validation_alias="STALE_DATA_TIMEOUT_SECONDS")
    circuit_breaker_cooldown_seconds: int = Field(default=300, validation_alias="CIRCUIT_BREAKER_COOLDOWN_SECONDS")

    # Bitget Credentials (For official Bitget Demo/Testnet via bgc CLI)
    bitget_api_key: str = Field(default="", validation_alias="BITGET_API_KEY")
    bitget_secret_key: str = Field(default="", validation_alias="BITGET_SECRET_KEY")
    bitget_passphrase: str = Field(default="", validation_alias="BITGET_PASSPHRASE")
    bitget_api_base_url: str = Field(default="https://api.bitget.com", validation_alias="BITGET_API_BASE_URL")

    # API Server & Logging
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    logs_dir: Path = Field(default=Path("logs"))


# Cached global settings instance
settings = Settings()
