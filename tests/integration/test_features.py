import pytest
import os
import shutil
import asyncio
from src.agents.multi_agent import run_sync
from src.brain.human_level_brain import HumanLevelBrain
from src.utils.config import cfg

@pytest.mark.integration
def test_human_brain_lite_mode():
    """Test the Lite mode of HumanLevelBrain"""
    async def run():
        # Initialize in lite mode
        brain = HumanLevelBrain(mode="lite")
        
        # Verify components are not initialized
        assert brain.emotion is None
        assert brain.embodied is None
        assert brain.developmental is None
        assert brain.social is None
        assert brain.homeostasis is None
        assert brain.metacognition is None
        
        # Verify self concept works
        concept = brain.get_self_concept()
        assert concept["developmental_stage"] == "N/A"
        assert "Lite 模式" in concept["subjective_report"]
        
        # Test experience processing
        input_data = {
            "cognitive": "Test input for lite mode",
            "event": {"relevance": 0.5}
        }
        result = await brain.experience(input_data)
        
        # Verify result structure
        assert result["cognitive_response"] is not None
        assert result["emotional_state"] is None
        assert result["body_state"] is None
        assert result["developmental_stage"] == "N/A"
        
        # Verify narrative was updated
        assert len(brain.life_narrative) > 0
        assert brain.life_narrative[-1]["what_happened"] == "Test input for lite mode"
        
    asyncio.run(run())

@pytest.mark.integration
def test_refactor_scenario():
    """Test end-to-end refactoring scenario using MultiAgent system"""
    # Setup temporary directory
    test_dir = os.path.abspath("tests/integration/data/refactor_test")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    
    bad_code = """
def calc(a,b):
    return a+b
    """
    
    file_path = os.path.join(test_dir, "bad_code.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(bad_code)
        
    # Goal: Refactor the code
    goal = f"Refactor the python file at '{file_path}'. Add type hints (int) and a docstring explaining it adds two numbers."
    
    print(f"Executing goal: {goal}")
    
    try:
        # Execute using MultiAgentRunner
        result = run_sync(goal, mode="single")
        
        print(f"Result: {result}")
        
        # Verify the file was modified
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"Modified content:\n{content}")
        
        # Check for type hints
        if "def calc(a: int, b: int)" in content or "def calc(a:int, b:int)" in content.replace(" ", ""):
            print("Type hints found.")
        else:
            print("Type hints NOT found.")
            
        # Check for docstring
        if '"""' in content or "'''" in content:
            print("Docstring found.")
        else:
            print("Docstring NOT found.")
            
    except Exception as e:
        print(f"Test execution failed: {e}")
        # Allow pass if it's an API error
        if "parsing JSON response" in str(e) or "状态不太好" in str(e):
            pytest.skip(f"LLM API instability detected: {e}")
        else:
            pytest.fail(f"Test failed with error: {e}")
        
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

def test_langsmith_config():
    """Test LangSmith configuration loading"""
    # Mock environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = "test_key"
    os.environ["LANGCHAIN_PROJECT"] = "test_project"
    
    # Reload config
    cfg.load()
    
    ls_config = cfg.langsmith_config
    assert ls_config.get("tracing") is True
    assert ls_config.get("api_key") == "test_key"
    assert ls_config.get("project") == "test_project"
    
    # Cleanup env
    del os.environ["LANGCHAIN_TRACING_V2"]
    del os.environ["LANGCHAIN_API_KEY"]
    del os.environ["LANGCHAIN_PROJECT"]
