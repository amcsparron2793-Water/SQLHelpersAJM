import unittest

from SQLHelpersAJM.backend import errors, meta


class TestBackendErrors(unittest.TestCase):
    def test_missing_required_class_attribute_default_message(self):
        e = errors.MissingRequiredClassAttribute()
        self.assertIn('Missing at least one required class attribute', str(e))

    def test_no_tracked_tables_error_formats_class_name(self):
        e = errors.NoTrackedTablesError(class_name='MyClass')
        self.assertIn('MyClass', str(e))
        self.assertIn('No tables have been specified to track', str(e))

    def test_no_cursor_initialized_error_message(self):
        e = errors.NoCursorInitializedError()
        self.assertIn('Cursor has not been initialized yet', str(e))

    def test_no_connection_initialized_error_message(self):
        e = errors.NoConnectionInitializedError()
        self.assertIn('Connection has not been initialized yet', str(e))

    def test_no_results_to_convert_error_message(self):
        e = errors.NoResultsToConvertError()
        self.assertIn('A query has not been executed', str(e))

    def test_invalid_input_mode_message(self):
        e = errors.InvalidInputMode()
        self.assertIn('Invalid input mode specified', str(e))


class StubAllUppercase:
    TABLES_TO_TRACK = ['t']
    AUDIT_LOG_CREATE_TABLE = 'CREATE TABLE t(x int);'
    AUDIT_LOG_CREATED_CHECK = 'select 1;'
    HAS_TRIGGER_CHECK = 'select 1;'
    GET_COLUMN_NAMES = 'select 1;'
    INSERT_TRIGGER = 'trig'
    UPDATE_TRIGGER = 'trig'
    DELETE_TRIGGER = 'trig'


class StubMissingSome:
    TABLES_TO_TRACK = []  # invalid (empty)
    AUDIT_LOG_CREATE_TABLE = None  # invalid


class TestABCCreateTriggers(unittest.TestCase):
    def test_metaclass_validation_success(self):
        # Should not raise
        class Good(StubAllUppercase, metaclass=meta.ABCCreateTriggers):
            pass
        self.assertTrue(hasattr(Good, '__mro__'))

    def test_metaclass_validation_failure_raises(self):
        with self.assertRaises(TypeError):
            class Bad(StubMissingSome, metaclass=meta.ABCCreateTriggers):
                pass

    def test_postgres_metaclass_requires_pg_specific_attributes(self):
        # For ABCPostgresCreateTriggers, inherit from a base that provides both sets
        class PgBase(StubAllUppercase):
            LOG_AFTER_INSERT_FUNC = 'f1'
            LOG_AFTER_UPDATE_FUNC = 'f2'
            LOG_AFTER_DELETE_FUNC = 'f3'
            FUNC_EXISTS_CHECK = 'q'
            VALID_SCHEMA_CHOICES_QUERY = 'q2'
        # Should be okay as all required uppercase attributes are present
        class GoodPg(PgBase, metaclass=meta.ABCPostgresCreateTriggers):
            pass
        self.assertTrue(hasattr(GoodPg, '__mro__'))


if __name__ == '__main__':
    unittest.main()