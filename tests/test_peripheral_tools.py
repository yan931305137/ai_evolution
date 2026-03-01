import unittest
from src.tools import Tools

class TestPeripheralToolsRegistration(unittest.TestCase):
    def test_tools_registered(self):
        """Verify that peripheral tools are registered in Tools class"""
        descriptions = Tools.get_tool_descriptions()
        
        # Check for key peripheral tools
        self.assertIn("mouse_move", descriptions)
        self.assertIn("mouse_click", descriptions)
        self.assertIn("type_text", descriptions)
        self.assertIn("open_browser", descriptions)
        
        # Check if methods exist on Tools class
        self.assertTrue(hasattr(Tools, 'mouse_move'))
        self.assertTrue(hasattr(Tools, 'key_press'))
        self.assertTrue(hasattr(Tools, 'open_browser'))

if __name__ == '__main__':
    unittest.main()
