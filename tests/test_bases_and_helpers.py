import unittest
import types
from pathlib import Path
from unittest import mock

from SQLHelpersAJM.helpers.bases import BaseSQLHelper, BaseConnectionAttributes, BaseCreateTriggers
from SQLHelpersAJM.backend import UserPassInput
from SQLHelpersAJM.backend.errors import NoCursorInitializedError, NoResultsToConvertError, MissingRequiredClassAttribute, NoTrackedTablesError
from SQLHelpersAJM.helpers.sqlite3_helper import SQLite3Helper, SQLite3HelperTT


class DummyConnection:
    def __init__(self):
        self._closed = False
        self._commits = 0

    def cursor(self):
        return DummyCursor()

    def close(self):
        self._closed = True

    def commit(self):
        self._commits += 1


class DummyCursor:
    def __init__(self):
        self.description = [('id',), ('name',)]
        self._executed = []
        self._data = [(1, 'a'), (2, 'b')]
        self._closed = False

    def execute(self, sql):
        self._executed.append(sql)

    def fetchall(self):
        return list(self._data)

    def close(self):
        self._closed = True


class SQLHelperStub(BaseSQLHelper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dummy = DummyConnection()

    def _connect(self):
        return self._dummy


class TestBaseSQLHelper(unittest.TestCase):
    def test_cursor_check_raises_without_cursor(self):
        h = SQLHelperStub()
        with self.assertRaises(NoCursorInitializedError):
            h.cursor_check()

    def test_get_connection_and_cursor_reuse_and_force_new(self):
        h = SQLHelperStub()
        cxn1, cur1 = h.get_connection_and_cursor()
        cxn2, cur2 = h.get_connection_and_cursor()
        self.assertIs(cxn1, cxn2)
        self.assertIs(cur1, cur2)
        cxn3, cur3 = h.get_connection_and_cursor(force_new=True)
        self.assertIsNot(cxn1, cxn3)
        self.assertIsNot(cur1, cur3)

    def test_normalize_and_convert_results(self):
        h = SQLHelperStub()
        h.get_connection_and_cursor()
        h.query("select 1")
        # results list of tuples
        self.assertIsInstance(h.query_results, list)
        self.assertIsInstance(h.query_results[0], tuple)
        # conversion to list of dicts
        out = h.list_dict_results
        self.assertEqual(out, [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}])

    def test_convert_raises_without_column_names(self):
        h = SQLHelperStub()
        h.get_connection_and_cursor()
        # break description
        h._cursor.description = None
        with self.assertRaises(NoResultsToConvertError):
            h._ConvertToFinalListDict([(1, 'a')])


class ConnAttrStub(BaseConnectionAttributes):
    _TRUSTED_CONNECTION_DEFAULT = 'yes'
    _DRIVER_DEFAULT = '{Driver}'
    _INSTANCE_DEFAULT = 'SQLEXPRESS'

    def _connect(self):
        return DummyConnection()


class TestBaseConnectionAttributes(unittest.TestCase):
    @mock.patch.object(UserPassInput, 'get_user_pass', side_effect=['user', 'pass'])
    def test_connection_string_builds(self, _):
        h = ConnAttrStub(server='srv', database='db')
        cs = h.connection_string
        self.assertIn('driver={Driver}', cs)
        self.assertIn('server=srv\\SQLEXPRESS', cs)
        self.assertIn('database=db', cs)
        self.assertIn('UID=user', cs)
        self.assertIn('PWD=pass', cs)
        self.assertIn('trusted_connection=yes', cs)

    def test_connection_string_to_attributes_parses_instance(self):
        s = 'driver={Driver};server=srv\\INST;database=db;UID=u;PWD=p;trusted_connection=no'
        out = ConnAttrStub._connection_string_to_attributes(s, ';', '=')
        self.assertEqual(out['server'], 'srv')
        self.assertEqual(out['instance'], 'INST')


class CreateTriggersStub(BaseCreateTriggers):
    TABLES_TO_TRACK = ['x']
    AUDIT_LOG_CREATE_TABLE = 'CREATE TABLE audit_log(id int);'
    AUDIT_LOG_CREATED_CHECK = 'select 1;'
    HAS_TRIGGER_CHECK = 'select 1;'
    GET_COLUMN_NAMES = 'select 1;'
    INSERT_TRIGGER = 'i'
    UPDATE_TRIGGER = 'u'
    DELETE_TRIGGER = 'd'

    def __init__(self, **kwargs):
        # Supply required fields used by BaseCreateTriggers
        self._connection = DummyConnection()
        self._cursor = self._connection.cursor()
        super().__init__(**kwargs)

    def _connect(self):
        return self._connection

    def Query(self, sql_string: str, **kwargs):
        return None

    @property
    def query_results(self):
        return []

    def GetConnectionAndCursor(self, **kwargs):
        return self._connection, self._cursor

    def get_connection_and_cursor(self, **kwargs):
        return self._connection, self._cursor


class TestBaseCreateTriggers(unittest.TestCase):
    def test_required_class_attributes_present(self):
        s = CreateTriggersStub()
        self.assertTrue(s.has_required_class_attributes)
        self.assertTrue(len(s.required_class_attributes) >= 7)
        self.assertIsInstance(s.class_attr_list, dict)

    def test_missing_tracked_tables_on_non_tracker_raises(self):
        # Create subclass with TABLES_TO_TRACK magic default and name not matching tracker/helper base
        with self.assertRaises(NoTrackedTablesError):
            class NotTracker(CreateTriggersStub):
                TABLES_TO_TRACK = [BaseCreateTriggers._MAGIC_IGNORE_STRING]
                __name__ = 'NotTracker'
                pass


class TestSQLite3Helpers(unittest.TestCase):
    def setUp(self):
        self.tmp = Path('tests_tmp_sqlite.db')
        try:
            self.tmp.unlink()
        except FileNotFoundError:
            pass

    def tearDown(self):
        try:
            self.tmp.unlink()
        except Exception:
            pass

    def test_sqlite_basic_query_and_foreign_keys(self):
        sql = SQLite3Helper(self.tmp)
        cxn, cur = sql.get_connection_and_cursor()
        cur.execute('create table t(id integer primary key, name text);')
        cur.execute("insert into t(name) values('a'),('b');")
        cxn.commit()
        sql.Query('select * from t')
        self.assertEqual(sql.list_dict_results, [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}])
        sql.Query('pragma foreign_keys')
        self.assertIn(sql.query_results, (1, ['1'], [('1',)]))

    def test_sqlite_helper_tt_guard(self):
        with self.assertRaises(NoTrackedTablesError):
            # Temporarily ensure default to trigger guard
            class BadTT(SQLite3HelperTT):
                TABLES_TO_TRACK = [BaseCreateTriggers._MAGIC_IGNORE_STRING]
                pass
            BadTT(self.tmp)


if __name__ == '__main__':
    unittest.main()