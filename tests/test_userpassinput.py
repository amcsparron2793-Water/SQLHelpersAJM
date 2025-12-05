import unittest
from unittest import mock

from SQLHelpersAJM.backend import UserPassInput
from SQLHelpersAJM.backend.errors import InvalidInputMode


class TestUserPassInput(unittest.TestCase):
    @mock.patch('builtins.input', return_value='theuser')
    def test_get_user_when_not_trusted_and_no_username(self, _):
        user = UserPassInput.get_user_pass(database='db', trusted_connection='no')
        self.assertEqual(user, 'theuser')

    @mock.patch('getpass.getpass', return_value='thepass')
    def test_get_pass_when_not_trusted_and_has_username(self, _):
        pwd = UserPassInput.get_user_pass(username='theuser', trusted_connection='no')
        self.assertEqual(pwd, 'thepass')

    @mock.patch('getpass.getpass', return_value='thepass')
    def test_force_mode_password_ignores_other_kwargs(self, _):
        pwd = UserPassInput.get_user_pass(mode='password', username='ignored', database='ignored')
        self.assertEqual(pwd, 'thepass')

    def test_invalid_mode_raises(self):
        with self.assertRaises(InvalidInputMode):
            UserPassInput._get_user_or_pass('notamode')


if __name__ == '__main__':
    unittest.main()