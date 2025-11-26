"""
Configuration management for DeepAgent Coding Assistant.

This module provides hierarchical configuration loading from multiple sources:
1. CLI arguments (highest priority)
2. Environment variables
3. Project-level config (.deepagent.yaml in current directory)
4. User-level config (~/.config/deepagent/config.yaml)
5. Default values (lowest priority)
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for DeepAgent.

    Handles loading and merging configuration from multiple sources
    with proper priority ordering.
    """

    # Default configuration values
    DEFAULTS = {
        "workspace": {
            "path": "~/.deepagents/workspace",
            "auto_mkdir": True,
            "sessions_dir": "sessions",
        },
        "agent": {
            "model": "qwen2.5:14b",
            "max_iterations": 10,
            "logging": {
                "level": "INFO",
                "file": "agent.log",
                "console": True,
            },
        },
        "models": {
            "main_agent": {
                "model": "qwen2.5:14b",
                "temperature": 0.3,
                "num_ctx": 32768,
                "num_gpu": 1,
                "timeout": 300,
            },
            "code_generator": {
                "model": "codellama:13b-code",
                "temperature": 0.2,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
            "debugger": {
                "model": "qwen2.5-coder:latest",
                "temperature": 0.1,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
            "summarizer": {
                "model": "llama3.1:8b",
                "temperature": 0.4,
                "num_ctx": 8192,
                "num_gpu": 1,
                "timeout": 180,
            },
            "test_writer": {
                "model": "qwen2.5-coder:latest",
                "temperature": 0.2,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
            "refactorer": {
                "model": "qwen2.5-coder:latest",
                "temperature": 0.2,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
            "devops": {
                "model": "qwen2.5-coder:latest",
                "temperature": 0.2,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
            "code_review": {
                "model": "qwen2.5-coder:latest",
                "temperature": 0.1,
                "num_ctx": 16384,
                "num_gpu": 1,
                "timeout": 300,
            },
        },
        "middleware": {
            "memory": {
                "enabled": True,
                "threshold": 6000,
                "keep_recent_messages": 10,
            },
            "git_safety": {
                "enabled": True,
                "enforce": False,
            },
            "error_recovery": {
                "enabled": True,
                "max_retries": 3,
                "backoff_multiplier": 2.0,
            },
            "audit": {
                "enabled": True,
                "file": "audit.jsonl",
                "include_tool_calls": True,
                "include_responses": True,
            },
        },
        "mcp": {
            "filesystem": {
                "enabled": True,
                "restricted_to_workspace": True,
            },
            "shell": {
                "enabled": True,
                "timeout": 300,
                "allow_sudo": False,
            },
            "custom_servers": {},
        },
        "quality": {
            "min_quality_score": 7.5,
            "test_coverage": {
                "minimum_percentage": 80,
                "enforce": True,
            },
            "complexity": {
                "max_cyclomatic_complexity": 10,
                "max_cognitive_complexity": 15,
            },
            "security": {
                "scan_for_vulnerabilities": True,
                "block_on_high_severity": True,
            },
        },
        "subagents": {
            "enabled": {
                "code_generator": True,
                "debugger": True,
                "test_writer": True,
                "refactorer": True,
                "devops": True,
                "code_review": True,
                "code_navigator": True,
            },
            "code_review": {
                "auto_review_on_generate": True,
                "quality_gate_required_for_deployment": True,
            },
            "test_writer": {
                "auto_generate_tests": False,
                "test_framework": "pytest",
            },
        },
        "chat": {
            "prompt": "> ",
            "history_file": "~/.deepagent_history",
            "max_history": 1000,
            "auto_save": True,
            "save_interval": 300,
        },
        "performance": {
            "parallel_tool_calls": True,
            "max_parallel_calls": 5,
            "cache_enabled": True,
            "cache_ttl": 3600,
            "preload_models": False,
            "preload_roles": [],
        },
        "api": {
            "enabled": False,
            "host": "localhost",
            "port": 8000,
            "auth_token": None,
        },
        "features": {
            "experimental": {
                "multi_agent_collaboration": False,
                "vector_search": False,
                "semantic_code_search": False,
            },
            "legacy_mode": False,
        },
    }

    def __init__(self, config_file: str | Path | None = None, cli_overrides: dict | None = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Optional path to config file (overrides default search)
            cli_overrides: Optional dictionary of CLI argument overrides
        """
        self.config_file = Path(config_file) if config_file else None
        self.cli_overrides = cli_overrides or {}
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources with proper priority."""
        # Start with defaults
        self._config = self._deep_copy(self.DEFAULTS)

        # Load from config files (user, then project)
        if not self.config_file:
            # Load user-level config
            user_config_path = self._get_user_config_path()
            if user_config_path.exists():
                logger.info(f"Loading user config from: {user_config_path}")
                self._merge_config(self._load_yaml(user_config_path))

            # Load project-level config (higher priority)
            project_config_path = Path(".deepagent.yaml")
            if project_config_path.exists():
                logger.info(f"Loading project config from: {project_config_path}")
                self._merge_config(self._load_yaml(project_config_path))
        else:
            # Load specified config file
            if self.config_file.exists():
                logger.info(f"Loading config from: {self.config_file}")
                self._merge_config(self._load_yaml(self.config_file))
            else:
                logger.warning(f"Config file not found: {self.config_file}")

        # Load from environment variables
        self._load_from_env()

        # Apply CLI overrides (highest priority)
        if self.cli_overrides:
            logger.debug(f"Applying CLI overrides: {self.cli_overrides}")
            self._merge_config(self.cli_overrides)

        # Expand paths
        self._expand_paths()

        logger.info("Configuration loaded successfully")

    def _get_user_config_path(self) -> Path:
        """Get path to user-level config file."""
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "deepagent" / "config.yaml"
        return Path.home() / ".config" / "deepagent" / "config.yaml"

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML config file."""
        try:
            with open(path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config file {path}: {e}")
            return {}

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "DEEPAGENT_MODEL": ["agent", "model"],
            "DEEPAGENT_WORKSPACE": ["workspace", "path"],
            "DEEPAGENT_LOG_LEVEL": ["agent", "logging", "level"],
            "DEEPAGENT_MAX_RETRIES": ["middleware", "error_recovery", "max_retries"],
            "DEEPAGENT_MEMORY_THRESHOLD": ["middleware", "memory", "threshold"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                # Convert to appropriate type
                final_value: str | int = value
                if env_var in ["DEEPAGENT_MAX_RETRIES", "DEEPAGENT_MEMORY_THRESHOLD"]:
                    final_value = int(value)

                # Set value in config
                self._set_nested(self._config, config_path, final_value)
                logger.debug(f"Set {'.'.join(config_path)} from {env_var}")

    def _merge_config(self, new_config: dict) -> None:
        """Deep merge new config into existing config."""
        self._deep_merge(self._config, new_config)

    def _deep_merge(self, base: dict, update: dict) -> None:
        """Recursively merge update dict into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy an object."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def _set_nested(self, config: dict, path: list[str], value: Any) -> None:
        """Set a nested value in config using a path list."""
        for key in path[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[path[-1]] = value

    def _expand_paths(self) -> None:
        """Expand ~ and environment variables in path configurations."""
        # Expand workspace path
        workspace_path = self._config["workspace"]["path"]
        self._config["workspace"]["path"] = str(Path(workspace_path).expanduser())

        # Expand chat history file
        history_file = self._config["chat"]["history_file"]
        self._config["chat"]["history_file"] = str(Path(history_file).expanduser())

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Dot-separated key path (e.g., "agent.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_section(self, section: str) -> dict:
        """
        Get an entire configuration section.

        Args:
            section: Section name (e.g., "models", "middleware")

        Returns:
            Dictionary containing the section configuration
        """
        return self._config.get(section, {})

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Dot-separated key path (e.g., "agent.model")
            value: Value to set
        """
        keys = key.split(".")
        self._set_nested(self._config, keys, value)

    def to_dict(self) -> dict:
        """Return the entire configuration as a dictionary."""
        return self._deep_copy(self._config)

    def save(self, path: Path | str) -> None:
        """
        Save current configuration to a YAML file.

        Args:
            path: Path to save config file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configuration saved to: {path}")


# Global config instance
_global_config: Config | None = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Global Config instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.

    Args:
        config: Config instance to set as global
    """
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _global_config
    _global_config = None
