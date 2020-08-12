"""Module for testing the natcap.invest.utils module.."""
import codecs
import unittest
import os
import tempfile
import shutil
import logging
import threading
import warnings
import re
import glob
import textwrap

import numpy
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from shapely.geometry import Polygon
from shapely.geometry import Point

import pygeoprocessing


class SuffixUtilsTests(unittest.TestCase):
    """Tests for natcap.invest.utils.make_suffix_string."""

    def test_suffix_string(self):
        """Utils: test suffix_string."""
        from natcap.invest import utils

        args = {'foo': 'bar', 'file_suffix': 'suff'}
        suffix = utils.make_suffix_string(args, 'file_suffix')
        self.assertEqual(suffix, '_suff')

    def test_suffix_string_underscore(self):
        """Utils: test suffix_string underscore."""
        from natcap.invest import utils

        args = {'foo': 'bar', 'file_suffix': '_suff'}
        suffix = utils.make_suffix_string(args, 'file_suffix')
        self.assertEqual(suffix, '_suff')

    def test_suffix_string_empty(self):
        """Utils: test empty suffix_string."""
        from natcap.invest import utils

        args = {'foo': 'bar', 'file_suffix': ''}
        suffix = utils.make_suffix_string(args, 'file_suffix')
        self.assertEqual(suffix, '')

    def test_suffix_string_no_entry(self):
        """Utils: test no suffix entry in args."""
        from natcap.invest import utils

        args = {'foo': 'bar'}
        suffix = utils.make_suffix_string(args, 'file_suffix')
        self.assertEqual(suffix, '')


class FileRegistryUtilsTests(unittest.TestCase):
    """Tests for natcap.invest.utils.file_registry."""

    def test_build_file_registry(self):
        """Utils: test build_file_registry on simple case."""
        from natcap.invest import utils

        base_dict = {'foo': 'bar', 'baz': '/bart/bam.txt'}
        file_registry = utils.build_file_registry([(base_dict, '')], '')

        self.assertEqual(
            FileRegistryUtilsTests._norm_dict(base_dict),
            FileRegistryUtilsTests._norm_dict(file_registry))

    def test_build_file_registry_suffix(self):
        """Utils: test build_file_registry on suffix."""
        from natcap.invest import utils

        base_dict = {'foo': 'bar', 'baz': '/bart/bam.txt'}
        file_registry = utils.build_file_registry([
            (base_dict, '')], '_suff')
        expected_dict = {
            'foo': 'bar_suff',
            'baz': '/bart/bam_suff.txt'
        }

        self.assertEqual(
            FileRegistryUtilsTests._norm_dict(expected_dict),
            FileRegistryUtilsTests._norm_dict(file_registry))

    def test_build_file_registry_list_suffix(self):
        """Utils: test build_file_registry on list of files w/ suffix."""
        from natcap.invest import utils

        base_dict = {
            'foo': ['bar', '/bart/bam.txt']
        }
        file_registry = utils.build_file_registry([
            (base_dict, '')], '_suff')
        expected_dict = {
            'foo': ['bar_suff', '/bart/bam_suff.txt']
        }

        self.assertEqual(
            FileRegistryUtilsTests._norm_dict(expected_dict),
            FileRegistryUtilsTests._norm_dict(file_registry))

    def test_build_file_registry_path(self):
        """Utils: test build_file_registry on path."""
        from natcap.invest import utils

        base_dict = {
            'foo': 'bar',
            'baz': '/bart/bam.txt',
            'jab': 'jim'
        }
        file_registry = utils.build_file_registry([
            (base_dict, 'newpath')], '')
        expected_dict = {
            'foo': 'newpath/bar',
            'jab': 'newpath/jim',
            'baz': '/bart/bam.txt',
        }

        self.assertEqual(
            FileRegistryUtilsTests._norm_dict(expected_dict),
            FileRegistryUtilsTests._norm_dict(file_registry))

    def test_build_file_registry_duppath(self):
        """Utils: test build_file_registry ValueError on duplicate paths."""
        from natcap.invest import utils

        base_dict = {
            'foo': 'bar',
            'jab': 'bar'
        }
        with self.assertRaises(ValueError):
            _ = utils.build_file_registry([
                (base_dict, 'newpath')], '')

    def test_build_file_registry_dupkeys(self):
        """Utils: test build_file_registry ValueError on duplicate keys."""
        from natcap.invest import utils

        base_dict1 = {
            'foo': 'bar',
        }
        base_dict2 = {
            'foo': 'bar2',
        }
        with self.assertRaises(ValueError):
            _ = utils.build_file_registry([
                (base_dict1, ''), (base_dict2, '')], '')

    def test_build_file_registry_invalid_value(self):
        """Utils: test build_file_registry with invalid path type."""
        from natcap.invest import utils

        base_dict = {
            'foo': 'bar',
            'baz': None
        }
        with self.assertRaises(ValueError):
            _ = utils.build_file_registry([(base_dict, 'somepath')], '')

    @staticmethod
    def _norm_dict(path_dict):
        """Take a dictionary of paths and normalize the paths."""
        result_dict = {}
        for key, path in path_dict.items():
            if isinstance(path, str):
                result_dict[key] = os.path.normpath(path)
            elif isinstance(path, list):
                result_dict[key] = [
                    os.path.normpath(list_path) for list_path in path]
            else:
                raise ValueError("Unexpected path value: %s", path)
        return result_dict


class ExponentialDecayUtilsTests(unittest.TestCase):
    """Tests for natcap.invest.utils.exponential_decay_kernel_raster."""

    _REGRESSION_PATH = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'invest-test-data',
        'exp_decay_kernel')

    def setUp(self):
        """Setup workspace."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)

    def test_exp_decay_kernel_raster(self):
        """Utils: test exponential_decay_kernel_raster."""
        from natcap.invest import utils
        expected_distance = 100  # 10 pixels
        kernel_filepath = os.path.join(self.workspace_dir, 'kernel_100.tif')
        utils.exponential_decay_kernel_raster(
            expected_distance, kernel_filepath)

        model_array = pygeoprocessing.raster_to_numpy_array(
            kernel_filepath)
        reg_array = pygeoprocessing.raster_to_numpy_array(
            os.path.join(
                ExponentialDecayUtilsTests._REGRESSION_PATH,
                'kernel_100.tif'))
        numpy.testing.assert_allclose(model_array, reg_array, atol=1e-6)


class SandboxTempdirTests(unittest.TestCase):
    """Test Sandbox Tempdir."""
    def setUp(self):
        """Setup workspace."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)

    def test_sandbox_manager(self):
        """Test sandbox manager."""
        from natcap.invest import utils

        with utils.sandbox_tempdir(suffix='foo',
                                   prefix='bar',
                                   dir=self.workspace_dir) as new_dir:
            self.assertTrue(new_dir.startswith(self.workspace_dir))
            basename = os.path.basename(new_dir)
            self.assertTrue(basename.startswith('bar'))
            self.assertTrue(basename.endswith('foo'))

            # trigger the exception handling for coverage.
            shutil.rmtree(new_dir)


class TimeFormattingTests(unittest.TestCase):
    """Test Time Formatting."""
    def test_format_time_hours(self):
        """Test format time hours."""
        from natcap.invest.utils import _format_time

        seconds = 3667
        self.assertEqual(_format_time(seconds), '1h 1m 7s')

    def test_format_time_minutes(self):
        """Test format time minutes."""
        from natcap.invest.utils import _format_time

        seconds = 67
        self.assertEqual(_format_time(seconds), '1m 7s')

    def test_format_time_seconds(self):
        """Test format time seconds."""
        from natcap.invest.utils import _format_time

        seconds = 7
        self.assertEqual(_format_time(seconds), '7s')


class LogToFileTests(unittest.TestCase):
    """Test Log To File."""
    def setUp(self):
        """Create a temporary workspace."""
        self.workspace = tempfile.mkdtemp()

    def tearDown(self):
        """Remove temporary workspace."""
        shutil.rmtree(self.workspace)

    def test_log_to_file_all_threads(self):
        """Utils: Verify that we can capture messages from all threads."""
        from natcap.invest.utils import log_to_file

        logfile = os.path.join(self.workspace, 'logfile.txt')

        def _log_from_other_thread():
            """Log from other thead."""
            thread_logger = logging.getLogger()
            thread_logger.info('this is from a thread')

        local_logger = logging.getLogger()

        # create the file before we log to it, so we know a warning should
        # be logged.
        with open(logfile, 'w') as new_file:
            new_file.write(' ')

        with log_to_file(logfile) as handler:
            thread = threading.Thread(target=_log_from_other_thread)
            thread.start()
            local_logger.info('this should be logged')
            local_logger.info('this should also be logged')

            thread.join()
            handler.flush()

        with open(logfile) as opened_logfile:
            messages = [msg for msg in opened_logfile.read().split('\n')
                        if msg if msg]
        self.assertEqual(len(messages), 3)

    def test_log_to_file_from_thread(self):
        """Utils: Verify that we can filter from a threading.Thread."""
        from natcap.invest.utils import log_to_file

        logfile = os.path.join(self.workspace, 'logfile.txt')

        def _log_from_other_thread():
            """Log from other thread."""
            thread_logger = logging.getLogger()
            thread_logger.info('this should not be logged')
            thread_logger.info('neither should this message')

        local_logger = logging.getLogger()

        thread = threading.Thread(target=_log_from_other_thread)

        with log_to_file(logfile, exclude_threads=[thread.name]) as handler:
            thread.start()
            local_logger.info('this should be logged')

            thread.join()
            handler.flush()

        with open(logfile) as opened_logfile:
            messages = [msg for msg in opened_logfile.read().split('\n')
                        if msg if msg]
        self.assertEqual(len(messages), 1)


class ThreadFilterTests(unittest.TestCase):
    """Test Thread Filter."""
    def test_thread_filter_same_thread(self):
        """Test threat filter same thread."""
        from natcap.invest.utils import ThreadFilter

        # name, level, pathname, lineno, msg, args, exc_info, func=None
        record = logging.LogRecord(
            name='foo',
            level=logging.INFO,
            pathname=__file__,
            lineno=500,
            msg='some logging message',
            args=(),
            exc_info=None,
            func='test_thread_filter_same_thread')
        filterer = ThreadFilter(threading.currentThread().name)

        # The record comes from the same thread.
        self.assertEqual(filterer.filter(record), False)

    def test_thread_filter_different_thread(self):
        """Test thread filter different thread."""
        from natcap.invest.utils import ThreadFilter

        # name, level, pathname, lineno, msg, args, exc_info, func=None
        record = logging.LogRecord(
            name='foo',
            level=logging.INFO,
            pathname=__file__,
            lineno=500,
            msg='some logging message',
            args=(),
            exc_info=None,
            func='test_thread_filter_same_thread')
        filterer = ThreadFilter('Thread-nonexistent')

        # The record comes from the same thread.
        self.assertEqual(filterer.filter(record), True)


class MakeDirectoryTests(unittest.TestCase):
    """Tests for natcap.invest.utils.make_directories."""

    def setUp(self):
        """Make temporary directory for workspace."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)

    def test_make_directories(self):
        """utils: test that make directories works as expected."""
        from natcap.invest import utils
        directory_list = [
            os.path.join(self.workspace_dir, x) for x in [
                'apple', 'apple/pie', 'foo/bar/baz']]
        utils.make_directories(directory_list)
        for path in directory_list:
            self.assertTrue(os.path.isdir(path))

    def test_make_directories_on_existing(self):
        """utils: test that no error if directory already exists."""
        from natcap.invest import utils
        path = os.path.join(self.workspace_dir, 'foo', 'bar', 'baz')
        os.makedirs(path)
        utils.make_directories([path])
        self.assertTrue(os.path.isdir(path))

    def test_make_directories_on_file(self):
        """utils: test that value error raised if file exists on directory."""
        from natcap.invest import utils
        dir_path = os.path.join(self.workspace_dir, 'foo', 'bar')
        os.makedirs(dir_path)
        file_path = os.path.join(dir_path, 'baz')
        file = open(file_path, 'w')
        file.close()
        with self.assertRaises(OSError):
            utils.make_directories([file_path])

    def test_make_directories_wrong_type(self):
        """utils: test that ValueError raised if value not a list."""
        from natcap.invest import utils
        with self.assertRaises(ValueError):
            utils.make_directories(self.workspace_dir)


class GDALWarningsLoggingTests(unittest.TestCase):
    """Test GDAL Warnings Logging."""
    def setUp(self):
        """Create a temporary workspace."""
        self.workspace = tempfile.mkdtemp()

    def tearDown(self):
        """Remove temporary workspace."""
        shutil.rmtree(self.workspace)

    def test_log_warnings(self):
        """utils: test that we can capture GDAL warnings to logging."""
        from natcap.invest import utils

        logfile = os.path.join(self.workspace, 'logfile.txt')

        # this warning should go to stdout.
        gdal.Open('this_file_should_not_exist.tif')

        with utils.log_to_file(logfile) as handler:
            with utils.capture_gdal_logging():
                # warning should be captured.
                gdal.Open('file_file_should_also_not_exist.tif')
            handler.flush()

        # warning should go to stdout
        gdal.Open('this_file_should_not_exist.tif')

        with open(logfile) as opened_logfile:
            messages = [msg for msg in opened_logfile.read().split('\n')
                        if msg if msg]

        self.assertEqual(len(messages), 1)


class PrepareWorkspaceTests(unittest.TestCase):
    """Test Prepare Workspace."""
    def setUp(self):
        """Create a temporary workspace."""
        self.workspace = tempfile.mkdtemp()

    def tearDown(self):
        """Remove temporary workspace."""
        shutil.rmtree(self.workspace)

    def test_prepare_workspace(self):
        """utils: test that prepare_workspace does what is expected."""
        from natcap.invest import utils

        workspace = os.path.join(self.workspace, 'foo')
        try:
            with utils.prepare_workspace(workspace,
                                         'some_model'):
                warnings.warn('deprecated', UserWarning)
                gdal.Open('file should not exist')
        except Warning as warning_raised:
            self.fail('Warning was not captured: %s' % warning_raised)

        self.assertTrue(os.path.exists(workspace))
        logfile_glob = glob.glob(os.path.join(workspace, '*.txt'))
        self.assertEqual(len(logfile_glob), 1)
        self.assertTrue(
            os.path.basename(logfile_glob[0]).startswith('InVEST-some_model'))
        with open(logfile_glob[0]) as logfile:
            logfile_text = logfile.read()
            # all the following strings should be in the logfile.
            expected_string = (
                'file should not exist: No such file or directory')
            self.assertTrue(
                expected_string in logfile_text)  # gdal error captured
            self.assertEqual(len(re.findall('WARNING', logfile_text)), 1)
            self.assertTrue('Elapsed time:' in logfile_text)


class BuildLookupFromCSVTests(unittest.TestCase):
    """Tests for natcap.invest.utils.build_lookup_from_csv."""
    def setUp(self):
        """Make temporary directory for workspace."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)

    def test_build_lookup_from_csv(self):
        """utils: test build_lookup_from_csv."""
        from natcap.invest import utils
        table_str = 'a,b,foo,bar,_\n0.0,x,-1,bar,apple\n'
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(table_str)
        result = utils.build_lookup_from_csv(
            table_path, 'a', to_lower=True)
        expected_dict = {
            0.0: {
                'a': 0.0,
                'b': 'x',
                'foo': -1.0,
                'bar': 'bar',
                '_': 'apple'
                },
            }
        self.assertDictEqual(result, expected_dict)

    def test_unique_key_not_first_column(self):
        """utils: test success when key field is not first column."""
        from natcap.invest import utils
        csv_text = ("desc,lucode,val1,val2\n"
                    "corn,1,0.5,2\n"
                    "bread,2,1,4\n"
                    "beans,3,0.5,4\n"
                    "butter,4,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True)
        expected_result = {
                1: {'desc': 'corn', 'val1': 0.5, 'val2': 2, 'lucode': 1},
                2: {'desc': 'bread', 'val1': 1, 'val2': 4, 'lucode': 2},
                3: {'desc': 'beans', 'val1': 0.5, 'val2': 4, 'lucode': 3},
                4: {'desc': 'butter', 'val1': 9, 'val2': 1, 'lucode': 4}}

        self.assertDictEqual(result, expected_result)

    def test_non_unique_keys(self):
        """utils: test error is raised if keys are not unique."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    "2,bread,1,4\n"
                    "2,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        with self.assertRaises(ValueError):
            utils.build_lookup_from_csv(table_path, 'lucode', to_lower=True)

    def test_missing_key_field(self):
        """utils: test error is raised when missing key field."""
        from natcap.invest import utils
        csv_text = ("luode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    "2,bread,1,4\n"
                    "3,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        with self.assertRaises(KeyError):
            utils.build_lookup_from_csv(table_path, 'lucode', to_lower=True)

    def test_nan_holes(self):
        """utils: test empty strings returned when missing data is present."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    "2,,1,4\n"
                    "3,beans,0.5,4\n"
                    "4,butter,,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True)
        expected_result = {
                1: {'desc': 'corn', 'val1': 0.5, 'val2': 2, 'lucode': 1},
                2: {'desc': '', 'val1': 1, 'val2': 4, 'lucode': 2},
                3: {'desc': 'beans', 'val1': 0.5, 'val2': 4, 'lucode': 3},
                4: {'desc': 'butter', 'val1': '', 'val2': 1, 'lucode': 4}}

        self.assertDictEqual(result, expected_result)

    def test_nan_row(self):
        """utils: test NaN row is dropped."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    ",,,\n"
                    "3,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True)
        expected_result = {
                1.0: {'desc': 'corn', 'val1': 0.5, 'val2': 2, 'lucode': 1.0},
                3.0: {'desc': 'beans', 'val1': 0.5, 'val2': 4, 'lucode': 3.0},
                4.0: {'desc': 'butter', 'val1': 9, 'val2': 1, 'lucode': 4.0}}

        self.assertDictEqual(result, expected_result)

    def test_column_subset(self):
        """utils: test column subset is properly returned."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    "2,bread,1,4\n"
                    "3,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True, column_list=['val1', 'val2'])

        expected_result = {
                1: {'val1': 0.5, 'val2': 2, 'lucode': 1},
                2: {'val1': 1, 'val2': 4, 'lucode': 2},
                3: {'val1': 0.5, 'val2': 4, 'lucode': 3},
                4: {'val1': 9, 'val2': 1, 'lucode': 4}}

        self.assertDictEqual(result, expected_result)

    def test_trailing_comma(self):
        """utils: test a trailing comma on first line is handled properly."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2,\n"
                    "2,bread,1,4\n"
                    "3,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True)

        expected_result = {
                1: {'desc': 'corn', 'val1': 0.5, 'val2': 2, 'lucode': 1},
                2: {'desc': 'bread', 'val1': 1, 'val2': 4, 'lucode': 2},
                3: {'desc': 'beans', 'val1': 0.5, 'val2': 4, 'lucode': 3},
                4: {'desc': 'butter', 'val1': 9, 'val2': 1, 'lucode': 4}}

        self.assertDictEqual(result, expected_result)

    def test_trailing_comma_second_line(self):
        """utils: test a trailing comma on second line is handled properly."""
        from natcap.invest import utils
        csv_text = ("lucode,desc,val1,val2\n"
                    "1,corn,0.5,2\n"
                    "2,bread,1,4,\n"
                    "3,beans,0.5,4\n"
                    "4,butter,9,1")
        table_path = os.path.join(self.workspace_dir, 'table.csv')
        with open(table_path, 'w') as table_file:
            table_file.write(csv_text)

        result = utils.build_lookup_from_csv(
            table_path, 'lucode', to_lower=True)

        expected_result = {
                1: {'desc': 'corn', 'val1': 0.5, 'val2': 2, 'lucode': 1},
                2: {'desc': 'bread', 'val1': 1, 'val2': 4, 'lucode': 2},
                3: {'desc': 'beans', 'val1': 0.5, 'val2': 4, 'lucode': 3},
                4: {'desc': 'butter', 'val1': 9, 'val2': 1, 'lucode': 4}}

        self.assertDictEqual(result, expected_result)

    def test_results_lowercase_non_numeric(self):
        """utils: text handling of converting to lowercase."""
        from natcap.invest import utils

        csv_file = os.path.join(self.workspace_dir, 'csv.csv')
        with open(csv_file, 'w') as file_obj:
            file_obj.write(textwrap.dedent(
                """
                header1,HEADER2,header3
                1,2,bar
                4,5,FOO
                """
            ).strip())

        lookup_dict = utils.build_lookup_from_csv(
            csv_file, 'header1', to_lower=True)

        self.assertEqual(lookup_dict[4]['header3'], 'foo')
        self.assertEqual(lookup_dict[1]['header2'], 2)

    def test_results_uppercase_numeric_cast(self):
        """utils: test handling of uppercase, num. casting, blank values."""
        from natcap.invest import utils

        csv_file = os.path.join(self.workspace_dir, 'csv.csv')
        with open(csv_file, 'w') as file_obj:
            file_obj.write(textwrap.dedent(
                """
                header1,HEADER2,header3,missing_column,
                1,2,3,
                4,FOO,bar,
                """
            ).strip())

        lookup_dict = utils.build_lookup_from_csv(
            csv_file, 'header1', to_lower=False)

        self.assertEqual(lookup_dict[4]['HEADER2'], 'FOO')
        self.assertEqual(lookup_dict[4]['header3'], 'bar')
        self.assertEqual(lookup_dict[1]['header1'], 1)

    def test_csv_dialect_detection_semicolon_delimited(self):
        """utils: test that we can parse semicolon-delimited CSVs."""
        from natcap.invest import utils

        csv_file = os.path.join(self.workspace_dir, 'csv.csv')
        with open(csv_file, 'w') as file_obj:
            file_obj.write(textwrap.dedent(
                """
                header1;HEADER2;header3;
                1;2;3;
                4;FOO;bar;
                """
            ).strip())

        lookup_dict = utils.build_lookup_from_csv(
            csv_file, 'header1', to_lower=False)

        self.assertEqual(lookup_dict[4]['HEADER2'], 'FOO')
        self.assertEqual(lookup_dict[4]['header3'], 'bar')
        self.assertEqual(lookup_dict[1]['header1'], 1)

    def test_csv_utf8_bom_encoding(self):
        """utils: test that CSV read correctly with UTF-8 BOM encoding."""
        from natcap.invest import utils

        csv_file = os.path.join(self.workspace_dir, 'csv.csv')
        # writing with utf-8-sig will prepend the BOM
        with open(csv_file, 'w', encoding='utf-8-sig') as file_obj:
            file_obj.write(textwrap.dedent(
                """
                header1,HEADER2,header3
                1,2,bar
                4,5,FOO
                """
            ).strip())
        # confirm that the file has the BOM prefix
        with open(csv_file, 'rb') as file_obj:
            self.assertTrue(file_obj.read().startswith(codecs.BOM_UTF8))

        lookup_dict = utils.build_lookup_from_csv(
            csv_file, 'header1')
        # assert the BOM prefix was correctly parsed and skipped
        self.assertEqual(lookup_dict[4]['header2'], 5)
        self.assertEqual(lookup_dict[4]['header3'], 'foo')
        self.assertEqual(lookup_dict[1]['header1'], 1)

    def test_csv_latin_1_encoding(self):
        """utils: test that CSV read correctly with Latin-1 encoding."""
        from natcap.invest import utils

        csv_file = os.path.join(self.workspace_dir, 'csv.csv')
        with codecs.open(csv_file, 'w', encoding='iso-8859-1') as file_obj:
            file_obj.write(textwrap.dedent(
                """
                header 1,HEADER 2,header 3
                1,2,bar1
                4,5,FOO
                """
            ).strip())

        lookup_dict = utils.build_lookup_from_csv(
            csv_file, 'header 1')

        self.assertEqual(lookup_dict[4]['header 2'], 5)
        self.assertEqual(lookup_dict[4]['header 3'], 'foo')
        self.assertEqual(lookup_dict[1]['header 1'], 1)


class CreateCoordinateTransformationTests(unittest.TestCase):
    """Tests for natcap.invest.utils.create_coordinate_transformer."""

    def test_latlon_to_latlon_transformer(self):
        """Utils: test transformer for lat/lon to lat/lon."""
        from natcap.invest import utils

        # Willamette valley in lat/lon for reference
        lon = -124.525
        lat = 44.525

        base_srs = osr.SpatialReference()
        base_srs.ImportFromEPSG(4326)  # WSG84 EPSG

        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)

        transformer = utils.create_coordinate_transformer(base_srs, target_srs)
        actual_x, actual_y, _ = transformer.TransformPoint(lon, lat)

        expected_x = -124.525
        expected_y = 44.525

        self.assertAlmostEqual(expected_x, actual_x, 5)
        self.assertAlmostEqual(expected_y, actual_y, 5)

    def test_latlon_to_projected_transformer(self):
        """Utils: test transformer for lat/lon to projected."""
        from natcap.invest import utils

        # Willamette valley in lat/lon for reference
        lon = -124.525
        lat = 44.525

        base_srs = osr.SpatialReference()
        base_srs.ImportFromEPSG(4326)  # WSG84 EPSG

        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(26910)  # UTM10N EPSG

        transformer = utils.create_coordinate_transformer(base_srs, target_srs)
        actual_x, actual_y, _ = transformer.TransformPoint(lon, lat)

        expected_x = 378816.2531852932
        expected_y = 4931317.807472325

        self.assertAlmostEqual(expected_x, actual_x, 5)
        self.assertAlmostEqual(expected_y, actual_y, 5)

    def test_projected_to_latlon_transformer(self):
        """Utils: test transformer for projected to lat/lon."""
        from natcap.invest import utils

        # Willamette valley in lat/lon for reference
        known_x = 378816.2531852932
        known_y = 4931317.807472325

        base_srs = osr.SpatialReference()
        base_srs.ImportFromEPSG(26910)  # UTM10N EPSG

        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)  # WSG84 EPSG

        transformer = utils.create_coordinate_transformer(base_srs, target_srs)
        actual_x, actual_y, _ = transformer.TransformPoint(known_x, known_y)

        expected_x = -124.52500000000002
        expected_y = 44.525

        self.assertAlmostEqual(expected_x, actual_x, places=3)
        self.assertAlmostEqual(expected_y, actual_y, places=3)

    def test_projected_to_projected_transformer(self):
        """Utils: test transformer for projected to projected."""
        from natcap.invest import utils

        # Willamette valley in lat/lon for reference
        known_x = 378816.2531852932
        known_y = 4931317.807472325

        base_srs = osr.SpatialReference()
        base_srs.ImportFromEPSG(26910)  # UTM10N EPSG

        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(26910)  # UTM10N EPSG

        transformer = utils.create_coordinate_transformer(base_srs, target_srs)
        actual_x, actual_y, _ = transformer.TransformPoint(known_x, known_y)

        expected_x = 378816.2531852932
        expected_y = 4931317.807472325

        self.assertAlmostEqual(expected_x, actual_x, 5)
        self.assertAlmostEqual(expected_y, actual_y, 5)


class AssertVectorsEqualTests(unittest.TestCase):
    """Tests for natcap.invest.utils._assert_vectors_equal."""
    def setUp(self):
        """Setup workspace."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)

    def test_identical_point_vectors(self):
        """Utils: test identical point vectors pass."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal}
        attrs = [{'id': 1}, {'id': 2}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        geometries = [Point(pos_x + 50, pos_y - 50),
                      Point(pos_x + 50, pos_y - 150)]
        shape_path = os.path.join(self.workspace_dir, 'point_shape.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'point_shape_copy.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        utils._assert_vectors_equal(shape_path, shape_copy_path)

    def test_identical_polygon_vectors(self):
        """Utils: test identical polygon vectors pass."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal}
        attrs = [{'id': 1}, {'id': 2}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        poly_geoms = {
            'poly_1': [(pos_x + 200, pos_y), (pos_x + 250, pos_y),
                       (pos_x + 250, pos_y - 100), (pos_x + 200, pos_y - 100),
                       (pos_x + 200, pos_y)],
            'poly_2': [(pos_x, pos_y - 150), (pos_x + 100, pos_y - 150),
                       (pos_x + 100, pos_y - 200), (pos_x, pos_y - 200),
                       (pos_x, pos_y - 150)]}

        geometries = [
            Polygon(poly_geoms['poly_1']), Polygon(poly_geoms['poly_2'])]

        shape_path = os.path.join(self.workspace_dir, 'poly_shape.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'poly_shape_copy.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        utils._assert_vectors_equal(shape_path, shape_copy_path)

    def test_identical_polygon_vectors_unorded_geometry(self):
        """Utils: test identical polygon vectors w/ diff geometry order."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal}
        attrs = [{'id': 1}, {'id': 2}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        poly_geoms = {
            'poly_1': [(pos_x + 200, pos_y), (pos_x + 250, pos_y),
                       (pos_x + 250, pos_y - 100), (pos_x + 200, pos_y - 100),
                       (pos_x + 200, pos_y)],
            'poly_2': [(pos_x, pos_y - 150), (pos_x + 100, pos_y - 150),
                       (pos_x + 100, pos_y - 200), (pos_x, pos_y - 200),
                       (pos_x, pos_y - 150)]}

        poly_geoms_unordered = {
            'poly_1': [(pos_x + 200, pos_y), (pos_x + 250, pos_y),
                       (pos_x + 250, pos_y - 100), (pos_x + 200, pos_y - 100),
                       (pos_x + 200, pos_y)],
            'poly_2': [(pos_x, pos_y - 150), (pos_x, pos_y - 200),
                       (pos_x + 100, pos_y - 200), (pos_x + 100, pos_y - 150),
                       (pos_x, pos_y - 150)]}

        geometries = [
            Polygon(poly_geoms['poly_1']), Polygon(poly_geoms['poly_2'])]

        geometries_copy = [
            Polygon(poly_geoms_unordered['poly_1']),
            Polygon(poly_geoms_unordered['poly_2'])]

        shape_path = os.path.join(self.workspace_dir, 'poly_shape.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'poly_shape_copy.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries_copy, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        utils._assert_vectors_equal(shape_path, shape_copy_path)

    def test_different_field_value(self):
        """Utils: test vectors w/ different field value fails."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal, 'foo': ogr.OFTReal}
        attrs = [{'id': 1, 'foo': 2.3456}, {'id': 2, 'foo': 5.6789}]
        attrs_copy = [{'id': 1, 'foo': 2.3467}, {'id': 2, 'foo': 5.6789}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        geometries = [Point(pos_x + 50, pos_y - 50),
                      Point(pos_x + 50, pos_y - 150)]
        shape_path = os.path.join(self.workspace_dir, 'point_shape.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'point_shape_copy.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs_copy,
            ogr_geom_type=ogr.wkbPoint)

        with self.assertRaises(AssertionError) as cm:
            utils._assert_vectors_equal(shape_path, shape_copy_path)

        self.assertTrue(
            "Vector field values are not equal" in str(cm.exception))

    def test_different_field_names(self):
        """Utils: test vectors w/ different field names fails."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal, 'foo': ogr.OFTReal}
        fields_copy = {'id': ogr.OFTReal, 'foobar': ogr.OFTReal}
        attrs = [{'id': 1, 'foo': 2.3456}, {'id': 2, 'foo': 5.6789}]
        attrs_copy = [{'id': 1, 'foobar': 2.3456}, {'id': 2, 'foobar': 5.6789}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        geometries = [Point(pos_x + 50, pos_y - 50),
                      Point(pos_x + 50, pos_y - 150)]
        shape_path = os.path.join(self.workspace_dir, 'point_shape.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'point_shape_copy.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields_copy, attribute_list=attrs_copy,
            ogr_geom_type=ogr.wkbPoint)

        with self.assertRaises(AssertionError) as cm:
            utils._assert_vectors_equal(shape_path, shape_copy_path)

        self.assertTrue(
            "Vector field names are not the same" in str(cm.exception))

    def test_different_feature_count(self):
        """Utils: test vectors w/ different feature count fails."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal, 'foo': ogr.OFTReal}
        attrs = [{'id': 1, 'foo': 2.3456}, {'id': 2, 'foo': 5.6789}]
        attrs_copy = [
            {'id': 1, 'foo': 2.3456}, {'id': 2, 'foo': 5.6789},
            {'id': 3, 'foo': 5.0}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        geometries = [Point(pos_x + 50, pos_y - 50),
                      Point(pos_x + 50, pos_y - 150)]

        geometries_copy = [Point(pos_x + 50, pos_y - 50),
                           Point(pos_x + 50, pos_y - 150),
                           Point(pos_x + 55, pos_y - 55)]
        shape_path = os.path.join(self.workspace_dir, 'point_shape.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'point_shape_copy.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries_copy, shape_copy_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs_copy,
            ogr_geom_type=ogr.wkbPoint)

        with self.assertRaises(AssertionError) as cm:
            utils._assert_vectors_equal(shape_path, shape_copy_path)

        self.assertTrue(
            "Vector feature counts are not the same" in str(cm.exception))

    def test_different_projections(self):
        """Utils: test vectors w/ different projections fails."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal, 'foo': ogr.OFTReal}
        attrs = [{'id': 1, 'foo': 2.3456}, {'id': 2, 'foo': 5.6789}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        geometries = [Point(pos_x + 50, pos_y - 50),
                      Point(pos_x + 50, pos_y - 150)]

        srs_copy = osr.SpatialReference()
        srs_copy.ImportFromEPSG(26910)  # UTM Zone 10N
        projection_wkt_copy = srs_copy.ExportToWkt()

        origin_copy = (1180000, 690000)
        pos_x_copy = origin_copy[0]
        pos_y_copy = origin_copy[1]

        geometries_copy = [Point(pos_x_copy + 50, pos_y_copy - 50),
                           Point(pos_x_copy + 50, pos_y_copy - 150)]

        shape_path = os.path.join(self.workspace_dir, 'point_shape.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        shape_copy_path = os.path.join(
            self.workspace_dir, 'point_shape_copy.shp')
        # Create point shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries_copy, shape_copy_path, projection_wkt_copy,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPoint)

        with self.assertRaises(AssertionError) as cm:
            utils._assert_vectors_equal(shape_path, shape_copy_path)

        self.assertTrue(
            "Vector projections are not the same" in str(cm.exception))

    def test_different_geometry_fails(self):
        """Utils: test vectors w/ diff geometries fail."""
        from natcap.invest import utils

        # Setup parameters to create point shapefile
        fields = {'id': ogr.OFTReal}
        attrs = [{'id': 1}, {'id': 2}]

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        projection_wkt = srs.ExportToWkt()
        origin = (443723.127327877911739, 4956546.905980412848294)
        pos_x = origin[0]
        pos_y = origin[1]

        poly_geoms = {
            'poly_1': [(pos_x + 200, pos_y), (pos_x + 250, pos_y),
                       (pos_x + 250, pos_y - 100), (pos_x + 200, pos_y - 100),
                       (pos_x + 200, pos_y)],
            'poly_2': [(pos_x, pos_y - 150), (pos_x + 100, pos_y - 150),
                       (pos_x + 100, pos_y - 200), (pos_x, pos_y - 200),
                       (pos_x, pos_y - 150)]}

        poly_geoms_diff = {
            'poly_1': [(pos_x + 200, pos_y), (pos_x + 250, pos_y),
                       (pos_x + 250, pos_y - 100), (pos_x + 200, pos_y - 100),
                       (pos_x + 200, pos_y)],
            'poly_2': [(pos_x, pos_y - 150), (pos_x, pos_y - 201),
                       (pos_x + 100, pos_y - 200), (pos_x + 100, pos_y - 150),
                       (pos_x, pos_y - 150)]}

        geometries = [
            Polygon(poly_geoms['poly_1']), Polygon(poly_geoms['poly_2'])]

        geometries_diff = [
            Polygon(poly_geoms_diff['poly_1']),
            Polygon(poly_geoms_diff['poly_2'])]

        shape_path = os.path.join(self.workspace_dir, 'poly_shape.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries, shape_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        shape_diff_path = os.path.join(
            self.workspace_dir, 'poly_shape_diff.shp')
        # Create polygon shapefile to use as testing input
        pygeoprocessing.shapely_geometry_to_vector(
            geometries_diff, shape_diff_path, projection_wkt,
            'ESRI Shapefile', fields=fields, attribute_list=attrs,
            ogr_geom_type=ogr.wkbPolygon)

        with self.assertRaises(AssertionError) as cm:
            utils._assert_vectors_equal(shape_path, shape_diff_path)

        self.assertTrue("Vector geometry assertion fail." in str(cm.exception))


class RasterDictValuesTests(unittest.TestCase):
    """Tests for natcap.invest.utils.raster_values_missing_from_dict_map."""
    def setUp(self):
        """Setup workspace."""
        self.workspace_dir = tempfile.mkdtemp()
        # set spatial reference used for this class of tests 
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3157)
        self.projection_wkt = srs.ExportToWkt()
        self.origin = (443723.1273, 4956546.9059)

        self.nodata = -1
        self.pixel_size = (1, -1)

    def tearDown(self):
        """Delete workspace."""
        shutil.rmtree(self.workspace_dir)
    
    def test_raster_values_subset_of_dict(self):
        """Utils: test raster values are a valid subset of dictionary."""
        from natcap.invest import utils
        
        raster_array = numpy.array([[1, 2, 3, 4], [4, 3, 2, 1], [1, 2, 2, 1]])
        raster_tmp_path = os.path.join(self.workspace_dir, 'tmp_raster.tif')
        pygeoprocessing.numpy_array_to_raster(
            raster_array, self.nodata, self.pixel_size, self.origin, 
            self.projection_wkt, raster_tmp_path)
        dict_map = {1: '', 2: '', 3: '', 4: ''}

        missing_values = utils.raster_values_missing_from_dict_map(
            (raster_tmp_path, 1), dict_map)

        self.assertFalse(
            missing_values, 
            "The returned missing value list should be empty but is not.")
    
    def test_raster_values_not_subset_of_dict(self):
        """Utils: test missing raster values are returned."""
        from natcap.invest import utils
        
        raster_array = numpy.array([[1, 2, 3, 4], [4, 3, 2, 1], [1, 9, 2, 1]])
        raster_tmp_path = os.path.join(self.workspace_dir, 'tmp_raster.tif')
        pygeoprocessing.numpy_array_to_raster(
            raster_array, self.nodata, self.pixel_size, self.origin, 
            self.projection_wkt, raster_tmp_path)
        dict_map = {1: '', 2: '', 3: '', 4: ''}

        missing_values = utils.raster_values_missing_from_dict_map(
            (raster_tmp_path, 1), dict_map)

        self.assertEqual(
            missing_values, {9}, 
            "The returned missing value list should be {9} but is not.")
    
    def test_raster_multipl_values_not_subset_of_dict(self):
        """Utils: test multiple missing raster values are returned."""
        from natcap.invest import utils
        
        raster_array = numpy.array([[1, 11, 3, 4], [4, 3, 2, 1], [1, 9, 2, 1]])
        raster_tmp_path = os.path.join(self.workspace_dir, 'tmp_raster.tif')
        pygeoprocessing.numpy_array_to_raster(
            raster_array, self.nodata, self.pixel_size, self.origin, 
            self.projection_wkt, raster_tmp_path)
        dict_map = {1: '', 2: '', 3: '', 4: ''}

        missing_values = utils.raster_values_missing_from_dict_map(
            (raster_tmp_path, 1), dict_map)

        self.assertEqual(
            missing_values, {9, 11}, 
            "The returned missing value list should be {9, 11} but is not.")
