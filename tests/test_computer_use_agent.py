
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
from dataclasses import dataclass

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.computer_use.agent import ComputerUseAgent, Action, Observation, Step
from src.utils.llm import LLMClient

class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        self.last_messages = []

    def generate(self, messages, stream=False, temperature=0.7):
        self.last_messages = messages
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return '{"action": "wait", "params": {"seconds": 1}, "reason": "No more mock responses"}'

class MockVisualPerception:
    def __init__(self):
        self.last_screenshot = "dummy_image_data"
        
    def capture_screen(self):
        return "dummy_image_object"
        
    def screenshot_to_base64(self, screenshot):
        return "base64_string"
        
    def get_screen_size(self):
        return (1920, 1080)

class MockInputController:
    def __init__(self):
        self.actions = []
        
    def get_mouse_position(self):
        return (100, 100)
        
    def click(self, x, y):
        self.actions.append(f"click({x}, {y})")
        
    def type_text(self, text):
        self.actions.append(f"type({text})")
        
    def wait(self, seconds):
        self.actions.append(f"wait({seconds})")

class TestComputerUseAgent(unittest.TestCase):
    
    def setUp(self):
        self.mock_llm = MockLLMClient()
        
        # Patch dependencies
        self.visual_patcher = patch('src.tools.computer_use.agent.VisualPerceptionSystem')
        self.input_patcher = patch('src.tools.computer_use.agent.InputController')
        self.browser_patcher = patch('src.tools.computer_use.agent.SyncBrowserController')
        
        self.MockVisualClass = self.visual_patcher.start()
        self.MockInputClass = self.input_patcher.start()
        self.MockBrowserClass = self.browser_patcher.start()
        
        # Setup mock instances
        self.mock_visual = self.MockVisualClass.return_value
        self.mock_visual.capture_screen.return_value = "dummy_screenshot"
        self.mock_visual.screenshot_to_base64.return_value = "base64_data"
        self.mock_visual.get_screen_size.return_value = (1920, 1080)
        
        self.mock_input = self.MockInputClass.return_value
        self.mock_input.get_mouse_position.return_value = (500, 500)
        
        self.agent = ComputerUseAgent(llm=self.mock_llm, max_steps=5, save_history=False)

    def tearDown(self):
        self.visual_patcher.stop()
        self.input_patcher.stop()
        self.browser_patcher.stop()

    def test_initialization(self):
        self.assertIsInstance(self.agent.llm, MockLLMClient)
        self.assertEqual(self.agent.max_steps, 5)

    def test_observe(self):
        observation = self.agent._observe()
        self.assertEqual(observation.screenshot, "base64_data")
        self.assertEqual(observation.mouse_position, (500, 500))
        self.assertEqual(observation.screen_size, (1920, 1080))

    def test_think_and_act_parsing(self):
        # Mock LLM response
        self.mock_llm.responses = [
            json.dumps({
                "thought": "I need to click the button",
                "action": "click",
                "params": {"x": 100, "y": 200},
                "reason": "Test click"
            })
        ]
        
        observation = Observation(screenshot="data", mouse_position=(0,0))
        action = self.agent._think_and_act("test task", observation, [])
        
        self.assertEqual(action.action_type, "click")
        self.assertEqual(action.params, {"x": 100, "y": 200})
        self.assertEqual(action.reason, "Test click")

    def test_think_and_act_fallback(self):
        # Mock invalid LLM response
        self.mock_llm.responses = ["Invalid JSON"]
        
        observation = Observation(screenshot="data", mouse_position=(0,0))
        action = self.agent._think_and_act("test task", observation, [])
        
        self.assertEqual(action.action_type, "wait")
        self.assertEqual(action.params, {"seconds": 1})

    def test_execute_action(self):
        # Test click
        action = Action(action_type="click", params={"x": 10, "y": 20})
        result = self.agent._execute_action(action)
        self.mock_input.click.assert_called_with(10, 20)
        self.assertIn("点击 (10, 20)", result)
        
        # Test type
        action = Action(action_type="type", params={"text": "hello"})
        result = self.agent._execute_action(action)
        self.mock_input.type_text.assert_called_with("hello")
        
        # Test finish
        action = Action(action_type="finish", params={"answer": "done"})
        result = self.agent._execute_action(action)
        self.assertTrue(self.agent.task_completed)
        self.assertIn("done", result)

    def test_run_loop(self):
        # Simulate a 2-step task: move -> finish
        self.mock_llm.responses = [
            json.dumps({
                "thought": "Move mouse",
                "action": "move",
                "params": {"x": 100, "y": 100},
                "reason": "Step 1"
            }),
            json.dumps({
                "thought": "Done",
                "action": "finish",
                "params": {"answer": "Task Complete"},
                "reason": "Step 2"
            })
        ]
        
        result = self.agent.run("Simple Task")
        
        self.assertEqual(result, "Task Complete")
        self.assertEqual(len(self.agent.steps), 2)
        self.mock_input.move_mouse.assert_called_with(100, 100)
        self.assertTrue(self.agent.task_completed)

if __name__ == '__main__':
    unittest.main()
