import unittest
import sys

# Provide a dummy psycopg module before imports
class DummyPsycopg:
    def __init__(self):
        self._calls = []

    def connect(self, **kwargs):
        self._calls.append(kwargs)
        return DummyPgConnection()


class DummyPgConnection:
    def __init__(self):
        self._closed = False

    def cursor(self):
        return DummyPgCursor()

    def close(self):
        self._closed = True


class DummyPgCursor:
    description = [('col',)]
    def execute(self, sql):
        return None
    def fetchall(self):
        return []


sys.modules.setdefault('psycopg', DummyPsycopg())

from SQLHelpersAJM.helpers.postgres import PostgresHelper, PostgresHelperTT  # noqa: E402
from SQLHelpersAJM.backend.errors import NoTrackedTablesError  # noqa: E402


class TestPostgresHelper(unittest.TestCase):
    def test_initialize_and_query_schema_injection(self):
        import psycopg
        h = PostgresHelper(server='localhost', database='db', username='u', password='p')
        # valid_schema_choices property will try to query; but our cursor returns empty; that's fine.
        # ensure connect was called during initialize_schema_choices
        self.assertTrue(len(psycopg._calls) >= 1)
        # Test _add_schema_to_query behavior
        h._schema_choice = 'public'
        out = h._add_schema_to_query('select * from things')
        self.assertIn('public.things', out)
        # when schema already present, stays same
        out2 = h._add_schema_to_query('select * from public.things')
        self.assertEqual(out2, 'select * from public.things')

    def test_tt_guard_and_success(self):
        class BadTT(PostgresHelperTT):
            TABLES_TO_TRACK = [PostgresHelperTT._MAGIC_IGNORE_STRING]
        with self.assertRaises(NoTrackedTablesError):
            BadTT(server='localhost', database='db')

        class GoodTT(PostgresHelperTT):
            TABLES_TO_TRACK = ['t']
        g = GoodTT(server='localhost', database='db')
        self.assertIsInstance(g, PostgresHelperTT)


if __name__ == '__main__':
    unittest.main()