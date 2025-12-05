import unittest
import logging
from logging import Logger

from SQLHelpersAJM import _SharedLogger


class DummyShared(_SharedLogger):
    pass


class TestSharedLogger(unittest.TestCase):
    def test_validate_bcl_accepts_name_and_level(self):
        self.assertEqual(DummyShared._validate_bcl(basic_config_level='INFO'), 'INFO')
        self.assertEqual(DummyShared._validate_bcl(basic_config_level=logging.INFO), logging.INFO)
        self.assertFalse(DummyShared._validate_bcl(basic_config_level='NOTALEVEL'))

    def test_setup_logger_uses_existing_and_skip_basic_config(self):
        lg = logging.getLogger('testlogger')
        d = DummyShared()
        out = d._setup_logger(logger=lg, skip_basic_config=True)
        self.assertIs(out, lg)
        # Ensure no handlers added implicitly when skip_basic_config
        self.assertTrue(isinstance(out, Logger))

    def test_setup_logger_basic_config_once(self):
        # First call should add handlers via basicConfig
        d = DummyShared()
        lg = d._setup_logger(logger_name_to_get='unique_logger_name_for_test')
        self.assertTrue(isinstance(lg, Logger))
        # Calling again should not duplicate handlers
        count1 = len(lg.handlers)
        lg2 = d._setup_logger(logger=lg)
        self.assertEqual(len(lg2.handlers), count1)


if __name__ == '__main__':
    unittest.main()