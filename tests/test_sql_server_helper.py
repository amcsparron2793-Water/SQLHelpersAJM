import unittest
import sys
from unittest import mock

# Create a dummy pyodbc module before import
class DummyPyodbcModule:
    def __init__(self):
        self._calls = []

    def connect(self, connection_string):
        self._calls.append(connection_string)
        return DummyConnection()


class DummyConnection:
    def __init__(self):
        self._closed = False

    def cursor(self):
        return DummyCursor()

    def close(self):
        self._closed = True


class DummyCursor:
    description = [('col',)]

    def execute(self, sql):
        return None

    def fetchall(self):
        return []


sys.modules.setdefault('pyodbc', DummyPyodbcModule())

from SQLHelpersAJM.helpers.sql_server import SQLServerHelper, SQLServerHelperTT, _SQLServerTableTracker  # noqa: E402
from SQLHelpersAJM.backend.errors import NoTrackedTablesError  # noqa: E402


class TestSQLServerHelper(unittest.TestCase):
    def test_connection_string_and_connect_called(self):
        # Ensure pyodbc mock is in place
        import pyodbc
        helper = SQLServerHelper(server='srv', database='db', driver='{SQL Server}', instance='SQLEXPRESS', trusted_connection='yes', username='u', password='p')
        cs = helper.connection_string
        self.assertIn('driver={SQL Server}', cs)
        self.assertIn('server=srv\\SQLEXPRESS', cs)
        helper.get_connection_and_cursor()
        # Verify our mock got a connect call
        self.assertTrue(len(pyodbc._calls) >= 1)
        self.assertIn(cs, pyodbc._calls[-1])

    def test_tt_guard_and_success(self):
        # Guard triggers when TABLES_TO_TRACK is magic default
        class BadTT(SQLServerHelperTT):
            TABLES_TO_TRACK = [SQLServerHelperTT._MAGIC_IGNORE_STRING]
        with self.assertRaises(NoTrackedTablesError):
            BadTT(server='srv', database='db', driver='{SQL Server}')

        # Success path when tables provided
        class GoodTT(SQLServerHelperTT):
            TABLES_TO_TRACK = ['t']
        g = GoodTT(server='srv', database='db', driver='{SQL Server}')
        self.assertIsInstance(g, SQLServerHelperTT)


if __name__ == '__main__':
    unittest.main()