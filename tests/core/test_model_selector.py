# tests/core/test_model_selector.py
from langchain_ollama import ChatOllama
import pytest

from deepagent_coder.core.model_selector import ModelSelector


def test_model_selector_initialization():
    """Test model selector creates with default configs"""
    selector = ModelSelector()

    assert selector is not None
    assert len(selector.model_configs) > 0
    assert "main_agent" in selector.model_configs


def test_get_model_returns_chat_ollama():
    """Test getting model returns ChatOllama instance"""
    selector = ModelSelector()
    model = selector.get_model("main_agent")

    assert isinstance(model, ChatOllama)
    assert model.model == selector.model_configs["main_agent"]["model"]


def test_get_model_with_custom_config():
    """Test getting model with overridden config"""
    selector = ModelSelector()
    model = selector.get_model("main_agent", temperature=0.5)

    assert model.temperature == 0.5


def test_model_configs_have_required_fields():
    """Test all model configs have required fields"""
    selector = ModelSelector()

    required_fields = ["model", "temperature", "num_ctx"]

    for role, config in selector.model_configs.items():
        for field in required_fields:
            assert field in config, f"Missing {field} in {role} config"


def test_get_model_with_invalid_role():
    """Test getting model with unknown role raises error"""
    selector = ModelSelector()

    with pytest.raises(ValueError, match="Unknown role"):
        selector.get_model("nonexistent_role")


def test_add_custom_role():
    """Test adding custom role configuration"""
    selector = ModelSelector()

    selector.add_custom_role("custom_agent", "llama2:7b", temperature=0.7, num_ctx=2048)

    assert "custom_agent" in selector.model_configs
    assert selector.model_configs["custom_agent"]["model"] == "llama2:7b"
    assert selector.model_configs["custom_agent"]["temperature"] == 0.7


def test_list_roles():
    """Test listing available roles"""
    selector = ModelSelector()

    roles = selector.list_roles()

    assert isinstance(roles, dict)
    assert "main_agent" in roles
    assert roles["main_agent"] == "qwen2.5:14b"
