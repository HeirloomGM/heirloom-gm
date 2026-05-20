import unittest

from heirloom.path_functions.path_functions import convert_to_unix_path, convert_to_wine_path


class PathFunctionsTest(unittest.TestCase):
    def test_convert_to_wine_path_adds_z_drive_and_backslashes(self):
        self.assertEqual(convert_to_wine_path('/home/deck/Games'), 'Z:\\home\\deck\\Games')

    def test_convert_to_wine_path_does_not_duplicate_z_drive(self):
        self.assertEqual(convert_to_wine_path('Z:\\home\\deck\\Games'), 'Z:\\home\\deck\\Games')

    def test_convert_to_unix_path_removes_drive_prefix(self):
        self.assertEqual(convert_to_unix_path('Z:\\home\\deck\\Games'), '/home/deck/Games')


if __name__ == '__main__':
    unittest.main()
