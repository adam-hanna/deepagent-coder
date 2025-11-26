"""
Model Selector - Core infrastructure component for managing model selection.

This module provides centralized model configuration and selection for different
agent roles (main agent, code generator, debugger, summarizer, test writer, refactorer).

Each role has optimized model settings including:
- model: The Ollama model to use
- temperature: Randomness in generation (0.0 = deterministic, 1.0 = creative)
- num_ctx: Context window size in tokens
- num_gpu: Number of GPU layers to use
- timeout: Request timeout in seconds

Example:
    selector = ModelSelector()
    main_model = selector.get_model("main_agent")
    custom_model = selector.get_model("code_generator", temperature=0.5)

    # Add custom role
    selector.add_custom_role("reviewer", "qwen2.5-coder:7b", temperature=0.2)
"""

import logging
from typing import Any

from langchain_ollama import ChatOllama

from deepagent_coder.core.config import Config

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Manages model selection and configuration for different agent roles.

    Provides role-based model configurations with sensible defaults and
    supports custom role definitions. Each role is optimized for its
    specific task (reasoning, generation, debugging, etc.).

    Attributes:
        model_configs: Dictionary mapping role names to their configurations
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize ModelSelector with role configurations from Config.

        Args:
            config: Optional Config instance. If not provided, uses defaults.

        Default roles:
        - main_agent: Primary reasoning and decision-making
        - code_generator: Code generation and implementation
        - debugger: Error analysis and debugging
        - summarizer: Documentation and summarization
        - test_writer: Test generation
        - refactorer: Code refactoring and optimization
        - devops: Deployment and infrastructure automation
        - code_review: Code quality assessment and review
        """
        self.config = config

        # Load model configurations from config or use defaults
        if config:
            self.model_configs: dict[str, dict[str, Any]] = config.get_section("models")
            logger.debug(
                f"ModelSelector initialized from config with {len(self.model_configs)} roles"
            )
        else:
            # Fallback to hard-coded defaults if no config provided
            self.model_configs = {
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
            }
            logger.debug(f"ModelSelector initialized with {len(self.model_configs)} default roles")

    def get_model(self, role: str, **override_params) -> ChatOllama:
        """
        Get a configured ChatOllama model for the specified role.

        Args:
            role: The agent role (e.g., "main_agent", "code_generator")
            **override_params: Optional parameters to override default config
                             (e.g., temperature=0.5, num_ctx=8192)

        Returns:
            ChatOllama: Configured model instance ready for use

        Raises:
            ValueError: If the role is not recognized

        Example:
            model = selector.get_model("main_agent")
            custom_model = selector.get_model("code_generator", temperature=0.5)
        """
        if role not in self.model_configs:
            available_roles = ", ".join(self.model_configs.keys())
            raise ValueError(f"Unknown role: {role}. Available roles: {available_roles}")

        # Get base config for role
        config = self.model_configs[role].copy()

        # Apply any overrides
        config.update(override_params)

        logger.debug(f"Creating model for role '{role}' with config: {config}")

        # Create and return ChatOllama instance
        return ChatOllama(**config)

    def add_custom_role(
        self,
        role_name: str,
        model: str,
        temperature: float = 0.3,
        num_ctx: int = 16384,
        num_gpu: int = 1,
        timeout: int = 300,
    ) -> None:
        """
        Add or update a custom role configuration.

        Args:
            role_name: Name for the custom role
            model: Ollama model to use (e.g., "qwen2.5-coder:7b")
            temperature: Randomness in generation (0.0-1.0)
            num_ctx: Context window size in tokens
            num_gpu: Number of GPU layers to use
            timeout: Request timeout in seconds

        Example:
            selector.add_custom_role(
                "reviewer",
                "qwen2.5-coder:7b",
                temperature=0.2,
                num_ctx=8192
            )
        """
        self.model_configs[role_name] = {
            "model": model,
            "temperature": temperature,
            "num_ctx": num_ctx,
            "num_gpu": num_gpu,
            "timeout": timeout,
        }
        logger.info(f"Added custom role: {role_name} with model {model}")

    def list_roles(self) -> dict[str, str]:
        """
        List all available roles and their associated models.

        Returns:
            Dict[str, str]: Mapping of role names to model names

        Example:
            roles = selector.list_roles()
            # {'main_agent': 'qwen2.5-coder:7b', 'code_generator': 'qwen2.5-coder:7b', ...}
        """
        return {role: config["model"] for role, config in self.model_configs.items()}

    async def preload_models(self) -> None:
        """
        Preload all configured models to warm up Ollama.

        This can be called at startup to ensure faster response times
        for the first request to each model. Each model is initialized
        with a simple test prompt.

        Note:
            This is an async operation that may take several seconds
            depending on the number of models and system resources.
        """
        logger.info("Preloading models for all roles...")
        for role in self.model_configs:
            try:
                model = self.get_model(role)
                # Simple warmup invocation
                await model.ainvoke("Hello")
                logger.debug(f"Preloaded model for role: {role}")
            except Exception as e:
                logger.warning(f"Failed to preload model for role {role}: {e}")
        logger.info("Model preloading complete")


# Global default instance
_default_selector: ModelSelector | None = None


def get_default_selector() -> ModelSelector:
    """
    Get or create the global default ModelSelector instance.

    This provides a convenient singleton pattern for accessing
    model selection throughout the application.

    Returns:
        ModelSelector: The global default selector instance

    Example:
        selector = get_default_selector()
        model = selector.get_model("main_agent")
    """
    global _default_selector
    if _default_selector is None:
        _default_selector = ModelSelector()
        logger.debug("Created default ModelSelector instance")
    return _default_selector
