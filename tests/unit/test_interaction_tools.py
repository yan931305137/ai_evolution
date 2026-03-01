import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock src.storage.memory to prevent model download during import
sys.modules['src.storage.memory'] = MagicMock()
sys.modules['src.storage.memory'].memory = MagicMock()

from src.tools.interaction_tools import ask_user

class TestInteractionTools(unittest.TestCase):
    
    @patch('builtins.input', return_value='yes')
    @patch('builtins.print')
    def test_ask_user_simple(self, mock_print, mock_input):
        """Test simple question asking without options."""
        result = ask_user("Is this correct?")
        
        # Verify print was called with the question
        mock_print.assert_any_call("\n[Agent Question] Is this correct?")
        
        # Verify result matches input
        self.assertEqual(result, 'yes')
        
    @patch('builtins.input', return_value='option1')
    @patch('builtins.print')
    def test_ask_user_with_options(self, mock_print, mock_input):
        """Test question with options displayed."""
        options = ['option1', 'option2']
        result = ask_user("Choose one:", options=options)
        
        # Verify options were printed
        mock_print.assert_any_call("Options: option1, option2")
        
        self.assertEqual(result, 'option1')
        
    @patch('builtins.input', side_effect=EOFError)
    @patch('builtins.print')
    def test_ask_user_eof(self, mock_print, mock_input):
        """Test handling of EOFError (e.g., in non-interactive environments)."""
        result = ask_user("Question?")
        
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
