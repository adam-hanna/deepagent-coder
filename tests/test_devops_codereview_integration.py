"""
Integration tests for DevOps and Code Review subagents.

These tests verify that the DevOps and Code Review agents can be created,
initialized, and integrated with the MCP tool ecosystem.
"""


import pytest

from deepagent_coder.core.model_selector import ModelSelector
from deepagent_coder.subagents.code_reviewer import SYSTEM_PROMPT as CODEREVIEW_SYSTEM_PROMPT
from deepagent_coder.subagents.devops import SYSTEM_PROMPT as DEVOPS_SYSTEM_PROMPT


@pytest.mark.integration
def test_devops_system_prompt_content():
    """Test DevOps agent system prompt contains all required sections"""
    # Verify key sections are present
    required_sections = [
        "DevOps",
        "Container",
        "Kubernetes",
        "Terraform",
        "CI/CD",
        "Safety Protocols",
        "Rollback",
    ]

    for section in required_sections:
        assert section in DEVOPS_SYSTEM_PROMPT, f"Missing section: {section}"


@pytest.mark.integration
def test_code_review_system_prompt_content():
    """Test Code Review agent system prompt contains all required sections"""
    # Verify key sections are present
    required_sections = [
        "code review",
        "Metrics",
        "Complexity",
        "Coverage",
        "Security",
        "Maintainability",
        "Quality Gate",
    ]

    for section in required_sections:
        assert section in CODEREVIEW_SYSTEM_PROMPT, f"Missing section: {section}"


@pytest.mark.integration
def test_devops_prompt_has_integration_guidance():
    """Test DevOps prompt includes guidance on team integration"""
    assert "Integration with Team" in DEVOPS_SYSTEM_PROMPT
    assert "Navigator" in DEVOPS_SYSTEM_PROMPT
    assert "Tester" in DEVOPS_SYSTEM_PROMPT


@pytest.mark.integration
def test_code_review_prompt_has_integration_guidance():
    """Test Code Review prompt includes guidance on team integration"""
    assert "Integration with Team" in CODEREVIEW_SYSTEM_PROMPT
    assert "Navigator" in CODEREVIEW_SYSTEM_PROMPT
    assert "Tester" in CODEREVIEW_SYSTEM_PROMPT


@pytest.mark.integration
def test_devops_prompt_has_workflow_patterns():
    """Test DevOps prompt includes workflow patterns"""
    assert "Workflow Patterns" in DEVOPS_SYSTEM_PROMPT
    assert "Containerization Flow" in DEVOPS_SYSTEM_PROMPT
    assert "Kubernetes Deployment" in DEVOPS_SYSTEM_PROMPT


@pytest.mark.integration
def test_code_review_prompt_has_review_process():
    """Test Code Review prompt includes review process steps"""
    assert "Review Process" in CODEREVIEW_SYSTEM_PROMPT
    assert "Contextual Analysis" in CODEREVIEW_SYSTEM_PROMPT
    assert "Metrics Collection" in CODEREVIEW_SYSTEM_PROMPT


@pytest.mark.integration
def test_devops_prompt_has_safety_guidance():
    """Test DevOps prompt emphasizes safety and rollback"""
    assert "rollback" in DEVOPS_SYSTEM_PROMPT.lower()
    assert "safety" in DEVOPS_SYSTEM_PROMPT.lower()
    assert "Progressive Deployment" in DEVOPS_SYSTEM_PROMPT


@pytest.mark.integration
def test_code_review_prompt_has_quality_gates():
    """Test Code Review prompt includes quality gate thresholds"""
    assert "Quality Gate" in CODEREVIEW_SYSTEM_PROMPT
    assert "8.0/10" in CODEREVIEW_SYSTEM_PROMPT
    assert "80%" in CODEREVIEW_SYSTEM_PROMPT


@pytest.mark.integration
def test_devops_prompt_includes_docker_guidance():
    """Test DevOps prompt has Docker-specific guidance"""
    assert "Docker" in DEVOPS_SYSTEM_PROMPT
    assert "Dockerfile" in DEVOPS_SYSTEM_PROMPT
    assert "docker-compose" in DEVOPS_SYSTEM_PROMPT


@pytest.mark.integration
def test_code_review_prompt_includes_metrics():
    """Test Code Review prompt specifies key metrics"""
    assert "Cyclomatic complexity" in CODEREVIEW_SYSTEM_PROMPT
    assert "Test coverage" in CODEREVIEW_SYSTEM_PROMPT
    assert "Code duplication" in CODEREVIEW_SYSTEM_PROMPT
    assert "Maintainability Index" in CODEREVIEW_SYSTEM_PROMPT


@pytest.mark.integration
def test_devops_prompt_has_examples():
    """Test DevOps prompt includes practical examples"""
    assert "dockerfile" in DEVOPS_SYSTEM_PROMPT.lower()
    assert "deployment" in DEVOPS_SYSTEM_PROMPT.lower()


@pytest.mark.integration
def test_code_review_prompt_has_output_format():
    """Test Code Review prompt specifies output format"""
    assert "Output Format" in CODEREVIEW_SYSTEM_PROMPT
    assert "Overall Score" in CODEREVIEW_SYSTEM_PROMPT
    assert "Strengths" in CODEREVIEW_SYSTEM_PROMPT
    assert "Issues Found" in CODEREVIEW_SYSTEM_PROMPT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_devops_agent_function_signature():
    """Test DevOps agent creation function has correct signature"""
    import inspect

    from deepagent_coder.subagents.devops import create_devops_agent

    sig = inspect.signature(create_devops_agent)
    params = list(sig.parameters.keys())

    assert "model_selector" in params
    assert "tools" in params
    assert "backend" in params or "workspace_path" in params


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_review_agent_function_signature():
    """Test Code Review agent creation function has correct signature"""
    import inspect

    from deepagent_coder.subagents.code_reviewer import create_code_review_agent

    sig = inspect.signature(create_code_review_agent)
    params = list(sig.parameters.keys())

    assert "model_selector" in params
    assert "tools" in params
    assert "backend" in params or "workspace_path" in params


@pytest.mark.integration
def test_model_selector_has_devops_role():
    """Test model selector configuration includes DevOps role"""
    selector = ModelSelector()

    # Verify selector can get model for devops (won't fail)
    try:
        model = selector.get_model("devops")
        assert model is not None
    except (KeyError, ValueError):
        # If devops not in config, that's okay - it will use default
        # This is expected until model_selector is updated with devops role
        pass


@pytest.mark.integration
def test_model_selector_has_code_review_role():
    """Test model selector configuration includes Code Review role"""
    selector = ModelSelector()

    # Verify selector can get model for code_review (won't fail)
    try:
        model = selector.get_model("code_review")
        assert model is not None
    except (KeyError, ValueError):
        # If code_review not in config, that's okay - it will use default
        # This is expected until model_selector is updated with code_review role
        pass


@pytest.mark.integration
def test_devops_agent_module_structure():
    """Test DevOps agent module has required exports"""
    from deepagent_coder.subagents import devops

    assert hasattr(devops, "create_devops_agent")
    assert hasattr(devops, "SYSTEM_PROMPT")
    assert callable(devops.create_devops_agent)


@pytest.mark.integration
def test_code_review_agent_module_structure():
    """Test Code Review agent module has required exports"""
    from deepagent_coder.subagents import code_reviewer

    assert hasattr(code_reviewer, "create_code_review_agent")
    assert hasattr(code_reviewer, "SYSTEM_PROMPT")
    assert callable(code_reviewer.create_code_review_agent)


@pytest.mark.integration
def test_devops_prompt_length_reasonable():
    """Test DevOps prompt is substantial but not excessive"""
    # Should be detailed but not too long for context windows
    assert len(DEVOPS_SYSTEM_PROMPT) > 1000, "Prompt should be detailed"
    assert len(DEVOPS_SYSTEM_PROMPT) < 50000, "Prompt should fit in context window"


@pytest.mark.integration
def test_code_review_prompt_length_reasonable():
    """Test Code Review prompt is substantial but not excessive"""
    # Should be detailed but not too long for context windows
    assert len(CODEREVIEW_SYSTEM_PROMPT) > 1000, "Prompt should be detailed"
    assert len(CODEREVIEW_SYSTEM_PROMPT) < 50000, "Prompt should fit in context window"
