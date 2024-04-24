import unittest

from cook import is_file_old

class TestIsFileOld(unittest.TestCase):
    def test_reject_nonint(self):
        """
        Test that it can detect non-integer input
        """
        strings = ["cat", "Roger", "al3x", "3M", "one", "Two"]
        for string in strings:
            result = is_file_old("unused_mains_recipes.json", string)
            self.assertTrue(result)

        