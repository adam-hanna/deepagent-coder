"""Tests for configuration module"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from deepagent_coder.core.config import Config, get_config, reset_config, set_config


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test config files"""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """Return a sample configuration dict"""
    return {
        "workspace": {"path": "/tmp/test_workspace"},
        "agent": {"model": "custom-model:latest", "max_iterations": 5},
        "models": {"main_agent": {"model": "test-model", "temperature": 0.5}},
        "middleware": {"memory": {"enabled": False}},
    }


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global config before and after each test"""
    reset_config()
    yield
    reset_config()


class TestConfigDefaults:
    """Test default configuration values"""

    def test_default_config_values(self):
        """Test that default configuration has expected values"""
        config = Config()

        assert config.get("agent.model") == "qwen2.5:14b"
        assert config.get("agent.max_iterations") == 10
        # Path is expanded, so check that it ends with the expected path
        assert config.get("workspace.path").endswith("/.deepagents/workspace")
        assert config.get("middleware.memory.threshold") == 6000
        assert config.get("middleware.git_safety.enforce") is False

    def test_default_model_configs(self):
        """Test that default model configurations are present"""
        config = Config()

        models = config.get_section("models")
        assert "main_agent" in models
        assert "code_generator" in models
        assert "debugger" in models

        main_agent = models["main_agent"]
        assert main_agent["model"] == "qwen2.5:14b"
        assert main_agent["temperature"] == 0.3
        assert main_agent["num_ctx"] == 32768

    def test_get_nonexistent_key_returns_default(self):
        """Test that getting a nonexistent key returns the default value"""
        config = Config()

        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"


class TestConfigFileLoading:
    """Test loading configuration from files"""

    def test_load_from_config_file(self, temp_config_dir, sample_config):
        """Test loading configuration from a specified file"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        config = Config(config_file=config_file)

        assert config.get("workspace.path") == "/tmp/test_workspace"
        assert config.get("agent.model") == "custom-model:latest"
        assert config.get("agent.max_iterations") == 5

    def test_load_from_project_config(self, temp_config_dir, sample_config, monkeypatch):
        """Test loading from project-level config (.deepagent.yaml)"""
        # Create .deepagent.yaml in "current directory"
        project_config = Path(".deepagent.yaml")
        with open(project_config, "w") as f:
            yaml.dump(sample_config, f)

        try:
            config = Config()
            assert config.get("agent.model") == "custom-model:latest"
        finally:
            # Clean up
            project_config.unlink()

    def test_nonexistent_config_file(self, temp_config_dir):
        """Test that nonexistent config file falls back to defaults"""
        nonexistent = temp_config_dir / "nonexistent.yaml"
        config = Config(config_file=nonexistent)

        # Should still have defaults
        assert config.get("agent.model") == "qwen2.5:14b"

    def test_invalid_yaml_file(self, temp_config_dir):
        """Test that invalid YAML file falls back to defaults"""
        invalid_config = temp_config_dir / "invalid.yaml"
        with open(invalid_config, "w") as f:
            f.write("invalid: yaml: content: [")

        config = Config(config_file=invalid_config)

        # Should still have defaults
        assert config.get("agent.model") == "qwen2.5:14b"


class TestConfigMerging:
    """Test configuration merging and priority"""

    def test_cli_overrides_take_precedence(self, temp_config_dir, sample_config):
        """Test that CLI overrides have highest priority"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        cli_overrides = {"agent": {"model": "cli-model:latest"}}
        config = Config(config_file=config_file, cli_overrides=cli_overrides)

        assert config.get("agent.model") == "cli-model:latest"  # CLI override wins
        assert config.get("agent.max_iterations") == 5  # From file

    def test_deep_merge_preserves_nested_values(self, temp_config_dir):
        """Test that deep merge preserves nested values"""
        config_file = temp_config_dir / "config.yaml"
        partial_config = {
            "models": {
                "main_agent": {
                    "temperature": 0.8,  # Override one field
                }
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(partial_config, f)

        config = Config(config_file=config_file)

        # Temperature should be overridden
        assert config.get("models.main_agent.temperature") == 0.8
        # Other fields should still have defaults
        assert config.get("models.main_agent.model") == "qwen2.5:14b"
        assert config.get("models.main_agent.num_ctx") == 32768


class TestEnvironmentVariables:
    """Test environment variable loading"""

    def test_load_from_environment_variables(self, monkeypatch):
        """Test loading configuration from environment variables"""
        monkeypatch.setenv("DEEPAGENT_MODEL", "env-model:latest")
        monkeypatch.setenv("DEEPAGENT_WORKSPACE", "/tmp/env_workspace")
        monkeypatch.setenv("DEEPAGENT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEEPAGENT_MAX_RETRIES", "5")
        monkeypatch.setenv("DEEPAGENT_MEMORY_THRESHOLD", "8000")

        config = Config()

        assert config.get("agent.model") == "env-model:latest"
        assert config.get("workspace.path") == "/tmp/env_workspace"
        assert config.get("agent.logging.level") == "DEBUG"
        assert config.get("middleware.error_recovery.max_retries") == 5
        assert config.get("middleware.memory.threshold") == 8000

    def test_env_vars_override_file(self, temp_config_dir, sample_config, monkeypatch):
        """Test that environment variables override config file"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        monkeypatch.setenv("DEEPAGENT_MODEL", "env-model:latest")

        config = Config(config_file=config_file)

        assert config.get("agent.model") == "env-model:latest"  # Env var wins


class TestConfigMethods:
    """Test configuration methods"""

    def test_get_method(self):
        """Test get method with dot notation"""
        config = Config()

        assert config.get("agent.model") is not None
        assert config.get("models.main_agent.temperature") == 0.3
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_section_method(self):
        """Test get_section method"""
        config = Config()

        models = config.get_section("models")
        assert isinstance(models, dict)
        assert "main_agent" in models
        assert "code_generator" in models

        middleware = config.get_section("middleware")
        assert isinstance(middleware, dict)
        assert "memory" in middleware

    def test_set_method(self):
        """Test set method with dot notation"""
        config = Config()

        config.set("agent.model", "new-model:latest")
        assert config.get("agent.model") == "new-model:latest"

        config.set("custom.nested.key", "value")
        assert config.get("custom.nested.key") == "value"

    def test_to_dict_method(self):
        """Test to_dict method"""
        config = Config()

        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "agent" in config_dict
        assert "models" in config_dict
        assert "workspace" in config_dict

        # Should be a deep copy
        config_dict["agent"]["model"] = "modified"
        assert config.get("agent.model") != "modified"

    def test_save_method(self, temp_config_dir):
        """Test save method"""
        config = Config()
        config.set("agent.model", "saved-model:latest")

        save_path = temp_config_dir / "saved_config.yaml"
        config.save(save_path)

        assert save_path.exists()

        # Load and verify
        with open(save_path) as f:
            loaded = yaml.safe_load(f)

        assert loaded["agent"]["model"] == "saved-model:latest"


class TestPathExpansion:
    """Test path expansion"""

    def test_workspace_path_expansion(self, temp_config_dir):
        """Test that ~/ in paths is expanded"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"workspace": {"path": "~/my_workspace"}}, f)

        config = Config(config_file=config_file)

        workspace_path = config.get("workspace.path")
        assert "~" not in workspace_path
        assert workspace_path.startswith(str(Path.home()))

    def test_history_file_expansion(self, temp_config_dir):
        """Test that ~/ in history file path is expanded"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"chat": {"history_file": "~/.my_history"}}, f)

        config = Config(config_file=config_file)

        history_file = config.get("chat.history_file")
        assert "~" not in history_file
        assert history_file.startswith(str(Path.home()))


class TestGlobalConfig:
    """Test global configuration singleton"""

    def test_get_config_returns_singleton(self):
        """Test that get_config returns a singleton instance"""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_set_config_updates_singleton(self):
        """Test that set_config updates the global instance"""
        custom_config = Config()
        custom_config.set("agent.model", "custom-model")

        set_config(custom_config)

        retrieved_config = get_config()
        assert retrieved_config.get("agent.model") == "custom-model"

    def test_reset_config_clears_singleton(self):
        """Test that reset_config clears the global instance"""
        config1 = get_config()
        reset_config()
        config2 = get_config()

        assert config1 is not config2


class TestConfigIntegration:
    """Integration tests for configuration"""

    def test_full_config_priority_chain(self, temp_config_dir, sample_config, monkeypatch):
        """Test complete priority chain: defaults < file < env < CLI"""
        # Setup config file
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Setup environment variable
        monkeypatch.setenv("DEEPAGENT_MAX_RETRIES", "7")

        # Setup CLI override
        cli_overrides = {"agent": {"model": "cli-override:latest"}}

        config = Config(config_file=config_file, cli_overrides=cli_overrides)

        # Check priority:
        # - agent.model: CLI override wins
        assert config.get("agent.model") == "cli-override:latest"

        # - max_retries: env var wins
        assert config.get("middleware.error_recovery.max_retries") == 7

        # - max_iterations: file wins
        assert config.get("agent.max_iterations") == 5

        # - git_safety.enforce: default wins (not in file or env)
        assert config.get("middleware.git_safety.enforce") is False

    def test_partial_config_with_defaults(self, temp_config_dir):
        """Test that partial config file merges with defaults"""
        minimal_config = {"agent": {"model": "minimal-model"}}

        config_file = temp_config_dir / "minimal.yaml"
        with open(config_file, "w") as f:
            yaml.dump(minimal_config, f)

        config = Config(config_file=config_file)

        # Custom value
        assert config.get("agent.model") == "minimal-model"

        # Default values should still be present
        assert config.get("agent.max_iterations") == 10
        assert config.get("middleware.memory.threshold") == 6000
        assert config.get("models.main_agent.temperature") == 0.3
