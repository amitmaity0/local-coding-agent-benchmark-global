"""Configuration management for MotionForge.

Loads settings from YAML files and environment variables.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


@dataclass
class ComfyUIConfig:
    """ComfyUI service configuration."""

    host: str = "127.0.0.1"
    port: int = 8188
    websocket_timeout: int = 300


@dataclass
class LMStudioConfig:
    """LM Studio service configuration."""

    host: str = "127.0.0.1"
    port: int = 1234
    model: str = ""
    timeout: int = 600


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///./motionforge.db"
    echo: bool = False


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 7000
    debug: bool = False


@dataclass
class GenerationConfig:
    """Generation configuration."""

    candidates_per_iteration: int = 1
    parallel_generation: bool = False


@dataclass
class OptimizationConfigData:
    """Optimization strategy configuration.

    Loaded from YAML under the 'optimization' key.
    """

    improvement_threshold: float = 1.0
    plateau_iterations: int = 2
    targeted_score_threshold: float = 70.0
    recovery_regression_threshold: float = 5.0
    exploration_probability: float = 0.25


@dataclass
class AppConfig:
    """Top-level application configuration."""

    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    comfyui: ComfyUIConfig = field(default_factory=ComfyUIConfig)
    lmstudio: LMStudioConfig = field(default_factory=LMStudioConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    optimization: OptimizationConfigData = field(
        default_factory=OptimizationConfigData
    )
    experiments_dir: str = "experiments"
    workflows_dir: str = "workflows"
    configs_dir: str = "configs"
    log_level: str = "INFO"


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load configuration from a YAML file, falling back to defaults.

    Args:
        path: Path to YAML config file. If None, uses defaults.

    Returns:
        Configured AppConfig instance.
    """
    config = AppConfig()
    if path is None:
        default_path = Path("configs/default.yaml")
        if default_path.exists():
            path = str(default_path)
        else:
            logger.info("No config file found; using defaults")
            return config

    path = Path(path)
    if not path.exists():
        logger.warning(f"Config file not found: {path}; using defaults")
        return config

    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    if "server" in data:
        config.server = ServerConfig(**data["server"])
    if "database" in data:
        config.database = DatabaseConfig(**data["database"])
    if "comfyui" in data:
        config.comfyui = ComfyUIConfig(**data["comfyui"])
    if "lmstudio" in data:
        config.lmstudio = LMStudioConfig(**data["lmstudio"])
    if "experiments_dir" in data:
        config.experiments_dir = data["experiments_dir"]
    if "workflows_dir" in data:
        config.workflows_dir = data["workflows_dir"]
    if "log_level" in data:
        config.log_level = data["log_level"]
    if "generation" in data:
        config.generation = GenerationConfig(**data["generation"])
    if "optimization" in data:
        config.optimization = OptimizationConfigData(**data["optimization"])

    logger.info(f"Configuration loaded from {path}")
    return config


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru logging.

    Args:
        level: Logging level string.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )